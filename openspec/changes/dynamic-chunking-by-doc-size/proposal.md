## Why

Chunking/retrieval parameters (`CHUNK_SIZE`, `CHUNK_OVERLAP`, `SIMILARITY_TOP_K`)
are currently fixed defaults applied to every ingested manual regardless of its
length. This was observed to produce a counterintuitive result while verifying
Section 5's tracing: on the small committed sample manual
(`aquaflow-200-manual.pdf`, ~3.2k extracted chars), RAG mode's top-k retrieved
chunks — inflated by `CHUNK_OVERLAP`'s duplicated boundary text — summed to
*more* input tokens (917) than full-doc mode's single unbroken extraction of the
entire manual (862, see `results/sample_trace.md`). For large manuals the fixed
defaults are fine (retrieved chunks stay a small fraction of the document); the
crossover only shows up when a manual is short relative to `chunk_size` /
`chunk_overlap` / `top_k`, which is exactly the situation a small demo/sample
manual is likely to hit. Stub only — not designed yet.

## What Changes

Rough shape, not designed:
- Some rule scaling chunk size, overlap, and/or `similarity_top_k` to the
  ingested document's length (e.g. token count), rather than the current fixed
  `src/config.py` defaults applied uniformly
- Goal: avoid RAG being less token-efficient than full-doc on short documents
  while preserving RAG's efficiency advantage on long ones
- Open question even at this rough level: does this belong in `src/ingest.py`
  (decided once at ingestion time, baked into the persisted index) or
  `src/query.py` (decided per query, e.g. adaptive `top_k`)? Not resolved here.

## Capabilities

None yet — stub only, no spec-level commitment until this is picked up.

## Impact

Not assessed yet. Touches `src/config.py`'s fixed `CHUNK_SIZE`/`CHUNK_OVERLAP`
defaults and `src/query.py`'s `SIMILARITY_TOP_K` constant, and interacts with
`src/ingest.py`'s per-manual Chroma collection model — but the actual shape of
that interaction depends on design decisions not made yet.
