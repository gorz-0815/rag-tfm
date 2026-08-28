## 1. Web Search and Ranking

- [ ] 1.1 Add an Anthropic web-search-tool-enabled call in a new `src/find_manual.py`: given a product name, prompt Claude to search the web and return a structured list of candidate manual URLs (`{url, title, confidence, note}`)
- [ ] 1.2 Parse the structured response into candidate objects; handle the case of zero candidates returned
- [ ] 1.3 Verify: run the search step alone (no download/ingest yet) against a real product name, confirm it returns plausible candidate URL(s) with confidence/notes

## 2. Candidate Confirmation UX

- [ ] 2.1 Implement single-best-match confirmation: when exactly one high-confidence candidate is returned, print its URL/title and prompt the user for yes/no
- [ ] 2.2 Implement multi-candidate selection: when multiple plausible candidates are returned, print a numbered list (URL + title + note) and prompt the user to pick one or decline all
- [ ] 2.3 Handle user declining all candidates: exit cleanly with no download, no ingestion
- [ ] 2.4 Verify: run against a product name that yields one clear candidate, and one that yields multiple plausible candidates (e.g. an ambiguous/generic product name); confirm both UX paths behave correctly

## 3. Download and Validation

- [ ] 3.1 Implement PDF download of the confirmed URL to `data/manuals/`, using content-type/magic-byte checks to confirm it's actually a PDF before writing
- [ ] 3.2 Handle a confirmed URL that isn't a real PDF (wrong content-type) with a clear error, no partial/invalid file left behind
- [ ] 3.3 Handle fetch failures (network error, 403/404) with a clear error message
- [ ] 3.4 Verify: confirm a real candidate downloads successfully to `data/manuals/`, and confirm a deliberately-wrong URL (e.g. an HTML page) fails cleanly with the expected error

## 4. Ingestion Hand-off

- [ ] 4.1 Call `src/ingest.py`'s existing ingestion function in-process with the downloaded PDF's path, unchanged from its current single-path contract
- [ ] 4.2 Print the same "ready to query" confirmation ingestion already prints, so the CLI flow reads as one continuous action from product name to queryable manual
- [ ] 4.3 Verify: run `python -m src.find_manual "<product name>"` end to end, confirm the manual is indexed, then immediately ask a question against it with `python -m src.ask` and get a grounded, cited answer

## 5. Tests

- [ ] 5.1 Add `tests/test_find_manual.py` covering the dependency-light logic without real network/API calls: candidate-list parsing (single vs. multiple vs. zero candidates), confirmation-path selection logic, and PDF content-type validation — mock the search/download calls
- [ ] 5.2 Add an opt-in live test (env-var gated, following `tests/test_ask_live.py`'s `RUN_LIVE_LLM_TESTS` pattern) that runs a real search+download+ingest for one known product name, skipped by default

## 6. Docs

- [ ] 6.1 Add a README section describing `python -m src.find_manual` alongside the existing `ingest`/`ask` usage, and note it as a discovery convenience layered on top of ingestion (not a replacement for pointing the CLI at a manual you already have)
