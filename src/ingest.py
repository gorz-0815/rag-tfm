"""Ingest PDF manuals from data/manuals/ into a local Chroma-backed vector index."""

import chromadb
from llama_index.core import Settings, SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from src import config
from src.validation import validate_manuals_dir


def build_index() -> VectorStoreIndex:
    validate_manuals_dir(config.MANUALS_DIR)

    # exclude_hidden=False: the default check treats any dot-prefixed path
    # segment as hidden, not just dotfiles inside manuals_dir - so a repo
    # checked out under a hidden ancestor directory (e.g. a worktree under
    # .claude/) would otherwise see every manual silently skipped.
    documents = SimpleDirectoryReader(
        input_dir=str(config.MANUALS_DIR), required_exts=[".pdf"], exclude_hidden=False
    ).load_data()

    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBEDDING_MODEL)
    Settings.node_parser = SentenceSplitter(
        chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP
    )

    chroma_client = chromadb.PersistentClient(path=str(config.STORAGE_DIR))
    chroma_collection = chroma_client.get_or_create_collection("manuals")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    return VectorStoreIndex.from_documents(documents, storage_context=storage_context)


def main() -> None:
    build_index()
    print(f"Ingested manuals from {config.MANUALS_DIR} into {config.STORAGE_DIR}")


if __name__ == "__main__":
    main()
