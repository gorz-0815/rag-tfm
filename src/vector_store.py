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


def _model_already_cached() -> bool:
    """True if config.EMBEDDING_MODEL's weights are already in the local HF
    cache. Lets us skip the network freshness checks HuggingFaceEmbedding
    otherwise makes on every load - a real cost for a CLI that starts a
    fresh process per invocation - while still allowing the normal
    online/downloading path the first time a model isn't cached yet.

    Deliberately checks the filesystem directly rather than importing
    huggingface_hub: HF_HUB_OFFLINE is read into a module-level constant at
    huggingface_hub's *import* time, not re-read afterwards, so importing it
    here (even just to call scan_cache_dir()) before setting the env var
    would permanently freeze the flag as unset for the rest of the process.
    """
    import os
    from pathlib import Path

    cache_home = Path(
        os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")
    )
    cache_dir_name = "models--" + config.EMBEDDING_MODEL.replace("/", "--")
    return (cache_home / "hub" / cache_dir_name).is_dir()


def configure_embed_model() -> None:
    import os

    # Must run before importing HuggingFaceEmbedding (which pulls in
    # huggingface_hub): HF_HUB_OFFLINE is frozen into a module constant at
    # huggingface_hub's import time, so setting it after that import is a
    # no-op even though construction itself happens later.
    if _model_already_cached():
        os.environ.setdefault("HF_HUB_OFFLINE", "1")

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
