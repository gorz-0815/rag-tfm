## Why

This project is a small, finished demonstration of RAG development, LLMOps tracing, and model-quality evaluation. A generic "RAG over vendor docs" demo doesn't differentiate; a comparative eval that empirically proves RAG's value over a no-RAG baseline does.

## What Changes

- New RAG application: ingest openly-licensed technical manuals (PDF, text-only) into a local vector index and answer natural-language questions about them, with citations to source chunks.
- New single-shot CLI command (`ask`) as v1 surface — no interactive/session mode yet (explicitly deferred to a future change).
- New end-to-end tracing of every query (chunks retrieved, prompt sent, latency per step, token usage) via Langfuse.
- New comparative evaluation harness: run the same hand-written question set through a no-RAG baseline and the RAG pipeline, score both with Ragas metrics (faithfulness, answer relevancy always; context precision/recall for the RAG condition), and produce an interpreted results report — not just raw numbers.
- New README documenting setup, architecture, a sample trace walkthrough, eval results and interpretation, and an explicit cost/latency/scalability trade-offs section.

## Capabilities

### New Capabilities
- `manual-ingestion`: load PDF manuals, chunk them, embed with a local embedding model, and persist a local vector index (Chroma) that queries run against.
- `manual-qa-cli`: single-shot `ask` CLI command that answers a question against the indexed manuals using Claude (Anthropic) + retrieved context, returning an answer with cited source chunks; also supports a no-RAG mode (bare LLM, no retrieval) for baseline comparison.
- `query-tracing`: every `ask` invocation (both RAG and no-RAG modes) is traced end-to-end in Langfuse — retrieved chunks, prompt, latency per step, token usage.
- `comparative-eval`: a hand-written Q&A eval set (~15-20 questions with verified ground-truth answers) run through both no-RAG and RAG conditions, scored with Ragas metrics, output as an interpreted comparison report.

### Modified Capabilities
(none — first change in this project)

## Impact

- New project at `F:\dev\rag-tfm`, Python-based (LlamaIndex, llama-index-llms-anthropic, local HF embeddings, Chroma, Langfuse SDK, Ragas, langchain-anthropic for the Ragas judge LLM).
- New dependency: Anthropic API key (user-provided, local `.env`, never committed) and a Langfuse account/keys (cloud free tier, local `.env`).
- New data: a small set of openly-licensed sample manuals committed to the repo for out-of-the-box reproducibility; a `data/manuals/` directory for the user's own private manuals is gitignored.
- Publishes to GitHub under the `gorz-0815` account via HTTPS remote.
