# Sample Trace Walkthrough

Verified 2026-08-22 against the committed sample manual
(`data/manuals/aquaflow-200-manual.pdf`), one trace per `ask` mode, all
confirmed present via the Langfuse API (`client.api.trace.get(...)`, same
project the Cloud UI reads from). Question asked in all three modes:
*"How long should I soak a new filter cartridge before using it?"*

## RAG mode — trace `28a74621e36432956ccd08c1998e9c17`

`python -m src.ask "How long should I soak a new filter cartridge before using it?" data/manuals/aquaflow-200-manual.pdf`

- Trace name: `ask_rag`, total latency: **14.2 s** (Langfuse's `latency`
  field is in seconds, not ms — worth noting since it's easy to misread)
- 7 observations, auto-captured by `LlamaIndexInstrumentor` plus two
  manual spans from `src/tracing.py`/`src/query.py`:
  - `load_embedding_model` (SPAN) — **10.6 s**, by far the largest single
    cost in this trace. This wraps `vector_store.configure_embed_model()`
    constructing `HuggingFaceEmbedding`, which loads the
    `BAAI/bge-small-en-v1.5` SentenceTransformer weights (plus HF Hub
    metadata checks). Without this manual span the time was invisible —
    it happens inside `ask_rag` but isn't a LlamaIndex call the
    auto-instrumentor sees, so it just inflated the parent span's wall
    time with no attribution. It's a per-process cost (this CLI starts a
    fresh process per invocation), not a per-query one — see the README's
    cost/latency trade-offs section.
  - `HuggingFaceEmbedding.get_query_embedding` (+ its internal
    `_get_query_embedding` child) — 0.03 s, embeds the question for
    retrieval
  - `VectorIndexRetriever.retrieve` (+ its internal `_retrieve` child) —
    0.06 s, top-k chunk retrieval against the manual's Chroma collection
  - `Anthropic.chat` (GENERATION) — 1.6 s, 917 input / 31 output / 948
    total tokens
- Answer: *"...soak a new filter cartridge in cold water for **15
  minutes** before using it."* — Sources: `aquaflow-200-manual.pdf`

## Full-doc mode — trace `23d60dd32eebe0987b5a44675eb25f69`

`python -m src.ask "How long should I soak a new filter cartridge before using it?" data/manuals/aquaflow-200-manual.pdf --full-doc`

- Trace name: `ask_full_doc`, total latency: 3.0 s
- 3 observations:
  - `extract_manual_text` (SPAN) — the manual `traced_span` from
    `src/query.py::ask_full_doc`, covering the pypdf text-extraction step
    that LlamaIndex's own instrumentation can't see (not a LlamaIndex
    operation)
  - `Anthropic.chat` (GENERATION) — 862 input / 31 output / 893 total
    tokens, 1.7 s
- Answer: same 15-minutes grounded answer, cited to
  `aquaflow-200-manual.pdf`, this time built from the whole document
  rather than retrieved chunks (visibly more input tokens than RAG mode
  for a comparable output)

## No-context mode — trace `f4953ebffdc4f582b0949f2b18563c14`

`python -m src.ask "How long should I soak a new filter cartridge before using it?" --no-context`

- Trace name: `ask_no_context`, total latency: 5.3 s
- 2 observations, both auto-captured, no retrieval/extraction step (as
  expected — this mode sends only the bare question):
  - `Anthropic.complete` (GENERATION) — 22 input / 221 output / 243 total
    tokens
  - `Anthropic.chat` (GENERATION) — mirrors the same call/usage; both are
    emitted by the LlamaIndex `Anthropic` LLM class's instrumentation for
    a `.complete()` call
- Answer: generic, product-agnostic guidance ("most cartridges don't need
  soaking... some pool filters benefit from a 15-30 minute soak"),
  uncited, and doesn't match the manual's actual instruction — the
  RAG/full-doc-vs-no-context gap this project is built to demonstrate.

## Graceful degradation

Not separately re-run against a real outage for this walkthrough (see
`tests/test_tracing.py::test_flush_tracing_swallows_client_errors` for
the automated check), but confirmed the two related paths work as
designed:
- With no Langfuse credentials configured, `init_tracing()`,
  `flush_tracing()`, and `traced_span()` are all silent no-ops (no
  warnings, no attempted network calls) — verified by running `ask` with
  `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` unset.
- With credentials configured but the flush failing, `flush_tracing()`
  catches the exception and prints `Warning: tracing flush failed (...)`
  after the answer, never before it and never in place of it.
