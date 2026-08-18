## Context

First implementation of `rag-tfm`, greenfield — no existing code or specs to integrate with. See `proposal.md` for motivation. Constraints carried from the interview: Anthropic Claude for generation, local (non-API) embeddings, local vector store, Langfuse for tracing, Ragas for eval, no cloud hosting, single-shot CLI only (no session/REPL mode) for this change.

## Goals / Non-Goals

**Goals:**
- A working, fully local (aside from the Anthropic API call) RAG pipeline over PDF manuals
- Every query traced in Langfuse regardless of RAG/no-RAG mode
- A defensible, interpreted comparative eval (no-RAG vs RAG) using Ragas

**Non-Goals:**
- Interactive/session CLI (multi-turn, mode-switching) — future change
- Diagram/image understanding in manuals — text-only per proposal
- Hosted/managed vector store or production deployment
- A third "search-tool" eval condition — discussed and deferred, not part of this change

## Decisions

**LLM: Anthropic Claude via `llama-index-llms-anthropic`.** Matches the interview decision and the Claude Code/Anthropic ecosystem this project is built in. Default to a cheap/fast model (e.g. Haiku) for both generation and CLI responsiveness, configurable to a stronger model via env var. Alternative considered: OpenAI — rejected, no reason to add a second model provider when Anthropic covers both generation and (via `langchain-anthropic`) the Ragas judge role.

**Embeddings: local `sentence-transformers` model (e.g. `BAAI/bge-small-en-v1.5`) via `llama-index-embeddings-huggingface`.** Matches the interview decision ("local embeddings for now"). No embedding API key needed; ingestion and retrieval work fully offline once the model is downloaded once. Trade-off (goes in README cost/latency section): weaker semantic retrieval quality than a hosted embedding API (e.g. Voyage/OpenAI), acceptable for a small, topically narrow manual corpus. Alternative considered: OpenAI embeddings — rejected to avoid a second API key/dependency for a demo-scale corpus.

**Vector store: Chroma, persisted to a local `storage/` directory.** File-based, zero external setup, matches "local only" constraint from config context. Alternative considered: FAISS — Chroma chosen for its native LlamaIndex integration and built-in metadata filtering (needed for per-chunk source-manual citation).

**Chunking: `SentenceSplitter`, chunk_size ~512 tokens, overlap ~64.** Manuals mix short numbered steps and longer prose (safety sections, specs tables); 512 tokens keeps most procedures intact while staying small enough for precise retrieval. Documented as an explicit trade-off in the README rather than tuned exhaustively — larger chunks improve multi-step recall at the cost of retrieval precision and per-query token cost; smaller chunks do the opposite and risk splitting a procedure mid-step.

**Tracing integration: Langfuse's callback-based LlamaIndex handler (`langfuse.llama_index.LlamaIndexCallbackHandler` → `Settings.callback_manager`), not the newer instrumentation-based integration.** As of this design, Langfuse's instrumentation-based LlamaIndex integration is still flagged less stable than the callback-based one; callback-based is simpler to reason about for a demo project and is the documented production-suggested path. Both RAG and no-RAG query paths route through the same instrumented LLM call so tracing coverage is uniform (per `query-tracing` spec).

**Ragas judge model: `langchain-anthropic`'s `ChatAnthropic`, wrapped via Ragas' `LangchainLLMWrapper`; same local HF embeddings wrapped via `LangchainEmbeddingsWrapper` for context-based metrics.** Reuses the same model family as generation for consistency and avoids adding a third provider just for evaluation.

**Corpus: sample manuals committed under an openly-licensed source; user's own manuals kept in a gitignored directory.** Per interview decision. Concrete license verification (source, license text, attribution) happens during implementation, before any file is committed — this is a task-level checklist item (see `tasks.md`), not a design decision to pre-resolve here.

**CLI shape (v1): a single `ask` command taking a question as its argument, with a mode flag for RAG vs no-RAG.** Matches the interview decision to start simple; the richer interactive CLI is explicitly out of scope for this change (see Non-Goals).

## Risks / Trade-offs

- **[Risk]** Local embedding model quality may cause weak retrieval on some manuals, making the RAG-vs-no-RAG eval gap look smaller than it should → **Mitigation**: eval questions are written to be answerable from clearly-worded manual sections, keeping retrieval quality less of a confound for a demo-scale corpus.
- **[Risk]** Langfuse Cloud outage/unreachability during a demo → **Mitigation**: `query-tracing` spec requires tracing failure to degrade gracefully (answer still returned, warning surfaced), not block the CLI.
- **[Risk]** Committing a "openly-licensed" manual that turns out to have licensing restrictions not initially noticed → **Mitigation**: explicit per-file license verification task before commit (see `tasks.md`), not left implicit.
- **[Trade-off]** Local embeddings keep the project dependency-light and free to run, at the cost of retrieval quality versus a hosted embedding API — accepted and documented in the README rather than hidden.

## Open Questions

None blocking implementation. Exact `ask` CLI argument/flag names and the specific sample manuals to source are implementation-level details resolved during task execution.
