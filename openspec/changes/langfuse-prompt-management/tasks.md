## 1. Migration script

- [ ] 1.1 Write `scripts/migrate_prompts_to_langfuse.py`: reads `SYSTEM_PROMPT.md` and `PROMPT_TEMPLATE.md`, creates `rag-tfm-system-prompt` and `rag-tfm-context-template` in Langfuse as `type="text"`, labeled `production`, using the installed Langfuse skill's migration mechanics (fetch current SDK docs, don't implement from memory)
- [ ] 1.2 Run the script once against the project's Langfuse account (credentials already in `.env`) — verify: both prompts appear in the Langfuse UI under Prompts, labeled `production`, with content matching the local `.md` files

## 2. Fetch-with-fallback in `src/prompts.py`

- [ ] 2.1 Add a Langfuse fetch path to `load_system_prompt()`: when `tracing._configured()` is true, try `langfuse.get_client().get_prompt("rag-tfm-system-prompt", label="production")`; on any exception, fall back to reading `SYSTEM_PROMPT.md` as today
- [ ] 2.2 Add the same fetch-with-fallback to `build_context_prompt()` for `rag-tfm-context-template`, using `.compile(context=context, question=question)` on success instead of the current `.replace()` calls
- [ ] 2.3 Verify: with valid Langfuse credentials in `.env`, run a query and confirm (via a temporary print or debugger) the prompt text came from Langfuse, not the local file
- [ ] 2.4 Verify: temporarily point `LANGFUSE_BASE_URL` at an unreachable host, run a query, confirm it still answers using the local `.md` file content and prints no unhandled exception

## 3. Link prompts to generations

- [ ] 3.1 In `src/query.py`'s `_ask_with_context` and `ask_no_context`, call `langfuse.get_client().update_current_generation(prompt=prompt)` immediately before the instrumented `llm.chat()` / `llm.complete()` call, passing the prompt object returned by the Langfuse fetch (skip if tracing isn't configured or the fetch fell back to local files)
- [ ] 3.2 Verify against a real trace in the Langfuse UI: does the generation show a linked prompt name/version? If not, fall back to recording the prompt name/version as `input` on a `traced_span`-wrapped call site instead (per design.md's fallback), and update design.md's Decisions section to reflect which approach actually worked
- [ ] 3.3 Confirm all three query modes (RAG, full-doc, no-context) still produce correct answers and (where applicable) linked-prompt traces

## 4. Cleanup and docs

- [ ] 4.1 Add a short code comment on `SYSTEM_PROMPT.md` / `PROMPT_TEMPLATE.md` (or a repo README note) stating they are now the offline fallback, not the live source of truth — avoid anyone editing them expecting it to change production behavior
- [ ] 4.2 Update `requirements.txt` only if the migration script needs anything beyond the already-installed `langfuse` package (expected: no change)
- [ ] 4.3 Run existing `tests/` suite, confirm nothing broke (prompt-loading tests may need a Langfuse-unconfigured-by-default assumption, matching the project's mocked-by-default test convention)
