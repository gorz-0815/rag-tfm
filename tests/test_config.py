import importlib

from src import config


def test_chunk_defaults():
    assert config.CHUNK_SIZE == 512
    assert config.CHUNK_OVERLAP == 64


def test_chunk_size_overridable_via_env(monkeypatch):
    monkeypatch.setenv("CHUNK_SIZE", "256")
    monkeypatch.setenv("CHUNK_OVERLAP", "32")

    reloaded = importlib.reload(config)

    assert reloaded.CHUNK_SIZE == 256
    assert reloaded.CHUNK_OVERLAP == 32

    importlib.reload(config)
