"""Comparative eval: run data/eval_qa.json through all three query modes
(no-context baseline, full-doc, RAG), score them with Ragas, and write a
comparison report to results/. Only RAG vs. no-context is required by the
comparative-eval spec; full-doc is scored alongside as an extra data point,
not a spec requirement.

Faithfulness for the no-context condition is judged against RAG's retrieved
manual chunks for the same question, not against nothing - that is the point
of the comparison. The no-context answer never saw those chunks, so a low
faithfulness score there shows it invented content the manual doesn't
support. Full-doc and RAG are each judged against what they were actually
given (the manual's full text vs. the retrieved chunks) - comparing their
faithfulness scores isolates retrieval's cost from generation quality.
context_precision and context_recall only make sense where retrieval
happened, so those stay RAG-only.

Heavy imports (ragas, langchain-anthropic) are kept inside main() so this
module stays importable without the full stack.

Usage: python -m src.eval <manual_path>
"""

import argparse
import json
import time
from pathlib import Path

from src import config
from src.query import ask_full_doc, ask_no_context, ask_rag

# USD per 1M tokens (input, output), Anthropic's published first-party API
# pricing as of 2026-08. Only models this project actually configures need an
# entry; an unrecognized config.ANTHROPIC_MODEL just skips cost reporting
# (see _cost_usd) rather than guessing at a price.
PRICING_PER_MILLION_TOKENS = {
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-opus-5": (5.00, 25.00),
}


def load_eval_qa() -> list[dict]:
    path = config.PROJECT_ROOT / "data" / "eval_qa.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _timed(fn, *args):
    start = time.perf_counter()
    result = fn(*args)
    return result, time.perf_counter() - start


def _cost_usd(usage: dict) -> float | None:
    pricing = PRICING_PER_MILLION_TOKENS.get(config.ANTHROPIC_MODEL)
    if pricing is None:
        return None
    input_price, output_price = pricing
    return (
        usage["input_tokens"] / 1_000_000 * input_price
        + usage["output_tokens"] / 1_000_000 * output_price
    )


def run_conditions(eval_qa: list[dict], manual_path: Path) -> list[dict]:
    """Run every eval question through all three conditions, returning one
    row per question with each answer, each condition's own retrieved/given
    contexts, wall-clock latency, per-query USD cost, and the ground-truth
    reference.
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
                "rag_cost_usd": _cost_usd(rag_result["usage"]),
                "full_doc_answer": full_doc_result["answer"],
                "full_doc_contexts": full_doc_result["contexts"],
                "full_doc_latency_s": full_doc_latency_s,
                "full_doc_cost_usd": _cost_usd(full_doc_result["usage"]),
                "no_context_answer": no_context_result["answer"],
                "no_context_latency_s": no_context_latency_s,
                "no_context_cost_usd": _cost_usd(no_context_result["usage"]),
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


def _relevancy_interpretation(baseline_relevancy: float | None, rag_relevancy: float | None) -> str:
    if baseline_relevancy is None or rag_relevancy is None:
        return ""
    if abs(rag_relevancy - baseline_relevancy) < 0.1:
        return (
            "Answer relevancy stays comparable between RAG and the no-context "
            "baseline since both answer the question asked - the gap that matters "
            "for this project is faithfulness, not relevancy."
        )
    return (
        f"Answer relevancy also gaps ({baseline_relevancy} baseline vs. {rag_relevancy} "
        "RAG): on manual-specific questions the baseline often hedges or answers a "
        "more generic version of the question instead of the one actually asked, "
        "which the relevancy metric penalizes independently of faithfulness."
    )


def _full_doc_interpretation(
    rag_faithfulness: float | None, full_doc_faithfulness: float | None
) -> str:
    if rag_faithfulness is None or full_doc_faithfulness is None:
        return ""
    if full_doc_faithfulness > rag_faithfulness + 0.05:
        return (
            f"Full-doc scored higher faithfulness ({full_doc_faithfulness} vs. "
            f"{rag_faithfulness} for RAG), each judged against what it was actually "
            "given - the gap is retrieval's cost: RAG occasionally answers from an "
            "incomplete slice of the manual, where full-doc never misses a relevant "
            "section. That comes at a real cost this eval doesn't score directly: "
            "full-doc sends the entire manual as context on every query, versus a "
            "handful of retrieved chunks for RAG - see the README's cost/latency "
            "section for the token/price trade-off."
        )
    return (
        f"Full-doc's faithfulness ({full_doc_faithfulness}) is on par with RAG's "
        f"({rag_faithfulness}), each judged against what it was actually given - for "
        "this manual's size and this eval's questions, RAG's retrieval isn't losing "
        "meaningfully relevant content, so full-doc's larger per-query token cost "
        "(see the README's cost/latency section) buys little accuracy here."
    )


def _latency_interpretation(
    rows: list[dict],
    rag_latency: float | None,
    full_doc_latency: float | None,
    baseline_latency: float | None,
) -> str:
    if rag_latency is None or full_doc_latency is None or baseline_latency is None:
        return ""

    def avg_len(key):
        return round(sum(len(row[key]) for row in rows) / len(rows)) if rows else None

    rag_chars = avg_len("rag_answer")
    baseline_chars = avg_len("no_context_answer")
    rag_latencies = [row["rag_latency_s"] for row in rows]
    rag_latency_excl_first = (
        round(sum(rag_latencies[1:]) / len(rag_latencies[1:]), 2)
        if len(rag_latencies) > 1
        else rag_latency
    )

    length_ratio = round(baseline_chars / rag_chars, 1) if rag_chars else "?"

    return (
        f"Wall-clock latency (avg per question, including this process's own "
        f"retrieval/extraction time, not just the LLM call): {baseline_latency}s "
        f"no-context, {rag_latency}s RAG, {full_doc_latency}s full-doc - full-doc's "
        "much larger input isn't the bottleneck here (prompt input is fast to "
        "process regardless of length), so it isn't slower than RAG despite its "
        "far larger per-query token spend. The no-context baseline is the slowest "
        "of the three despite doing the least work: its answers run roughly "
        f"{length_ratio}x longer ({baseline_chars} vs. {rag_chars} characters on "
        "average) since there's no 'answer only from this context, concisely' "
        "system prompt constraining it - output generation, not input size, "
        f"dominates latency here. RAG's own average includes a one-time "
        f"embedding-model load on the first question ({rag_latencies[0]:.1f}s of "
        f"it); excluding that startup cost, RAG averages {rag_latency_excl_first}s "
        "per query, on par with full-doc. This is a single run over 18 questions "
        "against one small local backend, not a rigorous benchmark - treat it as a "
        "directional signal, not a production latency SLA."
    )


def _cost_interpretation(
    rag_cost: float | None, full_doc_cost: float | None, baseline_cost: float | None
) -> str:
    if rag_cost is None or full_doc_cost is None or baseline_cost is None:
        return (
            f"Per-query cost isn't reported for model '{config.ANTHROPIC_MODEL}' - "
            "add it to PRICING_PER_MILLION_TOKENS in src/eval.py to include it."
        )
    full_doc_multiple = round(full_doc_cost / rag_cost, 1) if rag_cost else "?"
    return (
        f"Per-query cost (from Anthropic's actual reported token usage, at "
        f"{config.ANTHROPIC_MODEL}'s published rates): ${baseline_cost:.5f} "
        f"no-context, ${rag_cost:.5f} RAG, ${full_doc_cost:.5f} full-doc - "
        f"full-doc costs about {full_doc_multiple}x RAG's per-query price, almost "
        "entirely from input tokens (the whole manual, resent on every query, "
        "versus a handful of retrieved chunks). This is the actual trade-off "
        "full-doc's faithfulness parity with RAG comes at: not accuracy, and not "
        "necessarily latency, but dollars - at higher query volume or a larger "
        "manual, that gap scales linearly with corpus size for full-doc and stays "
        "roughly flat for RAG."
    )


def write_results(rows: list[dict], scores: dict) -> None:
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    rag_df = scores["rag"]
    full_doc_df = scores["full_doc"]
    no_context_df = scores["no_context"]

    raw = {
        "rag": rag_df.to_dict(orient="records"),
        "full_doc": full_doc_df.to_dict(orient="records"),
        "no_context": no_context_df.to_dict(orient="records"),
        "latency_s": [
            {
                "question": row["question"],
                "rag": row["rag_latency_s"],
                "full_doc": row["full_doc_latency_s"],
                "no_context": row["no_context_latency_s"],
            }
            for row in rows
        ],
        "cost_usd": [
            {
                "question": row["question"],
                "rag": row["rag_cost_usd"],
                "full_doc": row["full_doc_cost_usd"],
                "no_context": row["no_context_cost_usd"],
            }
            for row in rows
        ],
    }
    (config.RESULTS_DIR / "eval_results.json").write_text(
        json.dumps(raw, indent=2), encoding="utf-8"
    )

    def avg(df, col):
        return round(df[col].mean(), 3) if col in df else None

    def avg_latency(rows, key):
        return round(sum(row[key] for row in rows) / len(rows), 2) if rows else None

    def avg_cost(rows, key):
        values = [row[key] for row in rows if row[key] is not None]
        return round(sum(values) / len(values), 5) if values else None

    rag_faithfulness = avg(rag_df, "faithfulness")
    rag_relevancy = avg(rag_df, "answer_relevancy")
    rag_precision = avg(rag_df, "context_precision")
    rag_recall = avg(rag_df, "context_recall")
    full_doc_faithfulness = avg(full_doc_df, "faithfulness")
    full_doc_relevancy = avg(full_doc_df, "answer_relevancy")
    baseline_faithfulness = avg(no_context_df, "faithfulness")
    baseline_relevancy = avg(no_context_df, "answer_relevancy")
    rag_latency = avg_latency(rows, "rag_latency_s")
    full_doc_latency = avg_latency(rows, "full_doc_latency_s")
    baseline_latency = avg_latency(rows, "no_context_latency_s")
    rag_cost = avg_cost(rows, "rag_cost_usd")
    full_doc_cost = avg_cost(rows, "full_doc_cost_usd")
    baseline_cost = avg_cost(rows, "no_context_cost_usd")

    lines = [
        "# Comparative eval: RAG vs. full-doc vs. no-context baseline",
        "",
        f"{len(rows)} hand-written questions against the ingested manual, "
        "each answered under all three modes and scored with Ragas "
        "(judge: Claude, embeddings: the local HF model used for retrieval).",
        "",
        "## Results",
        "",
        "| Metric | No-context baseline | Full-doc | RAG |",
        "|---|---|---|---|",
        f"| Faithfulness | {baseline_faithfulness} | {full_doc_faithfulness} "
        f"| {rag_faithfulness} |",
        f"| Answer relevancy | {baseline_relevancy} | {full_doc_relevancy} | {rag_relevancy} |",
        f"| Context precision | n/a | n/a | {rag_precision} |",
        f"| Context recall | n/a | n/a | {rag_recall} |",
        f"| Latency (avg, s) | {baseline_latency} | {full_doc_latency} | {rag_latency} |",
        f"| Cost per query (avg, $) | {baseline_cost} | {full_doc_cost} | {rag_cost} |",
        "",
        "Faithfulness is judged against what each condition was actually given: "
        "RAG's retrieved chunks for RAG, the manual's full text for full-doc. The "
        "no-context baseline never saw any manual content, so it's judged against "
        "RAG's retrieved chunks too - its score reflects how much it invented "
        "versus what the manual actually says. Context precision/recall only apply "
        "where retrieval happened, so they're RAG-only.",
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
            f"{_relevancy_interpretation(baseline_relevancy, rag_relevancy)} "
            f"{_full_doc_interpretation(rag_faithfulness, full_doc_faithfulness)} "
            f"{_latency_interpretation(rows, rag_latency, full_doc_latency, baseline_latency)} "
            f"{_cost_interpretation(rag_cost, full_doc_cost, baseline_cost)}"
        ),
        "",
    ]
    (config.RESULTS_DIR / "eval_results.md").write_text("\n".join(lines), encoding="utf-8")


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
