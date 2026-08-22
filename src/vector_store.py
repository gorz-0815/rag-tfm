"""Chroma-backed vector store access, shared by ingest.py and query.py so
the embedding model and vector store live in one place. Heavy imports are
kept inside the functions that need them, not at module level.
"""

from src import config
from src.validation import manual_hash_id


def _collection_name(manual_path) -> str:
    return f"manual_{manual_hash_id(manual_path)}"


def _client():
    import chromadb

    return chromadb.PersistentClient(path=str(config.STORAGE_DIR))


def configure_embed_model() -> None:
    from llama_index.core import Settings
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBEDDING_MODEL)


def get_existing_collection(manual_path):
    """Return the manual's ChromaVectorStore, or None if not yet ingested."""
    import chromadb.errors
    from llama_index.vector_stores.chroma import ChromaVectorStore

    try:
        chroma_collection = _client().get_collection(_collection_name(manual_path))
    except chromadb.errors.NotFoundError:
        return None
    return ChromaVectorStore(chroma_collection=chroma_collection)


def create_collection(manual_path):
    """Create the manual's collection and return its ChromaVectorStore."""
    from llama_index.vector_stores.chroma import ChromaVectorStore

    chroma_collection = _client().create_collection(_collection_name(manual_path))
    return ChromaVectorStore(chroma_collection=chroma_collection)
