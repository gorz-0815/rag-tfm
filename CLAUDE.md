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
4. **PRs are scoped to match `specs/` capability boundaries, not raw
   `tasks.md` section count.** Sections 3-6 (Ingestion, CLI, Tracing, Eval)
   each map 1:1 to one of the four capabilities under `openspec/changes/
   rag-tfm-mvp/specs/` and each has its own verify step — keep these as one
   PR per section/capability, tracing included, even though it wires into
   the CLI's query path. Sections 1+2 (Scaffold, Corpus) aren't capabilities
   at all — no spec of their own, just repo plumbing — so bundle those two
   into a single prep PR instead of splitting them (learned this the hard
   way: shipped as two separate PRs first, both too small to be worth
   reviewing on their own). Section 7 (README) stands alone as the final
   wrap-up PR. Don't commit mid-section with a half-working capability.
5. **Worktree-per-PR:** each section's work happens in its own worktree/branch,
   pushed as its own PR against `main`. Don't stack unrelated section work into
   an already-open PR's branch.
6. **Review loop:** the user reviews on GitHub and leaves inline comments
   directly on the PR's code — they don't hand back a written list. Once told
   to work the PR, invoke the `pr-comment-triage` skill: it enumerates the
   PR's outstanding review comments, makes the change and replies in-thread
   for clear asks, and replies with a clarifying question (no guessing) for
   ambiguous ones. Only merge once comments are resolved and the user says so.
7. **Testing: pytest for logic that doesn't need heavy runtime deps.**
   `tasks.md`'s own "Verify" steps are manual end-to-end runs against real
   deps (a real PDF, a real Anthropic call, the Langfuse UI) — that stays as
   is, it's not being replaced. Alongside that, add `tests/` pytest coverage
   for the cheap, dependency-light logic in each section (guard clauses,
   config wiring, parsing/formatting) — e.g. `src/ingest.py`'s
   `validate_manuals_dir` is a plain function tests exercise directly, while
   the actual embedding/Chroma/LLM calls stay manual-only. Keep heavy
   third-party imports (`llama_index`, `chromadb`, embedding libs) inside the
   functions that need them rather than at module level, so importing the
   module for a unit test doesn't require the full dependency stack to be
   installed. Tests live in `tests/`, mirroring `src/`.
8. **Lint/format: Ruff, applied automatically via pre-commit.** Config is in
   `pyproject.toml` (`[tool.ruff]`); the hook is `language: system` (calls
   the `ruff` already in `requirements.txt`) rather than pre-commit's own
   managed env, because that path hit a Windows long-path build failure.
   After `pip install -r requirements.txt`, run `pre-commit install` once per
   clone so `ruff check --fix` + `ruff format` run automatically on every
   `git commit`. If a hook run modifies files, re-stage and commit again —
   that's expected pre-commit behavior, not a failure.
9. When every task in `tasks.md` is checked, use `openspec-archive-change` to
   move the change to `openspec/changes/archive/` and sync its delta specs
   into `openspec/specs/`.
9. Other changes under `openspec/changes/` (`interactive-cli`,
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
- If a worktree/checkout lives under a hidden ancestor directory (e.g.
  `.claude/worktrees/<name>/`), `SimpleDirectoryReader`'s default
  `exclude_hidden=True` treats every file under it as hidden and skips it —
  `src/ingest.py` already passes `exclude_hidden=False` to work around this;
  don't revert that without re-checking ingestion still finds manuals from
  such a checkout.
