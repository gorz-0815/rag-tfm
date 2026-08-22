## Purpose

Proves, with numbers rather than assertion, that retrieval-augmented answers are more faithful and relevant than an unaided LLM baseline on manual-specific questions — the differentiator that turns this into an evaluation-competence demo, not just a pipeline demo.

## ADDED Requirements

### Requirement: Hand-written evaluation question set
The system SHALL support a set of approximately 15-20 questions about the ingested manual, each with a human-verified ground-truth answer.

#### Scenario: Eval set is loadable and complete
- **WHEN** the evaluation command runs
- **THEN** it loads every question in the eval set and each has an associated ground-truth answer

### Requirement: Evaluation runs both conditions
The evaluation command SHALL run every question in the eval set through both the no-context baseline and the RAG pipeline.

#### Scenario: Both conditions produce answers for every question
- **WHEN** the evaluation command completes
- **THEN** there is a recorded answer for every eval question under both the no-context condition and the RAG condition

### Requirement: Ragas scoring per condition
The system SHALL score both conditions' answers using Ragas metrics: faithfulness and answer relevancy for both conditions, and context precision and context recall for the RAG condition only.

#### Scenario: Metrics computed for both conditions
- **WHEN** the evaluation command finishes scoring
- **THEN** faithfulness and answer relevancy scores exist for both the no-context and RAG conditions, and context precision/recall scores exist for the RAG condition

### Requirement: Interpreted comparison report
The evaluation command SHALL produce a written report comparing the two conditions, including both the raw metric numbers and a prose interpretation of what the comparison shows.

#### Scenario: Report includes interpretation, not just numbers
- **WHEN** the evaluation report is generated
- **THEN** it contains a metrics comparison table and an accompanying written explanation of what the gap (or lack of gap) between conditions demonstrates
