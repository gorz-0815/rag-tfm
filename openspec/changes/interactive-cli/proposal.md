## Why

`rag-tfm-mvp` ships a single-shot `ask` command only. A richer CLI (ask multiple questions in one session, see retrieved sources inline, switch between RAG/no-RAG mode without re-invoking the process) was explicitly wanted long-term but deferred to keep the MVP small and finishable, and review feedback (PR #1) asked for it to be tracked so it isn't lost. This is a stub to track the idea, not a committed design.

## What Changes

- (Not designed yet.) Rough shape: a session/REPL-style CLI entry point alongside the single-shot `ask` command, in-session RAG/no-RAG mode switching, and a way to inspect retrieved chunks/citations without leaving the session.

## Capabilities

### New Capabilities
(none yet — stub only, no spec-level commitment until this is picked up)

### Modified Capabilities
(none)

## Impact

Not assessed yet. Open questions to resolve when this is picked up: REPL approach (plain loop vs. TUI framework), whether session history carries across questions, and how this interacts with Langfuse tracing (one trace per question vs. per session).
