## Why

`rag-tfm-mvp` deliberately commits no manual files — per review feedback (PR #1), corpus sourcing/licensing needed more thought and was deferred rather than rushed. Without a committed sample corpus, the repo isn't runnable out of the box for reviewers. This is a stub to track the idea, not a committed design.

## What Changes

- (Not designed yet.) Rough shape: identify one openly-licensed technical manual/guide, verify and record its license/attribution, commit it for out-of-the-box reproducibility, and build the `comparative-eval` question set against it. **Revised down from "a small set of manuals" to one**, per PR #7 review's pivot to a single-manual-at-a-time model (see `rag-tfm-mvp/design.md`'s "Corpus scope" decision) — the app only ever ingests/queries one manual, so sourcing more than one would go unused. Note PR #7 also committed a synthetic, non-licensed sample manual (`data/manuals/aquaflow-200-manual.pdf`, generated content, no real-world source) specifically for demo/test purposes; picking this stub up should decide whether that supersedes the need for an openly-licensed real-world manual, or whether both continue to coexist for different purposes (synthetic for fast/free demo, real openly-licensed one for a more realistic eval).

## Capabilities

### New Capabilities
(none yet — stub only, no spec-level commitment until this is picked up)

### Modified Capabilities
(none — likely touches `manual-ingestion` and `comparative-eval` once designed)

## Impact

Not assessed yet. Open question: what source(s) of openly-licensed manuals to use.
