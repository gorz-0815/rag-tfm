"""Comparative eval: run data/eval_qa.json through all three query modes
(no-context baseline, full-doc, RAG), score them with Ragas, and write a
comparison report to results/. Only RAG vs. no-context is required by the
comparative-eval spec; full-doc is scored alongside as an extra data point,
not a spec requirement.

Faithfulness (Ragas' metric): an LLM judge extracts claims from the answer
and scores what fraction are supported by the given context. No-context and
RAG are both judged against RAG's retrieved chunks; full-doc against the
full manual text. context_precision/recall stay RAG-only - only RAG has an
actual retrieval step to score.

Answer relevancy (Ragas' metric): the judge LLM reverse-generates several
questions the answer would suit, then scores their embedding similarity to
the question actually asked - independent of context, purely whether the
answer stays on-topic rather than hedging or going generic.

Heavy imports (ragas, langchain-anthropic) are kept inside main() so this
module stays importable without the full stack.

Usage: python -m src.eval <manual_path>
"""

import argparse
import json
import time
from pathlib import Path

from src import config
from src.eval_report import write_results
from src.query import ask_full_doc, ask_no_context, ask_rag


def load_eval_qa() -> list[dict]:
    path = config.PROJECT_ROOT / "data" / "eval_qa.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _timed(fn, *args):
    start = time.perf_counter()
    result = fn(*args)
    return result, time.perf_counter() - start


def run_conditions(eval_qa: list[dict], manual_path: Path) -> list[dict]:
    """Run every eval question through all three conditions, returning one
    row per question with each answer, each condition's own retrieved/given
    contexts, wall-clock latency, token usage, and the ground-truth
    reference. USD cost is derived from usage later, in eval_report.
    """
    rows = []
    for item in eval_qa:
        question = item["question"]
        rag_result, rag_latency_s = _timed(ask_rag, question, manual_path)
        full_doc_result, full_doc_latency_s = _timed(ask_full_doc, question, manual_path)
        no_context_result, no_context_latency_s = _timed(ask_no_context, question)
        rows.append(
            {
                "question": question,
                "reference": item["ground_truth"],
                "rag_answer": rag_result["answer"],
                "rag_contexts": rag_result["contexts"],
                "rag_latency_s": rag_latency_s,
                "rag_usage": rag_result["usage"],
                "full_doc_answer": full_doc_result["answer"],
                "full_doc_contexts": full_doc_result["contexts"],
                "full_doc_latency_s": full_doc_latency_s,
                "full_doc_usage": full_doc_result["usage"],
                "no_context_answer": no_context_result["answer"],
                "no_context_latency_s": no_context_latency_s,
                "no_context_usage": no_context_result["usage"],
            }
        )
    return rows


def _build_ragas_dataset(rows: list[dict], answer_key: str, contexts_key: str):
    """Build a Ragas dataset scoring `answer_key`'s answers against
    `contexts_key`'s contexts. The no-context condition is deliberately
    scored against RAG's contexts, not its own (it has none) - see module
    docstring for why.
    """
    from ragas import EvaluationDataset

    samples = [
        {
            "user_input": row["question"],
            "response": row[answer_key],
            "reference": row["reference"],
            "retrieved_contexts": row[contexts_key],
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
    """Score all three conditions with Ragas: faithfulness + answer_relevancy
    for all three, context_precision + context_recall for RAG only (the only
    condition with an actual retrieval step to score).
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

    rag_dataset = _build_ragas_dataset(rows, "rag_answer", "rag_contexts")
    rag_scores = evaluate(
        rag_dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )

    # Scored against RAG's retrieved chunks, not its own contexts - see module docstring.
    no_context_dataset = _build_ragas_dataset(rows, "no_context_answer", "rag_contexts")
    no_context_scores = evaluate(
        no_context_dataset,
        metrics=[faithfulness, answer_relevancy],
    )

    # Full-doc is scored against what it was actually given (the whole manual),
    # not RAG's retrieved subset - it has that "context" natively.
    full_doc_dataset = _build_ragas_dataset(rows, "full_doc_answer", "full_doc_contexts")
    full_doc_scores = evaluate(
        full_doc_dataset,
        metrics=[faithfulness, answer_relevancy],
    )

    return {
        "rag": rag_scores.to_pandas(),
        "full_doc": full_doc_scores.to_pandas(),
        "no_context": no_context_scores.to_pandas(),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the comparative eval (no-context vs full-doc vs RAG) "
        "against an ingested manual."
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
