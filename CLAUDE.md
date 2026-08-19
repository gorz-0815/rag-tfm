# rag-tfm — agent workflow

Small RAG demo (ingest PDF manuals, cited Q&A, Langfuse tracing, Ragas eval vs.
no-RAG baseline). Planning is done; implementation happens through OpenSpec.

## How work flows

1. All approved work lives as an OpenSpec change under `openspec/changes/<name>/`
   (proposal.md, design.md, specs/, tasks.md). The active change right now is
   `rag-tfm-mvp` — read its `design.md` before touching code; it has already
   resolved most implementation-level decisions (LLM, embeddings, vector store,
   chunking defaults, tracing integration).
2. Implement via the `openspec-apply-change` skill, not ad hoc edits. It works
   through `tasks.md` top to bottom, checking items off as they're verified.
3. **Smallest unit of work is one task checkbox**, not a whole numbered section.
   Each task has an explicit verify step (e.g. "run ingestion against a test
   PDF, confirm storage/ is created") — implement, verify, check it off, then
   move to the next task. Don't batch multiple unrelated checkboxes into one
   uncommitted pile.
4. Commit at section boundaries (1. Scaffold, 2. Corpus, 3. Ingestion, ...) —
   each section finishes at a working, testable milestone and maps to one of
   the four capabilities in the proposal. Don't commit mid-section with a
   half-working capability.
5. When every task in `tasks.md` is checked, use `openspec-archive-change` to
   move the change to `openspec/changes/archive/` and sync its delta specs
   into `openspec/specs/`.
6. Other changes under `openspec/changes/` (`interactive-cli`,
   `pluggable-llm-backend`, `openai-embeddings-option`, `sample-corpus-sourcing`)
   are proposal-only stubs for deferred work — do not implement them alongside
   `rag-tfm-mvp` unless the user explicitly asks to pull one in.

## Guardrails specific to this project

- Never commit `.env`, `storage/`, or real contents of `data/manuals/` — the
  corpus is user-supplied and gitignored; only a `.gitkeep` belongs in git for
  now (see `sample-corpus-sourcing` stub for the eventual sample corpus).
- Confirm with the user before the first push / adding the `github` remote —
  `tasks.md` 7.8 explicitly calls this out as needing separate confirmation.
- Repo is not "clone and run" out of the box until a sample corpus exists —
  this is an accepted trade-off, not a bug to fix silently.
