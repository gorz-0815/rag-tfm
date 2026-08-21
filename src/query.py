"""Answer questions about ingested manuals via Claude, in one of three modes:
RAG (retrieved chunks), full-doc (the entire manual(s), no retrieval), or
no-context (bare question, no manual content at all - baseline).

Heavy third-party imports (llama_index, chromadb) are kept inside the
functions that need them, not at module level, so this module - and the
mocked tests in tests/test_query.py - can be imported without the full
embeddings/vector-store stack installed. See CLAUDE.md #7.
"""

from src import config
from src.prompts import NO_CONTEXT_MESSAGE, build_context_prompt

# Number of top-ranked chunks retrieved per question and passed to the LLM
# as context in RAG mode (see ask_rag's similarity_top_k usage below).
SIMILARITY_TOP_K = 4


def load_manuals_index():
    """Open the Chroma index built by `src.ingest`.

    Reads the existing persisted collection at config.STORAGE_DIR; does not
    create or populate it. Run `python -m src.ingest` first, or this raises
    when the "manuals" collection doesn't exist yet.
    """
    import chromadb
    from llama_index.core import Settings, VectorStoreIndex
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.vector_stores.chroma import ChromaVectorStore

    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBEDDING_MODEL)
    chroma_client = chromadb.PersistentClient(path=str(config.STORAGE_DIR))
    chroma_collection = chroma_client.get_collection("manuals")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    return VectorStoreIndex.from_vector_store(vector_store)


def _build_llm():
    from llama_index.llms.anthropic import Anthropic

    return Anthropic(model=config.ANTHROPIC_MODEL, api_key=config.ANTHROPIC_API_KEY)


def _load_manual_texts() -> list[tuple[str, str]]:
    """Extract raw text from every manual PDF, for full-doc mode.

    Deliberately independent of the Chroma index/embedding pipeline - this
    reads PDFs directly with pypdf, no chunking or vector search involved.
    Returns a list of (file_name, full_text) pairs, sorted by filename.
    """
    import pypdf

    manuals = []
    for path in sorted(config.MANUALS_DIR.glob("*.pdf")):
        reader = pypdf.PdfReader(path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        manuals.append((path.name, text))
    return manuals


def ask_rag(question: str) -> dict:
    index = load_manuals_index()
    nodes = index.as_retriever(similarity_top_k=SIMILARITY_TOP_K).retrieve(question)

    if not nodes:
        return {"answer": NO_CONTEXT_MESSAGE, "sources": []}

    # Only the top SIMILARITY_TOP_K retrieved chunks go into context, not the whole
    # manual - smaller than no-RAG's implicit "whatever Claude already knows",
    # but also smaller than the source document. Chunks are joined in
    # retrieval-rank (relevance) order, not their original position in the
    # manual, and each is a fixed-size window (see config.CHUNK_SIZE/
    # CHUNK_OVERLAP) - so if an answer spans two non-adjacent chunks, or a
    # procedure gets split across a chunk boundary, the model only sees the
    # disjoint fragments and has to reason across that gap itself.
    context = "\n\n".join(node.get_content() for node in nodes)
    prompt = build_context_prompt(question, context)

    llm = _build_llm()
    response = llm.complete(prompt)

    sources = sorted({node.metadata.get("file_name", "unknown") for node in nodes})
    return {"answer": str(response), "sources": sources}


def ask_full_doc(question: str) -> dict:
    manuals = _load_manual_texts()

    if not manuals:
        return {"answer": NO_CONTEXT_MESSAGE, "sources": []}

    # No retrieval, no chunking - every manual's full text goes into context,
    # in filename order. Larger and costlier per call than RAG mode's top-k
    # chunks, but nothing gets split across a chunk boundary or dropped for
    # not matching the query closely enough.
    context = "\n\n".join(text for _, text in manuals)
    prompt = build_context_prompt(question, context)

    llm = _build_llm()
    response = llm.complete(prompt)

    sources = [name for name, _ in manuals]
    return {"answer": str(response), "sources": sources}


def ask_no_context(question: str) -> dict:
    llm = _build_llm()
    response = llm.complete(question)
    return {"answer": str(response), "sources": []}
