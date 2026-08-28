## Purpose

Lets a user locate and retrieve a product's manual from the web by product name alone, so they can go straight into ingestion without already having a PDF on disk.

## ADDED Requirements

### Requirement: Search the web for a product's manual
The system SHALL accept a product name as input and search the web for candidate manual/documentation documents for that product.

#### Scenario: Search finds candidates
- **WHEN** the user runs the discovery command with a product name
- **THEN** the system retrieves a set of candidate web results relevant to that product's manual

#### Scenario: No candidates found
- **WHEN** the web search returns no results plausibly related to the named product
- **THEN** the command reports that no manual could be found rather than downloading an unrelated document

### Requirement: Rank candidates by likely correctness
The system SHALL use an LLM to evaluate each candidate result and rank it by how likely it is to be the correct, official manual for the named product, distinguishing it from wrong-product matches, non-manual pages (forums, retailer listings, reviews), and non-PDF content.

#### Scenario: Single clear best match
- **WHEN** exactly one candidate is clearly the correct official manual
- **THEN** the system identifies it as the top-ranked candidate for confirmation

#### Scenario: Multiple plausible candidates
- **WHEN** more than one candidate is plausibly the correct manual (e.g. different revisions, regional variants)
- **THEN** the system retains the plausible candidates for the user to choose among, rather than silently picking one

### Requirement: User confirms the manual before download
The system SHALL show the user the candidate manual's identifying information (at minimum its source URL) and require explicit confirmation before downloading anything.

#### Scenario: Single best match presented for confirmation
- **WHEN** the system has one top-ranked candidate
- **THEN** it shows that candidate's URL to the user and proceeds only after the user confirms it is correct

#### Scenario: Multiple candidates presented as a choice
- **WHEN** the system retains multiple plausible candidates
- **THEN** it shows the user a numbered list of candidates (with URLs) and proceeds only with the one the user selects

#### Scenario: User rejects all candidates
- **WHEN** the user declines the single candidate or selects none from the list
- **THEN** the command exits without downloading anything

### Requirement: Download the confirmed manual for ingestion
The system SHALL download the user-confirmed manual as a PDF to a local path and hand that path to the existing manual-ingestion flow, without altering that flow's single-file-path contract.

#### Scenario: Confirmed manual is downloaded and ingested
- **WHEN** the user confirms a candidate manual
- **THEN** the system downloads it to a local PDF file and passes that file's path into ingestion, resulting in an indexed manual

#### Scenario: Confirmed candidate is not a downloadable PDF
- **WHEN** the confirmed candidate's URL does not resolve to a PDF document
- **THEN** the command fails with a clear error rather than passing invalid content into ingestion
