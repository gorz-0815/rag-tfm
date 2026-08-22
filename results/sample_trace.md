# Sample Trace Walkthrough

Verified 2026-08-22 against the committed sample manual
(`data/manuals/aquaflow-200-manual.pdf`), one trace per `ask` mode, all
confirmed present via the Langfuse API (`client.api.trace.get(...)`, same
project the Cloud UI reads from). Question asked in all three modes:
*"How long should I soak a new filter cartridge before using it?"*

## RAG mode — trace `b5785f12025d163a2b7615278b438d92`

`python -m src.ask "How long should I soak a new filter cartridge before using it?" data/manuals/aquaflow-200-manual.pdf`

- Trace name: `ask_rag`, total latency: 26.6 ms
- 6 observations, auto-captured by `LlamaIndexInstrumentor` plus the
  `ask_rag` wrapper span from `src/tracing.py`:
  - `HuggingFaceEmbedding.get_query_embedding` (+ its internal
    `_get_query_embedding` child) — embeds the question for retrieval
  - `VectorIndexRetriever.retrieve` (+ its internal `_retrieve` child) —
    top-k chunk retrieval against the manual's Chroma collection
  - `Anthropic.chat` (GENERATION) — 917 input / 31 output / 948 total
    tokens, 6.7 ms
- Answer: *"...soak a new filter cartridge in cold water for **15
  minutes** before using it."* — Sources: `aquaflow-200-manual.pdf`

## Full-doc mode — trace `23d60dd32eebe0987b5a44675eb25f69`

`python -m src.ask "How long should I soak a new filter cartridge before using it?" data/manuals/aquaflow-200-manual.pdf --full-doc`

- Trace name: `ask_full_doc`, total latency: 3.0 ms
- 3 observations:
  - `extract_manual_text` (SPAN) — the manual `traced_span` from
    `src/query.py::ask_full_doc`, covering the pypdf text-extraction step
    that LlamaIndex's own instrumentation can't see (not a LlamaIndex
    operation)
  - `Anthropic.chat` (GENERATION) — 862 input / 31 output / 893 total
    tokens, 1.7 ms
- Answer: same 15-minutes grounded answer, cited to
  `aquaflow-200-manual.pdf`, this time built from the whole document
  rather than retrieved chunks (visibly more input tokens than RAG mode
  for a comparable output)

## No-context mode — trace `f4953ebffdc4f582b0949f2b18563c14`

`python -m src.ask "How long should I soak a new filter cartridge before using it?" --no-context`

- Trace name: `ask_no_context`, total latency: 5.3 ms
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
