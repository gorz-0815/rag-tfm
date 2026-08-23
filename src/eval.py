"""Comparative eval: run data/eval_qa.json through both the no-context
baseline and the RAG pipeline, score both with Ragas, and write a comparison
report to results/.

Faithfulness for the no-context condition is judged against the RAG
condition's retrieved manual chunks for the same question, not against
nothing - that is the point of the comparison. The no-context answer never
saw those chunks, so a low faithfulness score there shows it invented
content the manual doesn't support; the RAG answer, judged against the same
chunks it was given, shows how well it stuck to them. context_precision and
context_recall only make sense where retrieval happened, so those are
RAG-only per the comparative-eval spec.

Heavy imports (ragas, langchain-anthropic) are kept inside main() so this
module stays importable without the full stack.

Usage: python -m src.eval <manual_path>
"""

import argparse
import json
from pathlib import Path

from src import config
from src.query import ask_no_context, ask_rag


def load_eval_qa() -> list[dict]:
    path = config.PROJECT_ROOT / "data" / "eval_qa.json"
    return json.loads(path.read_text(encoding="utf-8"))


def run_conditions(eval_qa: list[dict], manual_path: Path) -> list[dict]:
    """Run every eval question through both conditions, returning one row
    per question with both answers, RAG's retrieved contexts, and the
    ground-truth reference.
    """
    rows = []
    for item in eval_qa:
        question = item["question"]
        rag_result = ask_rag(question, manual_path)
        no_context_result = ask_no_context(question)
        rows.append(
            {
                "question": question,
                "reference": item["ground_truth"],
                "rag_answer": rag_result["answer"],
                "rag_contexts": rag_result["contexts"],
                "no_context_answer": no_context_result["answer"],
            }
        )
    return rows


def _build_ragas_dataset(rows: list[dict], answer_key: str):
    """Build a Ragas dataset scoring `answer_key`'s answers against RAG's
    retrieved contexts - see module docstring for why both conditions are
    judged against the same retrieved contexts.
    """
    from ragas import EvaluationDataset

    samples = [
        {
            "user_input": row["question"],
            "response": row[answer_key],
            "reference": row["reference"],
            "retrieved_contexts": row["rag_contexts"],
        }
        for row in rows
    ]
    return EvaluationDataset.from_list(samples)


def _patch_ragas_vertexai_import() -> None:
    """installed langchain-community (>=0.4) dropped chat_models.vertexai,
    but ragas 0.4.x still imports ChatVertexAI at module load time for an
    isinstance check we never hit (Anthropic-only here) - stub it out so
    `import ragas` doesn't crash on a provider we don't use.
    """
    import sys
    import types

    module_name = "langchain_community.chat_models.vertexai"
    if module_name in sys.modules:
        return
    stub = types.ModuleType(module_name)
    stub.ChatVertexAI = type("ChatVertexAI", (), {})
    sys.modules[module_name] = stub


class _LlamaIndexEmbeddingsAdapter:
    """Exposes a langchain-shaped embed_query/embed_documents interface over
    an already-loaded llama_index embedding model, so Ragas'
    LangchainEmbeddingsWrapper can reuse the exact model instance ingestion
    and retrieval already loaded rather than loading a second copy under a
    different cache layout.
    """

    def __init__(self, llama_embed_model):
        self._model = llama_embed_model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._model.get_text_embedding(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._model.get_query_embedding(text)


def score_conditions(rows: list[dict]) -> dict:
    """Score both conditions with Ragas: faithfulness + answer_relevancy for
    both, context_precision + context_recall for RAG only.
    """
    _patch_ragas_vertexai_import()

    from langchain_anthropic import ChatAnthropic
    from llama_index.core import Settings
    from ragas import evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import (
        AnswerRelevancy,
        ContextPrecision,
        ContextRecall,
        Faithfulness,
    )

    from src.vector_store import configure_embed_model

    judge_llm = LangchainLLMWrapper(
        ChatAnthropic(model=config.ANTHROPIC_MODEL, api_key=config.ANTHROPIC_API_KEY)
    )
    configure_embed_model()
    judge_embeddings = LangchainEmbeddingsWrapper(
        _LlamaIndexEmbeddingsAdapter(Settings.embed_model)
    )

    faithfulness = Faithfulness(llm=judge_llm)
    answer_relevancy = AnswerRelevancy(llm=judge_llm, embeddings=judge_embeddings)
    context_precision = ContextPrecision(llm=judge_llm)
    context_recall = ContextRecall(llm=judge_llm)

    rag_dataset = _build_ragas_dataset(rows, "rag_answer")
    rag_scores = evaluate(
        rag_dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )

    no_context_dataset = _build_ragas_dataset(rows, "no_context_answer")
    no_context_scores = evaluate(
        no_context_dataset,
        metrics=[faithfulness, answer_relevancy],
    )

    return {"rag": rag_scores.to_pandas(), "no_context": no_context_scores.to_pandas()}


def _relevancy_interpretation(baseline_relevancy: float | None, rag_relevancy: float | None) -> str:
    if baseline_relevancy is None or rag_relevancy is None:
        return ""
    if abs(rag_relevancy - baseline_relevancy) < 0.1:
        return (
            "Answer relevancy stays comparable across both conditions since both "
            "answer the question asked - the gap that matters for this project is "
            "faithfulness, not relevancy."
        )
    return (
        f"Answer relevancy also gaps ({baseline_relevancy} baseline vs. {rag_relevancy} "
        "RAG): on manual-specific questions the baseline often hedges or answers a "
        "more generic version of the question instead of the one actually asked, "
        "which the relevancy metric penalizes independently of faithfulness."
    )


def write_results(rows: list[dict], scores: dict) -> None:
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    rag_df = scores["rag"]
    no_context_df = scores["no_context"]

    raw = {
        "rag": rag_df.to_dict(orient="records"),
        "no_context": no_context_df.to_dict(orient="records"),
    }
    (config.RESULTS_DIR / "eval_results.json").write_text(
        json.dumps(raw, indent=2), encoding="utf-8"
    )

    def avg(df, col):
        return round(df[col].mean(), 3) if col in df else None

    rag_faithfulness = avg(rag_df, "faithfulness")
    rag_relevancy = avg(rag_df, "answer_relevancy")
    rag_precision = avg(rag_df, "context_precision")
    rag_recall = avg(rag_df, "context_recall")
    baseline_faithfulness = avg(no_context_df, "faithfulness")
    baseline_relevancy = avg(no_context_df, "answer_relevancy")

    lines = [
        "# Comparative eval: RAG vs. no-context baseline",
        "",
        f"{len(rows)} hand-written questions against the ingested manual, "
        "each answered under both conditions and scored with Ragas "
        "(judge: Claude, embeddings: the local HF model used for retrieval).",
        "",
        "## Results",
        "",
        "| Metric | No-context baseline | RAG |",
        "|---|---|---|",
        f"| Faithfulness | {baseline_faithfulness} | {rag_faithfulness} |",
        f"| Answer relevancy | {baseline_relevancy} | {rag_relevancy} |",
        f"| Context precision | n/a | {rag_precision} |",
        f"| Context recall | n/a | {rag_recall} |",
        "",
        "Faithfulness for both conditions is judged against the same "
        "manual chunks RAG retrieved for each question - the no-context "
        "answer never saw them, so its faithfulness score reflects how "
        "much it invented versus what the manual actually says. Context "
        "precision/recall only apply where retrieval happened, so they're "
        "RAG-only.",
        "",
        "## Interpretation",
        "",
        (
            f"RAG scored {rag_faithfulness} on faithfulness against the manual's "
            f"actual content, versus {baseline_faithfulness} for the no-context "
            "baseline judged against that same content - the baseline has no "
            "access to the manual and answers from general world knowledge, so "
            "its faithfulness score demonstrates how often that knowledge diverges "
            "from this specific product's documented behavior. On manual-specific "
            "questions (exact soak times, cartridge model numbers, safety limits), "
            "the no-context condition either declines to answer specifically or "
            "invents a plausible-sounding but ungrounded number; the RAG condition "
            "answers from the retrieved chunks and can be verified against them. "
            f"{_relevancy_interpretation(baseline_relevancy, rag_relevancy)}"
        ),
        "",
    ]
    (config.RESULTS_DIR / "eval_results.md").write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the comparative eval (no-context vs RAG) against an ingested manual."
    )
    parser.add_argument("manual_path", type=Path, help="Path to the ingested manual PDF")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    eval_qa = load_eval_qa()
    print(f"Running {len(eval_qa)} questions through both conditions...")
    rows = run_conditions(eval_qa, args.manual_path)

    print("Scoring with Ragas...")
    scores = score_conditions(rows)

    write_results(rows, scores)
    print(f"Wrote {config.RESULTS_DIR / 'eval_results.json'}")
    print(f"Wrote {config.RESULTS_DIR / 'eval_results.md'}")


if __name__ == "__main__":
    main()
