## Why

`rag-tfm-mvp` uses a local HF embedding model exclusively. A hosted embedding API (e.g. OpenAI) generally retrieves better semantic matches at the cost of an extra dependency/API key. Review feedback (PR #1) asked for this to be tracked as a future option once the MVP's local-only path is proven. This is a stub to track the idea, not a committed design.

## What Changes

- (Not designed yet.) Rough shape: an env-var-selected embedding backend, local HF model remaining the default; a re-ingestion path when switching embedding models, since an existing index isn't compatible across embedding models.

## Capabilities

### New Capabilities
(none yet — stub only, no spec-level commitment until this is picked up)

### Modified Capabilities
(none)

## Impact

Not assessed yet. Open questions: whether this shares the same backend-selection mechanism as `pluggable-llm-backend` or is independent; which hosted embedding provider(s) to support beyond OpenAI.
