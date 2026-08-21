## Purpose

Turns a single text-based PDF technical manual, named explicitly by the caller, into a queryable local vector index, so the QA CLI has grounded content to retrieve from.

## ADDED Requirements

### Requirement: Ingest a single named PDF manual into a local vector index
The system SHALL take the path to one PDF manual as an explicit argument (never auto-discovered from a directory), split it into chunks, embed each chunk with a local (non-API) embedding model, and persist the result as a local vector index that can be reused across CLI invocations without re-ingesting.

#### Scenario: Successful ingestion of a named manual
- **WHEN** the ingestion command is run with the path to a PDF manual
- **THEN** a persisted local vector index is created on disk containing that manual's chunks, and the command exits successfully

#### Scenario: Re-running ingestion with a different manual
- **WHEN** ingestion is re-run with a different manual's path than the one currently indexed
- **THEN** the persisted index is replaced with the new manual's chunks — the previous manual's chunks are not retained alongside it

#### Scenario: Ingestion path does not point to a PDF
- **WHEN** the given path does not exist or is not a PDF file
- **THEN** the command fails with a clear error message rather than silently producing an empty or invalid index

### Requirement: Retain source attribution per chunk
Each indexed chunk SHALL retain metadata identifying its source manual (filename) so that answers can cite which manual they came from.

#### Scenario: Chunk metadata includes source manual
- **WHEN** a chunk is retrieved from the index
- **THEN** its metadata includes the filename of the manual it was extracted from
