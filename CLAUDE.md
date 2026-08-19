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
4. **PRs are scoped by reviewable weight, not mechanically one-per-section.**
   `tasks.md` sections (1. Scaffold, 2. Corpus, 3. Ingestion, 4. CLI,
   5. Tracing, 6. Eval, 7. README) are the starting unit, but thin/wiring-only
   sections get bundled into an adjacent section rather than shipped as their
   own PR (sections 1+2 turned out too small standalone — fold scaffold+corpus
   together next time; section 5/Tracing is wiring into the query path from
   section 4/CLI, so it rides along with that PR instead of going solo).
   Split into its own PR only where a section is a substantial, independent
   capability slice (ingestion, CLI, eval). Don't commit mid-section with a
   half-working capability.
5. **Worktree-per-PR:** each section's work happens in its own worktree/branch,
   pushed as its own PR against `main`. Don't stack unrelated section work into
   an already-open PR's branch.
6. **Review loop:** the user reviews on GitHub and leaves inline comments
   directly on the PR's code — they don't hand back a written list. Once told
   to work the PR, invoke the `pr-comment-triage` skill: it enumerates the
   PR's outstanding review comments, makes the change and replies in-thread
   for clear asks, and replies with a clarifying question (no guessing) for
   ambiguous ones. Only merge once comments are resolved and the user says so.
7. When every task in `tasks.md` is checked, use `openspec-archive-change` to
   move the change to `openspec/changes/archive/` and sync its delta specs
   into `openspec/specs/`.
8. Other changes under `openspec/changes/` (`interactive-cli`,
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
