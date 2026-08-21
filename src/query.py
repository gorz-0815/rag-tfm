"""Answer questions about a single ingested manual via Claude, in one of three
modes: RAG (retrieved chunks), full-doc (the entire manual, no retrieval), or
no-context (bare question, no manual content at all - baseline).

Heavy third-party imports (llama_index, chromadb) are kept inside the
functions that need them, not at module level, so this module - and the
mocked tests in tests/test_query.py - can be imported without the full
embeddings/vector-store stack installed. See CLAUDE.md #7.
"""

from src import config
from src.prompts import NO_CONTEXT_MESSAGE, build_context_prompt, load_system_prompt

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


def _ask_with_context(user_prompt: str) -> str:
    """Send a real Anthropic `system` message (SYSTEM_PROMPT.md) plus the
    context+question user turn (PROMPT_TEMPLATE.md), via llm.chat() - not
    llm.complete(), which never applies a system message at all. Shared by
    ask_rag and ask_full_doc; ask_no_context deliberately doesn't use this,
    since sending "answer using only the context below" makes no sense when
    there's no context.
    """
    from llama_index.core.llms import ChatMessage, MessageRole

    llm = _build_llm()
    response = llm.chat(
        [
            ChatMessage(role=MessageRole.SYSTEM, content=load_system_prompt()),
            ChatMessage(role=MessageRole.USER, content=user_prompt),
        ]
    )
    return response.message.content


def _load_manual_text(manual_path) -> str:
    """Extract raw text from a single manual PDF, for full-doc mode.

    Deliberately independent of the Chroma index/embedding pipeline - this
    reads the PDF directly with pypdf, no chunking or vector search involved.
    """
    import pypdf

    reader = pypdf.PdfReader(manual_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


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
    user_prompt = build_context_prompt(question, context)

    answer = _ask_with_context(user_prompt)

    sources = sorted({node.metadata.get("file_name", "unknown") for node in nodes})
    return {"answer": answer, "sources": sources}


def ask_full_doc(question: str, manual_path) -> dict:
    from pathlib import Path

    manual_path = Path(manual_path)
    if not manual_path.exists():
        return {"answer": NO_CONTEXT_MESSAGE, "sources": []}

    # No retrieval, no chunking - the manual's entire text goes into context.
    # Larger and costlier per call than RAG mode's top-k chunks, but nothing
    # gets split across a chunk boundary or dropped for not matching the
    # query closely enough.
    context = _load_manual_text(manual_path)
    user_prompt = build_context_prompt(question, context)

    answer = _ask_with_context(user_prompt)

    return {"answer": answer, "sources": [manual_path.name]}


def ask_no_context(question: str) -> dict:
    llm = _build_llm()
    response = llm.complete(question)
    return {"answer": str(response), "sources": []}
