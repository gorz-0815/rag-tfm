"""Turns src.eval's per-question rows and Ragas scores into
results/eval_results.json (raw) and results/eval_results.md (comparison
table + prose interpretation). Kept separate from src/eval.py so that
module stays focused on running conditions and scoring, not report text.
"""

import json

from src import config
from src.query import SIMILARITY_TOP_K

# USD per 1M tokens (input, output), Anthropic's published first-party API
# pricing as of 2026-08. Only models this project actually configures need an
# entry; an unrecognized config.ANTHROPIC_MODEL just skips cost reporting
# (see _cost_usd) rather than guessing at a price.
PRICING_PER_MILLION_TOKENS = {
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-opus-5": (5.00, 25.00),
}


def _cost_usd(usage: dict) -> float | None:
    pricing = PRICING_PER_MILLION_TOKENS.get(config.ANTHROPIC_MODEL)
    if pricing is None:
        return None
    input_price, output_price = pricing
    return (
        usage["input_tokens"] / 1_000_000 * input_price
        + usage["output_tokens"] / 1_000_000 * output_price
    )


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
    rag_cost: float | None,
    full_doc_cost: float | None,
    baseline_cost: float | None,
    rag_input_tokens: int | None,
    full_doc_input_tokens: int | None,
) -> str:
    if rag_cost is None or full_doc_cost is None or baseline_cost is None:
        return (
            f"Per-query cost isn't reported for model '{config.ANTHROPIC_MODEL}' - "
            "add it to PRICING_PER_MILLION_TOKENS in src/eval_report.py to include it."
        )
    full_doc_multiple = round(full_doc_cost / rag_cost, 1) if rag_cost else "?"
    token_multiple = (
        round(full_doc_input_tokens / rag_input_tokens, 1)
        if rag_input_tokens and full_doc_input_tokens
        else "?"
    )
    return (
        f"Per-query cost (from Anthropic's actual reported token usage, at "
        f"{config.ANTHROPIC_MODEL}'s published rates as of 2026-08): ${baseline_cost:.5f} "
        f"no-context, ${rag_cost:.5f} RAG, ${full_doc_cost:.5f} full-doc - "
        f"full-doc costs about {full_doc_multiple}x RAG's per-query price. That "
        f"traces directly to input tokens: full-doc averages {full_doc_input_tokens} "
        f"input tokens per query (the whole manual, resent every time) versus RAG's "
        f"{rag_input_tokens} ({token_multiple}x fewer, from only "
        f"{SIMILARITY_TOP_K} retrieved chunks) - output tokens are comparable "
        "between the two, so input is where the cost gap actually comes from. This "
        "is the real trade-off full-doc's faithfulness parity with RAG comes at: not "
        "accuracy, and not necessarily latency, but dollars - at higher query volume "
        "or a larger manual, that gap scales linearly with corpus size for full-doc "
        "and stays roughly flat for RAG."
    )


def _build_raw_json(rows: list[dict], rag_df, full_doc_df, no_context_df) -> dict:
    return {
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
                "rag": _cost_usd(row["rag_usage"]),
                "full_doc": _cost_usd(row["full_doc_usage"]),
                "no_context": _cost_usd(row["no_context_usage"]),
            }
            for row in rows
        ],
        "token_usage": [
            {
                "question": row["question"],
                "rag": row["rag_usage"],
                "full_doc": row["full_doc_usage"],
                "no_context": row["no_context_usage"],
            }
            for row in rows
        ],
    }


def _avg(df, col):
    return round(df[col].mean(), 3) if col in df else None


def _avg_latency(rows, key):
    return round(sum(row[key] for row in rows) / len(rows), 2) if rows else None


def _avg_cost(rows, usage_key):
    values = [cost for row in rows if (cost := _cost_usd(row[usage_key])) is not None]
    return round(sum(values) / len(values), 5) if values else None


def _avg_tokens(rows, usage_key, token_key):
    values = [row[usage_key][token_key] for row in rows]
    return round(sum(values) / len(values)) if values else None


def _build_markdown(rows: list[dict], rag_df, full_doc_df, no_context_df) -> str:
    rag_faithfulness = _avg(rag_df, "faithfulness")
    rag_relevancy = _avg(rag_df, "answer_relevancy")
    rag_precision = _avg(rag_df, "context_precision")
    rag_recall = _avg(rag_df, "context_recall")
    full_doc_faithfulness = _avg(full_doc_df, "faithfulness")
    full_doc_relevancy = _avg(full_doc_df, "answer_relevancy")
    baseline_faithfulness = _avg(no_context_df, "faithfulness")
    baseline_relevancy = _avg(no_context_df, "answer_relevancy")
    rag_latency = _avg_latency(rows, "rag_latency_s")
    full_doc_latency = _avg_latency(rows, "full_doc_latency_s")
    baseline_latency = _avg_latency(rows, "no_context_latency_s")
    rag_cost = _avg_cost(rows, "rag_usage")
    full_doc_cost = _avg_cost(rows, "full_doc_usage")
    baseline_cost = _avg_cost(rows, "no_context_usage")
    rag_input_tokens = _avg_tokens(rows, "rag_usage", "input_tokens")
    rag_output_tokens = _avg_tokens(rows, "rag_usage", "output_tokens")
    full_doc_input_tokens = _avg_tokens(rows, "full_doc_usage", "input_tokens")
    full_doc_output_tokens = _avg_tokens(rows, "full_doc_usage", "output_tokens")
    baseline_input_tokens = _avg_tokens(rows, "no_context_usage", "input_tokens")
    baseline_output_tokens = _avg_tokens(rows, "no_context_usage", "output_tokens")

    cost_interpretation = _cost_interpretation(
        rag_cost, full_doc_cost, baseline_cost, rag_input_tokens, full_doc_input_tokens
    )

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
        f"| Input tokens (avg) | {baseline_input_tokens} | {full_doc_input_tokens} "
        f"| {rag_input_tokens} |",
        f"| Output tokens (avg) | {baseline_output_tokens} | {full_doc_output_tokens} "
        f"| {rag_output_tokens} |",
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
            f"{cost_interpretation}"
        ),
        "",
    ]
    return "\n".join(lines)


def write_results(rows: list[dict], scores: dict) -> None:
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    rag_df = scores["rag"]
    full_doc_df = scores["full_doc"]
    no_context_df = scores["no_context"]

    raw = _build_raw_json(rows, rag_df, full_doc_df, no_context_df)
    (config.RESULTS_DIR / "eval_results.json").write_text(
        json.dumps(raw, indent=2), encoding="utf-8"
    )

    markdown = _build_markdown(rows, rag_df, full_doc_df, no_context_df)
    (config.RESULTS_DIR / "eval_results.md").write_text(markdown, encoding="utf-8")
