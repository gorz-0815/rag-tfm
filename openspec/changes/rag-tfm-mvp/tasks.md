## 1. Project Scaffold

- [x] 1.1 Create `.gitignore` (`.venv/`, `.env`, `storage/`, `data/manuals/`, `__pycache__/`, `*.db`)
- [x] 1.2 Create `requirements.txt` (llama-index, llama-index-llms-anthropic, llama-index-embeddings-huggingface, llama-index-vector-stores-chroma, chromadb, langfuse, ragas, langchain-anthropic, pypdf, python-dotenv)
- [x] 1.3 Create `.env.example` (ANTHROPIC_API_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST)
- [x] 1.4 Add MIT `LICENSE`
- [x] 1.5 Create `src/` package skeleton (`src/__init__.py`, `src/config.py` for env loading, model names, paths, and configurable chunk_size/chunk_overlap)

## 2. Corpus Directory

- [x] 2.1 Create empty `data/manuals/` with a `.gitkeep` for the user's own manuals (gitignored contents) — no manual files are committed in this change (see the `sample-corpus-sourcing` stub change)

## 3. Manual Ingestion (`manual-ingestion` capability)

- [x] 3.1 Implement `src/ingest.py`: load a PDF via SimpleDirectoryReader/pypdf — originally from a configurable manuals directory (auto-discovered), **revised in PR #7 review to take the manual's path as an explicit CLI argument instead** (`python -m src.ingest <manual.pdf>`); the app only ever indexes one manual at a time, never a directory-wide corpus
- [x] 3.2 Chunk with `SentenceSplitter`, chunk_size/overlap read from `src/config.py`/env (defaults 512/64 per design.md)
- [x] 3.3 Embed chunks with local HF embedding model (`BAAI/bge-small-en-v1.5` or similar) via `llama-index-embeddings-huggingface`
- [x] 3.4 Persist index to Chroma-backed `storage/`, one collection per manual named by a content hash — re-ingesting an unchanged manual reuses its collection (no re-embedding); a different manual gets its own collection alongside it
- [x] 3.5 Ensure chunk metadata retains source manual filename
- [x] 3.6 Handle a missing/non-PDF manual path with a clear error (per spec scenario; revised for the single-file argument, was originally "empty/missing manuals directory")
- [x] 3.7 Verify: run ingestion against a locally-supplied test PDF, confirm `storage/` is created and contains its chunks

## 4. Manual QA CLI (`manual-qa-cli` capability)

- [x] 4.1 Implement `src/query.py` with a single-shot `ask` CLI command: `python -m src.ask "<question>" <manual_path>`
- [x] 4.2 Implement RAG mode: retrieve top-k chunks from the persisted index, build prompt, call Claude, print answer
- [x] 4.3 Implement citation output: list source manual(s) alongside the RAG-mode answer
- [x] 4.4 Implement no-context mode flag (`--no-context`, renamed from `--no-rag` per review): send only the question to Claude, no retrieval, no citations
- [x] 4.5 Handle no-relevant-content case: if retrieval returns nothing usable, say so rather than fabricating an answer
- [x] 4.6 Verify: ask a manual-specific question in RAG mode (grounded, cited answer) and the same question in no-context mode (baseline, uncited) — verified 2026-08-20 against `data/manuals/aquaflow-200-manual.pdf`: RAG mode answered "soak in cold water for 15 minutes" with `Sources: aquaflow-200-manual.pdf`; no-context mode gave a generic, product-agnostic, uncited answer that contradicted the manual
- [x] 4.7 Implement full-document mode flag (`--full-doc`, using the same `manual_path` argument as RAG mode): send the named manual's full extracted text as context, no retrieval/chunking, cite that manual
- [x] 4.8 Verify: ask a manual-specific question in full-doc mode and confirm it returns a grounded answer citing the named manual — re-verified 2026-08-22 with the current CLI shape: `data/manuals/aquaflow-200-manual.pdf --full-doc` answered "soak in cold water for 15 minutes" with `Sources: aquaflow-200-manual.pdf`

## 5. Query Tracing (`query-tracing` capability)

- [x] 5.1 Wire Langfuse tracing into the query paths — **revised from the original callback-based-handler plan**: `langfuse.llama_index.LlamaIndexCallbackHandler` no longer exists in installed `langfuse` v4 (Langfuse dropped its LlamaIndex-specific integration for third-party OTel instrumentation). Implemented via `src/tracing.py`: `openinference-instrumentation-llama-index`'s `LlamaIndexInstrumentor().instrument()` auto-captures retrieval and LLM calls process-wide; a manual `traced_span` covers full-doc mode's pypdf text extraction, which isn't a LlamaIndex operation. See revised `design.md` tracing-integration note.
- [ ] 5.2 Confirm all three query paths (RAG, full-doc, no-context) produce a trace (chunks/extraction/prompt/latency/tokens where applicable) — code wired and offline-tested (`tests/test_tracing.py`); live confirmation against Langfuse Cloud UI still pending
- [x] 5.3 Add graceful degradation: if Langfuse is unreachable, still return the answer and print a warning instead of failing — `flush_tracing()` catches any flush failure and warns rather than raising; both `flush_tracing`/`traced_span` also no-op cleanly when no Langfuse credentials are configured at all
- [ ] 5.4 Verify: run one query, confirm a matching trace appears in the Langfuse Cloud UI; capture a written walkthrough for `results/sample_trace.md`

## 6. Comparative Eval (`comparative-eval` capability)

- [ ] 6.1 Write `data/eval_qa.json`: ~15-20 hand-written questions against the single manual named at eval time (per the single-manual-by-path model established in PR #7 review — no directory-wide scan), each with a manually-verified ground-truth answer (not committed with real manual content until a corpus decision is made — see the `sample-corpus-sourcing` stub change; the committed synthetic `data/manuals/aquaflow-200-manual.pdf` from PR #7 could serve as that eval target)
- [ ] 6.2 Implement `src/eval.py`: run every eval question through both no-context and RAG conditions using `src/query.py`'s functions
- [ ] 6.3 Build a Ragas `EvaluationDataset` from the results; wrap Claude (`langchain-anthropic` + `LangchainLLMWrapper`) as judge and the local HF embeddings (`LangchainEmbeddingsWrapper`) for context metrics
- [ ] 6.4 Score faithfulness + answer_relevancy for both conditions; context_precision + context_recall for RAG only
- [ ] 6.5 Write `results/eval_results.json` (raw) and `results/eval_results.md` (comparison table + prose interpretation of the gap)
- [ ] 6.6 Verify: `python -m src.eval` completes end-to-end and produces a results table with a visible RAG-vs-no-context gap on manual-specific questions

## 7. README and Publish Prep

- [ ] 7.1 Write README: what/why, setup (single documented path), architecture description
- [ ] 7.2 Write README tracing section referencing `results/sample_trace.md`
- [ ] 7.3 Write README eval section referencing `results/eval_results.md`, interpreted not just raw numbers
- [ ] 7.4 Write README cost/latency/scalability trade-offs section (chunking trade-off, per-query cost estimate, local Chroma scaling ceiling, what production would need instead)
- [ ] 7.5 Write README corpus note: the app works with one manual at a time, named explicitly on the CLI (`python -m src.ingest <manual.pdf>`); a synthetic sample manual is committed at `data/manuals/aquaflow-200-manual.pdf` for out-of-the-box use, or point it at your own PDF
- [ ] 7.6 Note explicitly in README: demo project, not production-ready; future work tracked as separate stub changes under `openspec/changes/` (interactive CLI, pluggable LLM backend, sample-corpus sourcing, and a search-tool eval condition)
- [ ] 7.7 Final secrets check: confirm no `.env`, API keys, `storage/`, or `data/manuals/` private content in `git status` or history before first commit
- [ ] 7.8 `git init`, first commit; add `github` remote (`https://github.com/gorz-0815/rag-tfm.git`) once the empty repo exists on GitHub — do not push without separate confirmation
