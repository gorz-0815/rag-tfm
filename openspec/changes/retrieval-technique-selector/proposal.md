## Why

Raised in review (PR #7), as a follow-up to the `rag-context-continuity` discussion about retrieval quality: reranking, hybrid search (BM25 + dense), HyDE, MMR, RAPTOR/hierarchical summarization, and GraphRAG were all mentioned as options beyond plain top-k similarity retrieval. Retrieval quality is explicitly the focus of this application (per its stated purpose), so these are all worth evaluating rather than dismissing outright — but none are designed or scoped yet. This is a stub to track the idea, not a committed design.

## What Changes

(Not designed yet.) Rough shape: let the user pick a retrieval technique at query time (CLI flag, likely alongside the existing `--full-doc`/`--no-context` mode flags on `python -m src.ask`), each technique shown with a short description of what it does and its tradeoffs — reviewer specifically suggested this could include small ASCII-art visuals in the CLI output to make the tradeoffs legible at a glance, not just a name. Candidate techniques to eventually support (cheapest to most involved): reranking, hybrid search (BM25 + dense vectors), HyDE, MMR, RAPTOR/hierarchical summarization, GraphRAG.

## Capabilities

### New Capabilities
(none yet — stub only, no spec-level commitment until this is picked up)

### Modified Capabilities
(none — would likely modify `manual-qa-cli`'s retrieval behavior once designed, not add a new capability)

## Impact

Not assessed yet. Open questions to resolve when this is picked up: whether to build custom implementations of each technique or lean on llama_index's built-ins where available (e.g. it already ships rerankers, HyDE query transforms, and auto-merging retrieval), how a technique selector interacts with the `--full-doc`/`--no-context` mode flags, whether this belongs in `comparative-eval`'s Ragas scoring as another axis of comparison, and how "small ASCII-art visuals per technique" should actually look in a single-shot CLI's stdout output.
