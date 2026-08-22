## Why

`ask_rag()` in `src/query.py` joins retrieved chunks in retrieval-rank (relevance) order, not their original position in the source manual. Raised in review (PR #7): when an answer spans two non-adjacent chunks, or a procedure gets split mid-step across a chunk boundary, the LLM only sees disjoint fragments and has to bridge that gap itself — an inherent limitation of plain top-k chunk retrieval, and the same trade-off already flagged in `rag-tfm-mvp`'s `design.md` (Risks/Trade-offs: smaller chunks risk splitting a procedure mid-step). Reviewer asked for mitigation options and explicitly deferred acting on any of them — including the cheapest one — to keep this PR's scope small. This is a stub to track the idea, not a committed design.

## What Changes

(Not designed yet.) Options discussed, cheapest to most involved:
1. Sort retrieved nodes by original document position (e.g. `start_char_idx`) before joining, instead of retrieval-rank order. Near-free, reorders what's already fetched, doesn't fix a genuinely disjoint answer but keeps a spread-out one closer to reading order.
2. Neighbor-chunk expansion: for each retrieved chunk, also fetch its immediate neighbors from the same document, so a split procedure gets its surrounding steps even if only one side matched the query.
3. LlamaIndex's built-in sentence-window / auto-merging retrieval (`SentenceWindowNodeParser` + `MetadataReplacementPostProcessor`, or `AutoMergingRetriever`) — index small chunks for precise matching, expand to a larger parent window/chunk at synthesis time. The more structurally correct fix for the split-procedure case, but touches `src/ingest.py`'s chunking strategy too, not just retrieval.
4. Anthropic-style contextual retrieval — prepend a short LLM-generated context summary to each chunk before embedding, so a chunk is more self-contained even in isolation.

## Capabilities

### New Capabilities
(none yet — stub only, no spec-level commitment until this is picked up)

### Modified Capabilities
(none — would modify `manual-qa-cli`'s retrieval/context-assembly behavior when picked up, not add a new capability)

## Impact

Not assessed yet. Open questions to resolve when this is picked up: whether to do the cheap reorder-only fix (#1) versus the structurally correct sentence-window/auto-merging fix (#3), whether #3's chunking-strategy change should itself revisit the `rag-tfm-mvp` chunk-size/overlap trade-off documented in that change's `design.md`, and whether any of this materially changes `comparative-eval`'s Ragas context-precision/recall numbers.
