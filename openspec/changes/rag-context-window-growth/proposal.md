## Why

Raised in PR #10 review: today's eval only measures single-shot questions,
each mode starting from a clean context. Once `interactive-cli` (session/REPL
mode, multiple questions per process) is picked up, RAG's per-turn retrieved
chunks would accumulate across a session's history, while `--full-doc`'s
context is only the manual's full text, potentially added once. It's an open
question whether RAG's accumulated context could grow to rival or exceed
full-doc's per-turn cost over a long-enough session, and whether answer
quality degrades as that history grows — neither is measured today, and
`interactive-cli`'s own proposal doesn't cover it. This is a stub to track
the idea, not a committed design.

## What Changes

(Not designed yet.) Rough shape: once a session/REPL mode exists
(`interactive-cli`), extend the comparative eval to a multi-turn scenario —
run a sequence of related questions in one session under RAG and full-doc,
track cumulative context size and per-turn cost/latency across turns, and
score answer quality (e.g. faithfulness) per turn to check for degradation
as history accumulates.

## Capabilities

### New Capabilities
(none yet — stub only, no spec-level commitment until this is picked up)

### Modified Capabilities
(none — would extend `comparative-eval`'s scope to multi-turn scenarios when
picked up, not add a new capability)

## Impact

Not assessed yet. Depends on `interactive-cli` existing first (no session
mode to measure otherwise). Open questions to resolve when this is picked
up: how session history is carried per-turn in RAG mode (full history
re-sent vs. summarized vs. windowed), whether the same question applies to
full-doc mode's history handling, and what "quality degradation" should be
scored against (Ragas faithfulness per turn, or something else).
