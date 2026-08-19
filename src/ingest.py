"""Ingest PDF manuals from data/manuals/ into a local Chroma-backed vector index."""

from pathlib import Path

from src import config


def validate_manuals_dir(manuals_dir: Path) -> None:
    if not manuals_dir.exists() or not any(manuals_dir.glob("*.pdf")):
        raise SystemExit(
            f"No PDF manuals found in {manuals_dir}. "
            "Add at least one PDF file to that directory before running ingestion."
        )


def build_index():
    validate_manuals_dir(config.MANUALS_DIR)

    import chromadb
    from llama_index.core import Settings, SimpleDirectoryReader, StorageContext, VectorStoreIndex
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.vector_stores.chroma import ChromaVectorStore

    documents = SimpleDirectoryReader(
        input_dir=str(config.MANUALS_DIR), required_exts=[".pdf"]
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
