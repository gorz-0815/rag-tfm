---
name: finish-pr
description: Wrap-up audit for a PR once its review comments have been addressed — checks whether tracked work is actually complete (and archivable, if the project uses OpenSpec), verifies the project's own drift/consistency guards still pass, and mines the full review history for patterns worth turning into a guideline or an automated check. Use when the user says "finish the PR", "wrap this PR up", "is this PR done", "finish pr step", or similar.
license: MIT
---

Audit pass for closing out a PR: is the tracked work actually done, do the project's own guard checks still pass, and did the review conversation surface a pattern worth codifying. This is an audit and light process-improvement pass, not a place to sneak in unrelated feature work.

## Process

### 1. Completion / archive check

- If the project tracks work as an OpenSpec change (`openspec/changes/<name>/tasks.md`), count checked vs. unchecked tasks for the *whole* change, not just this PR's section.
- All checked → run (or tell the user to run) `openspec-archive-change` to move it to `openspec/changes/archive/` and sync delta specs into `openspec/specs/`.
- Not all checked → report status honestly (e.g. "21/39 done, Sections 5-7 still open") and do **not** archive. A PR finishing its own scope does not mean the whole tracked change is done.
- If the project doesn't use OpenSpec, look for whatever completion artifact it does use (a tracking issue, a checklist in the PR description) and apply the same "don't declare done until everything's actually checked" discipline.

### 2. Guard-check audit

Run the project's own automated consistency checks — linter, test suite, and anything that specifically guards against docs/spec/code drift (an `openspec validate` pre-commit hook, a test that cross-checks documented CLI flags against the real parser, etc.). If none of these drift-guards exist yet and this PR touched a public interface (CLI flags, config keys, API shape) that got documented somewhere, consider adding a cheap one now — see the "flag-consistency test" pattern: introspect the real interface, grep docs for mentions of it, assert they match. Don't build something elaborate; a targeted test that would have caught the specific drift this PR already had to fix by hand is the right scope.

### 3. Mine the review history

Pull the **entire** review comment history for the PR (all rounds, not just the latest), including both inline comments and any general/issue-level comments:

```
gh api repos/<owner>/<repo>/pulls/<n>/comments --paginate
gh api repos/<owner>/<repo>/issues/<n>/comments --paginate
```

Group by underlying theme (not literal wording — "comment too verbose" and "shorten this comment" and "too much prose" are the same theme). For each theme:

- **1-2 occurrences**: a one-off. Not worth process change; skip, or note it only if it's genuinely surprising.
- **3+ occurrences of the same category**: this is a pattern, not a one-off mistake. Don't just write it down again — build an automated check for it if one is feasible (a pre-commit hook, a lint rule, a test), the same way a repeated "docs drifted from code" complaint became a consistency test. Verify the check actually catches the violation (reintroduce it deliberately, confirm the check fails, revert) before considering it done. If genuinely not automatable (a judgment call, not a mechanical pattern), add it as an explicit guideline in the project's instructions file (CLAUDE.md or equivalent) instead — but automation beats documentation whenever the pattern is checkable.
- Also watch for meta-patterns even without 3+ recurrences: e.g. "check for an existing tracked idea before creating a new one" if that mistake (or near-miss) shows up even once alongside evidence it could easily recur.

### 4. Summarize

Short report: completion status (and whether anything got archived), what guard checks ran and their result, what got automated vs. documented from the review-history scan (with commit references), and anything explicitly left as-is with a one-line reason.

## Guardrails

- Never archive a change with unchecked tasks, even if this PR's own scope is fully done.
- Don't invent a new hook/guideline from a single comment — require actual recurrence, or a clear meta-pattern, before adding process weight. Noise in, noise out.
- Don't use this pass to start unrelated implementation work the review never asked for — if something looks worth doing but is out of scope, note it (a stub, a follow-up) rather than doing it here.
- Confirm before anything destructive or merge-adjacent (archiving is a move+sync, not destructive, but a `git merge`/`gh pr merge` is — never do that as part of this skill without the user explicitly asking).
