# Sample Trace Walkthrough

Verified 2026-08-22 against the committed sample manual
(`data/manuals/aquaflow-200-manual.pdf`), one trace per `ask` mode, all
confirmed present via the Langfuse API (`client.api.trace.get(...)`, same
project the Cloud UI reads from). Question asked in all three modes:
*"How long should I soak a new filter cartridge before using it?"*

Note on the manual: it was regenerated (bigger than the original PR #7
version - 4 pages / ~1,900 words instead of 3 sections / ~550 words) after
the first pass of this verification showed a degenerate case: on the small
original manual, RAG mode's overlapping top-k chunks summed to *more*
input tokens than full-doc mode's whole-document extraction, which is
backwards from the intended RAG-is-cheaper-per-query story. The general
fix (chunking parameters that scale with document size) is tracked as the
`dynamic-chunking-by-doc-size` stub change; regenerating a bigger sample
manual was the pragmatic fix so this walkthrough's numbers actually
demonstrate what they're supposed to, given fixed chunking works fine once
the manual isn't tiny relative to `chunk_size`/`top_k`.

## RAG mode — trace `3401e960844830d7787bcafdc7285758`

`python -m src.ask "How long should I soak a new filter cartridge before using it?" data/manuals/aquaflow-200-manual.pdf`

- Trace name: `ask_rag`, total latency: **11.1 s** (Langfuse's `latency`
  field is in seconds, not ms — worth noting since it's easy to misread)
- 7 observations, auto-captured by `LlamaIndexInstrumentor` plus two
  manual spans from `src/tracing.py`/`src/query.py`/`src/vector_store.py`:
  - `load_embedding_model` (SPAN) — **7.2 s**, by far the largest single
    cost in this trace. Wraps `vector_store.configure_embed_model()`
    constructing `HuggingFaceEmbedding`, which loads the
    `BAAI/bge-small-en-v1.5` SentenceTransformer weights. Without this
    manual span the time was invisible — it happens inside `ask_rag` but
    isn't a LlamaIndex call the auto-instrumentor sees. It's already been
    reduced from an initial ~10.6 s by skipping HuggingFace Hub's
    online freshness checks once the model is confirmed cached locally
    (`vector_store._model_already_cached()` sets `HF_HUB_OFFLINE` before
    the model is imported); the remainder is Python import overhead of
    `torch`/`sentence_transformers` plus actual weight materialization,
    which is a per-process cost of this CLI's single-shot design (see the
    `interactive-cli` stub for the real fix — a warm long-running process
    would pay this once, not per query).
  - `HuggingFaceEmbedding.get_query_embedding` (+ its internal
    `_get_query_embedding` child) — 0.03 s, embeds the question for
    retrieval
  - `VectorIndexRetriever.retrieve` (+ its internal `_retrieve` child) —
    0.06 s, top-k chunk retrieval against the manual's Chroma collection
  - `Anthropic.chat` (GENERATION) — 1.9 s, **1,838 input** / 31 output /
    1,869 total tokens
- Answer: *"...soak a new filter cartridge in cold water for **15
  minutes** before first use."* — Sources: `aquaflow-200-manual.pdf`

## Full-doc mode — trace `c5acb145c80585f6b9451fd643e11b3c`

`python -m src.ask "How long should I soak a new filter cartridge before using it?" data/manuals/aquaflow-200-manual.pdf --full-doc`

- Trace name: `ask_full_doc`, total latency: 3.5 s
- 3 observations:
  - `extract_manual_text` (SPAN) — the manual `traced_span` from
    `src/query.py::ask_full_doc`, covering the pypdf text-extraction step
    that LlamaIndex's own instrumentation can't see (not a LlamaIndex
    operation)
  - `Anthropic.chat` (GENERATION) — 2.1 s, **2,891 input** / 67 output /
    2,958 total tokens
- Answer: same 15-minutes grounded answer, cited to
  `aquaflow-200-manual.pdf`, built from the whole document rather than
  retrieved chunks — visibly more input tokens than RAG mode (2,891 vs.
  1,838), which is the expected direction now that the manual is big
  enough for RAG's top-k retrieval to be a genuine fraction of the whole
  document rather than nearly all of it.

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

## Token cost summary

| Mode | Input tokens | Output tokens |
|---|---|---|
| RAG | 1,838 | 31 |
| Full-doc | 2,891 | 67 |
| No-context | 22 | 221 |

RAG costs more input tokens than the bare no-context baseline (expected —
it's paying for grounding) but meaningfully less than full-doc on this
manual, since retrieval narrows the context to the relevant top-k chunks
instead of sending the whole document every time.

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
