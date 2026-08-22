"""Answer questions about a single ingested manual via Claude, in one of three
modes: RAG (retrieved chunks), full-doc (the entire manual, no retrieval), or
no-context (bare question, no manual content at all - baseline).

Heavy third-party imports are kept inside the functions that need them, not
at module level, so this module stays importable without the full stack.
"""

from src import config, tracing, vector_store
from src.prompts import NO_CONTEXT_MESSAGE, build_context_prompt, load_system_prompt

# Number of top-ranked chunks retrieved per question and passed to the LLM
# as context in RAG mode (see ask_rag's similarity_top_k usage below).
SIMILARITY_TOP_K = 4


def load_manuals_index(manual_path):
    """Open the Chroma collection built by `src.ingest` for this manual.

    Raises if that manual hasn't been ingested yet.
    """
    from llama_index.core import VectorStoreIndex

    with tracing.traced_span("load_embedding_model"):
        vector_store.configure_embed_model()
    store = vector_store.get_existing_collection(manual_path)
    if store is None:
        raise SystemExit(
            f"No index found for {manual_path}. Run `python -m src.ingest {manual_path}` first."
        )
    return VectorStoreIndex.from_vector_store(store)


def _build_llm():
    from llama_index.llms.anthropic import Anthropic

    return Anthropic(model=config.ANTHROPIC_MODEL, api_key=config.ANTHROPIC_API_KEY)


def _ask_with_context(user_prompt: str) -> str:
    """Send SYSTEM_PROMPT.md as the system message and user_prompt as the
    user turn. Used by ask_rag and ask_full_doc, not ask_no_context.
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


def ask_rag(question: str, manual_path) -> dict:
    index = load_manuals_index(manual_path)
    nodes = index.as_retriever(similarity_top_k=SIMILARITY_TOP_K).retrieve(question)

    if not nodes:
        return {"answer": NO_CONTEXT_MESSAGE, "sources": []}

    # Chunks are joined in retrieval-rank order, not document order - an
    # answer split across non-adjacent chunks may read as disjoint fragments.
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

    with tracing.traced_span("extract_manual_text", manual_path=str(manual_path)) as span:
        context = _load_manual_text(manual_path)
        if span is not None:
            # The full text is already visible in Anthropic.chat's prompt input
            # (build_context_prompt embeds it) - a preview here is enough to
            # confirm extraction worked without duplicating the whole manual.
            span.update(output={"char_count": len(context), "preview": context[:200]})
    user_prompt = build_context_prompt(question, context)

    answer = _ask_with_context(user_prompt)

    return {"answer": answer, "sources": [manual_path.name]}


def ask_no_context(question: str) -> dict:
    llm = _build_llm()
    response = llm.complete(question)
    return {"answer": str(response), "sources": []}
