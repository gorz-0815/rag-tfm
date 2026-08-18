## Purpose

Turns a directory of text-based PDF technical manuals into a queryable local vector index, so the QA CLI has grounded content to retrieve from.

## ADDED Requirements

### Requirement: Ingest PDF manuals into a local vector index
The system SHALL load all PDF files from a configured manuals directory, split them into chunks, embed each chunk with a local (non-API) embedding model, and persist the result as a local vector index that can be reused across CLI invocations without re-ingesting.

#### Scenario: Successful ingestion of sample manuals
- **WHEN** the ingestion command is run against the committed sample manuals directory
- **THEN** a persisted local vector index is created on disk containing chunks from every PDF in that directory, and the command exits successfully

#### Scenario: Re-running ingestion after adding a manual
- **WHEN** a new PDF is added to the manuals directory and ingestion is re-run
- **THEN** the persisted index is rebuilt (or updated) to include chunks from the new manual, without requiring manual deletion of old index files

#### Scenario: Ingestion source directory is empty or missing
- **WHEN** the configured manuals directory contains no PDF files
- **THEN** the command fails with a clear error message rather than silently producing an empty or invalid index

### Requirement: Retain source attribution per chunk
Each indexed chunk SHALL retain metadata identifying its source manual (filename) so that answers can cite which manual they came from.

#### Scenario: Chunk metadata includes source manual
- **WHEN** a chunk is retrieved from the index
- **THEN** its metadata includes the filename of the manual it was extracted from
