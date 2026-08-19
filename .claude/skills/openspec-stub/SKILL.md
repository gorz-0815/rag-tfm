---
name: openspec-stub
description: Track a deferred idea as a proposal-only OpenSpec change (skip_specs:true, no specs/design/tasks). Use when the user says "spec stub", "stub this out in openspec", "track this as a future idea/change" without wanting a full proposal/specs/design/tasks cycle right now.
license: MIT
compatibility: Requires the openspec CLI and an initialized openspec/ root (openspec init).
---

Create a lightweight, valid-but-incomplete OpenSpec change: just enough to record an idea for later without committing to specs, design, or tasks. This is the `skip_specs: true` flag on `.openspec.yaml`, not a separate schema — the change stays on the project's normal schema (usually `spec-driven`), it just isn't required to have deltas.

## When to use this vs a full `/opsx:propose`

- **Stub**: the idea is real and worth not losing, but nobody's ready to design it — a deferred feature, a "later" from review feedback, a parking lot for scope cut during planning.
- **Full propose**: the idea is about to be implemented, or its shape is already clear enough to write real requirements/scenarios.

A stub is not required to ever become a full change — it can sit indefinitely as a tracked-but-unstarted idea. When someone does pick it up, run `/opsx:propose` (or the normal artifact flow) against the same change name to fill in real `specs`/`design`/`tasks` — `skip_specs` can be removed from `.openspec.yaml` at that point since the change will have real deltas.

## Steps

1. **Derive a kebab-case name** from the idea, same convention as `openspec new change`.
2. **Create the change**: `openspec new change "<name>"` (add `--store <id>` if the project uses a store — check `openspec store list --json` per the propose skill's store-selection note).
3. **Add the flag**: append `skip_specs: true` to the generated `openspec/changes/<name>/.openspec.yaml`.
4. **Write `proposal.md` only** — do not create `specs/`, `design.md`, or `tasks.md`. Use the schema's normal proposal template/instructions (`openspec instructions proposal --change "<name>" --json`) but keep it honest about being a stub:
   - **Why**: the real motivation — often "raised in review/planning, deferred to keep scope small," cite where it came from if relevant (a PR, a conversation).
   - **What Changes**: rough shape only, explicitly marked not-designed-yet.
   - **Capabilities**: leave New/Modified empty with a note like "none yet — stub only, no spec-level commitment until this is picked up." Don't invent capability names just to fill the section.
   - **Impact**: "Not assessed yet," plus any genuinely known open questions worth recording now so they aren't re-discovered later.
5. **Validate**: `openspec validate "<name>" --json` — expect `valid: true` with an INFO-level note that `skip_specs` allowed zero deltas. If it fails, the proposal likely still lists a capability under "New/Modified Capabilities" — remove it, or this isn't actually a stub.
6. **Index it** if the project tracks deferred work in one place (e.g. a `FUTURE_WORK.md` alongside the change that spawned the stub) — link to `openspec/changes/<name>/proposal.md`, don't duplicate its content.

## Guardrails

- Never write `specs/`, `design.md`, or `tasks.md` for a stub — that's what makes it lightweight. If you catch yourself wanting to add tasks, the idea has graduated past "stub" — do a real propose instead.
- Don't fill "Capabilities" with placeholder/invented capability names to satisfy the template's shape — leave it genuinely empty with a note.
- A stub change is not runnable/applyable (`apply` still requires `tasks`, which doesn't exist) — that's expected and fine. Don't try to make `openspec status` show "complete" for a stub.
- If asked to create several stubs from a list (e.g. deferred items from a review), create one change per distinct idea — don't bundle unrelated deferred items into a single stub change.
