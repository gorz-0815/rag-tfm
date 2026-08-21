"""Ingest a single PDF manual into a local Chroma-backed vector index.

Heavy third-party imports (llama_index, chromadb) are kept inside build_index(),
not at module level, so this module can be imported - e.g. by tests/test_ask_live.py
- without the full embeddings/vector-store stack installed. See CLAUDE.md #7.
"""

import argparse
import contextlib
from pathlib import Path

from src import config
from src.validation import validate_manual_path


def build_index(manual_path: Path):
    import chromadb
    import chromadb.errors
    from llama_index.core import Settings, SimpleDirectoryReader, StorageContext, VectorStoreIndex
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.vector_stores.chroma import ChromaVectorStore

    validate_manual_path(manual_path)

    # input_files (a single explicit file), not input_dir - no directory walk,
    # so there's no hidden-ancestor-directory pitfall to work around here (see
    # the now-removed exclude_hidden=False workaround this replaced).
    documents = SimpleDirectoryReader(input_files=[str(manual_path)]).load_data()

    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBEDDING_MODEL)
    Settings.node_parser = SentenceSplitter(
        chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP
    )

    chroma_client = chromadb.PersistentClient(path=str(config.STORAGE_DIR))
    # Only one manual is ever indexed at a time - replace the collection on
    # every ingest rather than appending, so re-ingesting a different manual
    # can't leave stale chunks from a prior one mixed into retrieval.
    with contextlib.suppress(chromadb.errors.NotFoundError):
        chroma_client.delete_collection("manuals")
    chroma_collection = chroma_client.create_collection("manuals")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    return VectorStoreIndex.from_documents(documents, storage_context=storage_context)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest a single PDF manual into the vector index."
    )
    parser.add_argument("manual_path", type=Path, help="Path to the PDF manual to ingest")
    args = parser.parse_args()

    build_index(args.manual_path)
    print(f"Ingested {args.manual_path} into {config.STORAGE_DIR}")


if __name__ == "__main__":
    main()
