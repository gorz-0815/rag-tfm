## 1. Project Scaffold

- [x] 1.1 Create `.gitignore` (`.venv/`, `.env`, `storage/`, `data/manuals/`, `__pycache__/`, `*.db`)
- [x] 1.2 Create `requirements.txt` (llama-index, llama-index-llms-anthropic, llama-index-embeddings-huggingface, llama-index-vector-stores-chroma, chromadb, langfuse, ragas, langchain-anthropic, pypdf, python-dotenv)
- [x] 1.3 Create `.env.example` (ANTHROPIC_API_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST)
- [x] 1.4 Add MIT `LICENSE`
- [x] 1.5 Create `src/` package skeleton (`src/__init__.py`, `src/config.py` for env loading, model names, paths, and configurable chunk_size/chunk_overlap)

## 2. Corpus Directory

- [ ] 2.1 Create empty `data/manuals/` with a `.gitkeep` for the user's own manuals (gitignored contents) — no manual files are committed in this change (see the `sample-corpus-sourcing` stub change)

## 3. Manual Ingestion (`manual-ingestion` capability)

- [ ] 3.1 Implement `src/ingest.py`: load PDFs via SimpleDirectoryReader/pypdf from a configurable manuals directory
- [ ] 3.2 Chunk with `SentenceSplitter`, chunk_size/overlap read from `src/config.py`/env (defaults 512/64 per design.md)
- [ ] 3.3 Embed chunks with local HF embedding model (`BAAI/bge-small-en-v1.5` or similar) via `llama-index-embeddings-huggingface`
- [ ] 3.4 Persist index to Chroma-backed `storage/`, rebuildable by re-running ingestion
- [ ] 3.5 Ensure chunk metadata retains source manual filename
- [ ] 3.6 Handle empty/missing manuals directory with a clear error (per spec scenario)
- [ ] 3.7 Verify: run ingestion against a locally-supplied test PDF in `data/manuals/` (not committed), confirm `storage/` is created and contains its chunks

## 4. Manual QA CLI (`manual-qa-cli` capability)

- [ ] 4.1 Implement `src/query.py` with a single-shot `ask` CLI command: `python -m src.ask "<question>"`
- [ ] 4.2 Implement RAG mode: retrieve top-k chunks from the persisted index, build prompt, call Claude, print answer
- [ ] 4.3 Implement citation output: list source manual(s) alongside the RAG-mode answer
- [ ] 4.4 Implement no-RAG mode flag: send only the question to Claude, no retrieval, no citations
- [ ] 4.5 Handle no-relevant-content case: if retrieval returns nothing usable, say so rather than fabricating an answer
- [ ] 4.6 Verify: ask a manual-specific question in RAG mode (grounded, cited answer) and the same question in no-RAG mode (baseline, uncited)

## 5. Query Tracing (`query-tracing` capability)

- [ ] 5.1 Wire Langfuse's callback-based LlamaIndex handler into `Settings.callback_manager` (per design.md decision)
- [ ] 5.2 Confirm both RAG and no-RAG query paths produce a trace (chunks/prompt/latency/tokens where applicable)
- [ ] 5.3 Add graceful degradation: if Langfuse is unreachable, still return the answer and print a warning instead of failing
- [ ] 5.4 Verify: run one query, confirm a matching trace appears in the Langfuse Cloud UI; capture a written walkthrough for `results/sample_trace.md`

## 6. Comparative Eval (`comparative-eval` capability)

- [ ] 6.1 Write `data/eval_qa.json`: ~15-20 hand-written questions against the manuals present in `data/manuals/` at the time, each with a manually-verified ground-truth answer (not committed with real manual content until a corpus decision is made — see the `sample-corpus-sourcing` stub change)
- [ ] 6.2 Implement `src/eval.py`: run every eval question through both no-RAG and RAG conditions using `src/query.py`'s functions
- [ ] 6.3 Build a Ragas `EvaluationDataset` from the results; wrap Claude (`langchain-anthropic` + `LangchainLLMWrapper`) as judge and the local HF embeddings (`LangchainEmbeddingsWrapper`) for context metrics
- [ ] 6.4 Score faithfulness + answer_relevancy for both conditions; context_precision + context_recall for RAG only
- [ ] 6.5 Write `results/eval_results.json` (raw) and `results/eval_results.md` (comparison table + prose interpretation of the gap)
- [ ] 6.6 Verify: `python -m src.eval` completes end-to-end and produces a results table with a visible RAG-vs-no-RAG gap on manual-specific questions

## 7. README and Publish Prep

- [ ] 7.1 Write README: what/why, setup (single documented path), architecture description
- [ ] 7.2 Write README tracing section referencing `results/sample_trace.md`
- [ ] 7.3 Write README eval section referencing `results/eval_results.md`, interpreted not just raw numbers
- [ ] 7.4 Write README cost/latency/scalability trade-offs section (chunking trade-off, per-query cost estimate, local Chroma scaling ceiling, what production would need instead)
- [ ] 7.5 Write README corpus note: no manuals are committed in this repo, how to add your own to `data/manuals/` to run ingestion/eval locally
- [ ] 7.6 Note explicitly in README: demo project, not production-ready; future work tracked as separate stub changes under `openspec/changes/` (interactive CLI, pluggable LLM backend, sample-corpus sourcing, and a search-tool eval condition)
- [ ] 7.7 Final secrets check: confirm no `.env`, API keys, `storage/`, or `data/manuals/` private content in `git status` or history before first commit
- [ ] 7.8 `git init`, first commit; add `github` remote (`https://github.com/gorz-0815/rag-tfm.git`) once the empty repo exists on GitHub — do not push without separate confirmation
