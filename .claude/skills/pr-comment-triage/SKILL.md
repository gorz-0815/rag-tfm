---
name: pr-comment-triage
description: Work through pending/unresolved PR review comments one at a time — make the change and reply when the ask is clear, reply with a clarifying question when it isn't. Use when the user says things like "work through the comments I added on the PR", "address the review feedback", "go through my PR comments".
license: MIT
---

Work through a pull request's outstanding review comments systematically, one comment at a time. Don't batch-guess across all of them before checking your read on each is right.

## Process

1. **Enumerate the comments.** For GitHub, use `gh api repos/<owner>/<repo>/pulls/<n>/comments` (line/review comments) and, if there's a pending review, `gh api repos/<owner>/<repo>/pulls/<n>/reviews/<review_id>/comments`. Get `id`, `path`, `body`, and enough of `diff_hunk`/`line` context to know what each comment is pointing at.

2. **For each comment, decide: clear or ambiguous.**
   - **Clear**: the requested change and its scope are unambiguous — you know exactly what file(s)/line(s) to change and the change doesn't quietly invalidate other decisions already on record (other specs, other design sections, other comments) without you noticing.
   - **Ambiguous**: the comment asks a direct question, offers multiple plausible interpretations, or its request conflicts with or has unclear downstream impact on other parts of the plan/code.
   - When a comment is clear on its own but its implementation has real downstream implications for other artifacts (e.g. a spec that assumed the opposite), treat that link as part of making the change correctly — update the downstream artifact too — not as a reason to ask, unless the *right* resolution of that downstream conflict is itself ambiguous.

3. **Act per comment:**
   - **Clear → make the change, then reply.** Edit the actual file(s) the comment concerns (and any downstream artifact the change touches). Then post a reply on that comment thread stating what changed (concrete: file, what was added/removed/reworded) — not just "done".
   - **Ambiguous → reply with a question, don't guess.** Post a reply asking the specific clarifying question. Do not edit files for that comment until it's answered.

4. **Look for cross-references between comments.** Reviewers often write follow-up comments referencing earlier ones ("as mentioned above", "same as the other one"). Read all comments before acting on any one, so a later comment can inform how you resolve an earlier one (or vice versa) instead of treating each in isolation.

5. **Use the platform's reply mechanism**, not a new top-level comment:
   - GitHub line comments: `gh api repos/<owner>/<repo>/pulls/<n>/comments -f body='<reply>' -F in_reply_to=<comment_id> -X POST` (replies into the same thread).
   - If the review is still pending (unsubmitted, only visible to its author), replies work the same way against comment IDs; don't submit/publish the review unless asked.
   - **Prefix every reply body with `Claude: `.** Replies post under the user's own account/token (`gh` uses their auth), so without a marker a Claude-authored reply is visually indistinguishable from the human reviewer's own comments in the thread. The prefix is what makes it possible to tell them apart later.

6. **Summarize when done.** Short list: which comments got a code change (+ what changed), which got a question (+ what was asked), any comment intentionally left untouched and why. Note which addressed threads are ready to be marked resolved — but don't resolve them yourself; that's the user's call. A reply does *not* automatically mark a GitHub thread resolved (that's a separate GitHub action), so an addressed thread stays open until the user closes it, and that's expected, not a bug.

## Guardrails

- Never resolve ambiguity by picking the interpretation that's least work — ask.
- Don't let "clear" become "clear enough" — if two readings of a comment would lead to materially different changes, it's ambiguous.
- Preserve existing thread structure: reply in-thread, don't delete/recreate comments unless the user asks.
- If a clear change would remove or contradict something another still-open comment depends on, flag that conflict in your reply rather than silently picking a side.
- **Never resolve a review thread**, even one you fully addressed. Resolving is the user's decision to make, always — report it as done via your reply and let them close it.
