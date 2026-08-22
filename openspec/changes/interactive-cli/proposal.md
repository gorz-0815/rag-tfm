## Why

`rag-tfm-mvp` ships a single-shot `ask` command only. A richer CLI (ask multiple questions in one session, see retrieved sources inline, switch between RAG/no-context mode without re-invoking the process) was explicitly wanted long-term but deferred to keep the MVP small and finishable, and review feedback (PR #1) asked for it to be tracked so it isn't lost. This is a stub to track the idea, not a committed design.

## What Changes

- (Not designed yet.) Rough shape: a session/REPL-style CLI entry point alongside the single-shot `ask` command, in-session RAG/no-context mode switching, and a way to inspect retrieved chunks/citations without leaving the session.

## Capabilities

### New Capabilities
(none yet — stub only, no spec-level commitment until this is picked up)

### Modified Capabilities
(none)

## Impact

Not assessed yet. Open questions to resolve when this is picked up: REPL approach (plain loop vs. TUI framework), whether session history carries across questions, and how this interacts with Langfuse tracing.

On that last point: likely both, not one-or-the-other. Langfuse has a `session_id` mechanism (Python SDK: `propagate_attributes(session_id=...)`) that groups multiple *traces* together for replay as one interaction thread - see https://langfuse.com/docs/observability/features/sessions. Each question asked in a REPL session would still get its own trace (as `ask` does today, one per question, per `src/tracing.py::traced_span`), but all traces from one REPL invocation would share a `session_id` so the whole interactive session can be viewed/replayed together in Langfuse, distinct from ad-hoc single-shot `ask` usage. The same `session_id` mechanism would also suit `src/eval.py` (Section 6, not yet built) for grouping one eval run's traces.
