## Purpose

Lets a user ask a natural-language question about the ingested manuals from the command line and get a grounded, cited answer — plus a full-document mode and a no-context mode for baseline comparison.

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

### Requirement: No-context baseline mode
The system SHALL support running the same question through the LLM without any manual content at all, for use as an un-grounded comparison baseline.

#### Scenario: No-context mode produces an answer without any manual content
- **WHEN** the ask command is run with no-context mode selected (`--no-context`)
- **THEN** the command sends only the question — no retrieved chunks, no full manual text — to the LLM and prints its answer, with no citations shown

### Requirement: Full-document baseline mode
The system SHALL support sending the complete text of every ingested manual as context, bypassing retrieval entirely, for use as an upper-bound comparison against RAG mode's chunk-based context.

#### Scenario: Full-document mode produces an answer without retrieval
- **WHEN** the ask command is run with full-document mode selected (`--full-doc`)
- **THEN** the command extracts and sends the full text of every manual in the manuals directory as context (no chunking, no vector search) and prints the answer with every manual listed as a source

#### Scenario: Full-document mode with no manuals present
- **WHEN** full-document mode is selected and no manuals exist in the manuals directory
- **THEN** the command indicates it found no relevant content rather than sending an empty context to the LLM
