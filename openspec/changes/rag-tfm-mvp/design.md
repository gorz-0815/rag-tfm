## Context

First implementation of `rag-tfm`, greenfield — no existing code or specs to integrate with. See `proposal.md` for motivation. Constraints carried from the interview: Anthropic Claude for generation, local (non-API) embeddings, local vector store, Langfuse for tracing, Ragas for eval, no cloud hosting, single-shot CLI only (no session/REPL mode) for this change.

## Goals / Non-Goals

**Goals:**
- A working, fully local (aside from the Anthropic API call) RAG pipeline over PDF manuals
- Every query traced in Langfuse regardless of RAG/no-context mode
- A defensible, interpreted comparative eval (no-context vs RAG) using Ragas

**Non-Goals:**
- Interactive/session CLI (multi-turn, mode-switching) — tracked as the `interactive-cli` stub change
- Diagram/image understanding in manuals — text-only per proposal
- Hosted/managed vector store or production deployment
- A third "search-tool" eval condition — discussed and deferred, not part of this change
- Pluggable/multi-provider LLM backend — tracked as the `pluggable-llm-backend` stub change (default backend for v1 still under discussion, see PR #1)

## Decisions

**LLM: Anthropic Claude via `llama-index-llms-anthropic`.** Matches the interview decision and the Claude Code/Anthropic ecosystem this project is built in. Default to a cheap/fast model (e.g. Haiku) for both generation and CLI responsiveness, configurable to a stronger model via env var. Alternative considered: OpenAI — rejected, no reason to add a second model provider when Anthropic covers both generation and (via `langchain-anthropic`) the Ragas judge role.

**Embeddings: local `sentence-transformers` model (e.g. `BAAI/bge-small-en-v1.5`) via `llama-index-embeddings-huggingface`.** Matches the interview decision ("local embeddings for now"). No embedding API key needed; ingestion and retrieval work fully offline once the model is downloaded once. Trade-off (goes in README cost/latency section): weaker semantic retrieval quality than a hosted embedding API (e.g. Voyage/OpenAI), acceptable for a small, topically narrow manual corpus. Alternative considered: OpenAI embeddings — kept local-only for this change; a configurable OpenAI option is tracked as the `openai-embeddings-option` stub change per review feedback.

**Vector store: Chroma, persisted to a local `storage/` directory.** File-based, zero external setup, matches "local only" constraint from config context. Alternative considered: FAISS — Chroma chosen for its native LlamaIndex integration and built-in metadata filtering (needed for per-chunk source-manual citation).

**Chunking: `SentenceSplitter`, chunk_size and overlap configurable via `src/config.py`/env, defaulting to 512 tokens / 64 overlap.** Manuals mix short numbered steps and longer prose (safety sections, specs tables); 512/64 is a reasonable starting default but not a one-size-fits-all fit, so it's exposed as config rather than hardcoded, per review feedback. Documented as an explicit trade-off in the README rather than tuned exhaustively — larger chunks improve multi-step recall at the cost of retrieval precision and per-query token cost; smaller chunks do the opposite and risk splitting a procedure mid-step.

**Tracing integration: Langfuse's callback-based LlamaIndex handler (`langfuse.llama_index.LlamaIndexCallbackHandler` → `Settings.callback_manager`), not the newer instrumentation-based integration.** As of this design, Langfuse's instrumentation-based LlamaIndex integration is still flagged less stable than the callback-based one; callback-based is simpler to reason about for a demo project and is the documented production-suggested path. Both RAG and no-context query paths route through the same instrumented LLM call so tracing coverage is uniform (per `query-tracing` spec).

**Ragas judge model: `langchain-anthropic`'s `ChatAnthropic`, wrapped via Ragas' `LangchainLLMWrapper`; same local HF embeddings wrapped via `LangchainEmbeddingsWrapper` for context-based metrics.** Reuses the same model family as generation for consistency and avoids adding a third provider just for evaluation.

**Corpus: no manual files are committed in this change.** Reversed from the earlier plan to ship openly-licensed sample manuals — per review feedback, corpus sourcing/licensing needs more thought and is deferred (tracked as the `sample-corpus-sourcing` stub change). Ingestion and eval in this change run against manuals the user supplies locally in the gitignored `data/manuals/`; the repo is not "clone and run" out of the box until a sample corpus decision is made.

**CLI shape (v1): a single `ask` command taking a question as its argument, with mode flags for RAG vs no-context vs full-document.** Matches the interview decision to start simple; the richer interactive CLI is explicitly out of scope for this change (see Non-Goals). Originally shipped as a boolean `--no-rag` flag; PR #7 review added `--full-doc` as a third mode (send the whole manual as context, no retrieval/chunking, as an upper-bound comparison against RAG's chunked context) and renamed `--no-rag` to `--no-context` for clarity against it.

**Corpus scope (revised, PR #7 review): exactly one manual at a time, named explicitly by path — never auto-discovered from a directory.** `src/ingest.py` originally scanned `data/manuals/` for every PDF present (`SimpleDirectoryReader(input_dir=...)`), and `manual-ingestion`/`manual-qa-cli`'s specs described a multi-manual corpus accordingly. Review feedback rejected that as unnecessary complexity for this project's actual shape (one manual, one demo) and asked for the manual's path to be a required CLI argument instead (`python -m src.ingest <manual.pdf>`, `--full-doc <manual.pdf>`) — `SimpleDirectoryReader(input_files=[path])`, no directory walk. Every ingest now replaces the Chroma collection rather than appending, so the index can never mix chunks from more than one manual. This also incidentally resolved an unrelated bug where `exclude_hidden`'s default treated any hidden ancestor path segment (e.g. a Claude Code worktree under `.claude/worktrees/<name>/`) as reason to skip every file — `input_files` doesn't walk the tree, so that check never runs. Downstream effect: the `sample-corpus-sourcing` stub's "small set of manuals" framing predates this pivot and needs reconciling to "one sample manual" whenever it's picked up.

## Risks / Trade-offs

- **[Risk]** Local embedding model quality may cause weak retrieval on some manuals, making the RAG-vs-no-context eval gap look smaller than it should → **Mitigation**: eval questions are written to be answerable from clearly-worded manual sections, keeping retrieval quality less of a confound for a demo-scale corpus.
- **[Risk]** Langfuse Cloud outage/unreachability during a demo → **Mitigation**: `query-tracing` spec requires tracing failure to degrade gracefully (answer still returned, warning surfaced), not block the CLI.
- **[Risk]** No manuals are committed in this change, so the repo isn't runnable out of the box for reviewers → **Mitigation**: explicitly accepted trade-off per review feedback; tracked as the `sample-corpus-sourcing` stub change rather than rushed.
- **[Trade-off]** Local embeddings keep the project dependency-light and free to run, at the cost of retrieval quality versus a hosted embedding API — accepted and documented in the README rather than hidden.

## Open Questions

None blocking implementation. Exact `ask` CLI argument/flag names and the specific sample manual(s) to source are implementation-level details resolved during task execution.

- **Should `comparative-eval` (Section 6, not yet implemented) score `--full-doc` as a third condition, not just RAG vs no-context?** `--full-doc` was added after this section was originally scoped (PR #7 review). `query-tracing`'s spec was updated to cover all three modes since tracing is mode-agnostic by nature, but extending the eval report to a three-way comparison is a bigger call (report format, whether Ragas' context-precision/recall metrics even apply to "whole document as context") that wasn't asked for — left for whoever picks up Section 6 to decide rather than assumed here.
