"""Answer questions about ingested manuals via Claude, in RAG or no-RAG mode."""

import chromadb
from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.anthropic import Anthropic
from llama_index.vector_stores.chroma import ChromaVectorStore

from src import config
from src.prompts import NO_CONTEXT_MESSAGE, build_context_prompt

TOP_K = 4


def load_index() -> VectorStoreIndex:
    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBEDDING_MODEL)
    chroma_client = chromadb.PersistentClient(path=str(config.STORAGE_DIR))
    chroma_collection = chroma_client.get_collection("manuals")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    return VectorStoreIndex.from_vector_store(vector_store)


def ask_rag(question: str) -> dict:
    index = load_index()
    nodes = index.as_retriever(similarity_top_k=TOP_K).retrieve(question)

    if not nodes:
        return {"answer": NO_CONTEXT_MESSAGE, "sources": []}

    context = "\n\n".join(node.get_content() for node in nodes)
    prompt = build_context_prompt(question, context)

    llm = Anthropic(model=config.ANTHROPIC_MODEL, api_key=config.ANTHROPIC_API_KEY)
    response = llm.complete(prompt)

    sources = sorted({node.metadata.get("file_name", "unknown") for node in nodes})
    return {"answer": str(response), "sources": sources}


def ask_no_rag(question: str) -> dict:
    llm = Anthropic(model=config.ANTHROPIC_MODEL, api_key=config.ANTHROPIC_API_KEY)
    response = llm.complete(question)
    return {"answer": str(response), "sources": []}
