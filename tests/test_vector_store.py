"""Mocked tests for src.vector_store's cache-detection helper. Dependency-light
like test_docs_consistency.py - doesn't need llama_index/chromadb installed,
since _model_already_cached is a plain filesystem check.
"""

from src import config, vector_store


def test_model_already_cached_true_when_model_dir_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    monkeypatch.setenv("HF_HOME", str(tmp_path))
    (tmp_path / "hub" / "models--BAAI--bge-small-en-v1.5").mkdir(parents=True)

    assert vector_store._model_already_cached() is True


def test_model_already_cached_false_when_model_dir_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    monkeypatch.setenv("HF_HOME", str(tmp_path))

    assert vector_store._model_already_cached() is False
