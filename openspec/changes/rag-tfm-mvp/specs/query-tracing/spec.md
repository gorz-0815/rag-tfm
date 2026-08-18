## Purpose

Makes every question-answering run inspectable after the fact — what was retrieved, what was sent to the LLM, how long each step took, and what it cost — so the project demonstrates real LLMOps tracing practice, not just a working pipeline.

## ADDED Requirements

### Requirement: Every query is traced end-to-end
Every invocation of the ask command, in both RAG and no-RAG modes, SHALL produce a trace recorded to Langfuse covering the full lifecycle of that query.

#### Scenario: RAG query produces a complete trace
- **WHEN** the ask command answers a question in RAG mode
- **THEN** a Langfuse trace is created containing the retrieved chunks, the exact prompt sent to the LLM, the LLM's response, per-step latency, and token usage

#### Scenario: No-RAG query is also traced
- **WHEN** the ask command answers a question in no-RAG mode
- **THEN** a Langfuse trace is created containing the prompt sent, the LLM's response, latency, and token usage (with no retrieval step present)

### Requirement: Tracing failure does not block answering
If the tracing backend is unreachable, the system SHALL still return an answer to the user rather than failing the entire query.

#### Scenario: Langfuse unreachable
- **WHEN** the Langfuse service cannot be reached during a query
- **THEN** the ask command still prints an answer to the user, and surfaces a warning that tracing was not recorded
