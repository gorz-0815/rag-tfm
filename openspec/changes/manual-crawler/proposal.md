## Why

Today, getting a manual into the RAG pipeline requires the user to already have a PDF on disk and pass its path to `src/ingest.py`. Most of the time the user only knows the product's name, not where its manual lives online. A crawler that takes a product name, finds the manual on the web, confirms it with the user, and ingests it directly removes that manual sourcing step and makes the whole "ask questions about product X" flow start from just a name.

## What Changes

- New CLI entry point (e.g. `python -m src.find_manual "<product name>"`) that:
  - Runs a web search for the product's official manual/documentation.
  - Uses an LLM to rank candidate results by how likely each is to be the correct, official manual for the named product (as opposed to a wrong product, a forum post, a retailer listing, etc.).
  - Presents the result(s) to the user before downloading anything: a single best match shown with its URL for a yes/no confirmation, or a short numbered list to pick from when multiple candidates are plausibly correct.
  - Downloads the user-confirmed PDF to a local path and hands that path to the existing `src/ingest.py` ingestion flow unchanged — this proposal adds a discovery step in front of ingestion, it does not change ingestion's contract (still one explicit PDF path in, per `manual-ingestion`'s existing requirement).
- New capability `manual-discovery` covering the search → rank → confirm → download flow, independent of `manual-ingestion` (which continues to own "given a PDF path, index it").
- Out of scope for this proposal: a web app UI (CLI only, consistent with the rest of the project today), non-PDF manual formats, and any change to `manual-ingestion`'s single-file-path contract.

## Capabilities

### New Capabilities
- `manual-discovery`: given a product name, search the web, rank candidates with an LLM, get user confirmation on the correct manual, and download it to a local path ready for ingestion.

### Modified Capabilities
(none — `manual-ingestion`'s contract is unchanged; `manual-discovery` calls into it but does not alter its requirements)

## Impact

- New module (e.g. `src/find_manual.py`) plus a web search dependency (a search API/tool) and an HTTP fetch for the PDF download.
- Downloaded PDFs land in the same gitignored manuals location `src/ingest.py` already reads from; no change to what gets committed.
- Relies on an LLM call to rank/verify candidates — reuses the same Claude client/config already used for query answering (`src/config.py`).
- Distinct from the `sample-corpus-sourcing` stub, which is about committing one static, openly-licensed demo manual to the repo for out-of-the-box reproducibility. This change is a runtime feature for locating *any* manual, not a corpus decision — the two should stay separate; `sample-corpus-sourcing` may want to note this change as a related alternative once it's implemented, but should not be merged into it.
- Independent of PR #12 (`feat/langfuse-prompt-management-rebased`), which is in-flight on top of the archived `rag-tfm-mvp` change; this proposal does not depend on it landing first.
