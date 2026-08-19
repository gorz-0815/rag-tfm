## Purpose

Lets a user ask a natural-language question about the ingested manuals from the command line and get a grounded, cited answer — plus a no-RAG mode for baseline comparison.

## ADDED Requirements

### Requirement: Single-shot question answering command
The system SHALL provide a CLI command that accepts one question as an argument, answers it using the indexed manuals as context, and prints the answer to stdout.

#### Scenario: Question answered from indexed manuals
- **WHEN** the user runs the ask command with a question whose answer exists in an ingested manual
- **THEN** the command prints an answer consistent with that manual's content

#### Scenario: No relevant content in the index
- **WHEN** the user asks a question unrelated to any ingested manual
- **THEN** the command indicates it found no relevant content rather than fabricating an answer with false confidence

### Requirement: Answers cite their source
Every RAG-mode answer SHALL be accompanied by a list of the source manual(s)/chunk(s) it was grounded in.

#### Scenario: Citation shown alongside answer
- **WHEN** the ask command produces an answer in RAG mode
- **THEN** the output includes which manual(s) the retrieved context came from

### Requirement: No-RAG baseline mode
The system SHALL support running the same question through the LLM without any retrieved context, for use as a comparison baseline.

#### Scenario: No-RAG mode produces an answer without retrieval
- **WHEN** the ask command is run with no-RAG mode selected
- **THEN** the command sends only the question (no retrieved manual content) to the LLM and prints its answer, with no citations shown
