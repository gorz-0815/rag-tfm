"""Real Anthropic API smoke tests - opt-in only, skipped by default.

These make actual billed API calls, so they do not run as part of the
normal `pytest` suite. To run them:

    RUN_LIVE_LLM_TESTS=1 pytest tests/test_ask_live.py

Requires ANTHROPIC_API_KEY set (via .env or the environment) and the full
requirements.txt stack installed.

test_ask_rag_gets_a_real_grounded_answer additionally builds a real index
from the committed sample manual into a temp directory (never the repo's
own storage/ - a dev's local index is never touched or reused) using the
full ingestion pipeline, so it also exercises embeddings end-to-end, not
just the Claude call. We build fresh rather than committing a pre-built
storage/ fixture because a persisted Chroma collection is tied to the
embedding model version/config that created it - a stale binary fixture
could silently mismatch whatever's currently pinned in requirements.txt
and fail in a confusing way; building it from the pinned deps each run
guarantees it matches what's actually installed.
"""

import os

import pytest

from src import config
from src.query import ask_no_context

RUN_LIVE = os.getenv("RUN_LIVE_LLM_TESTS") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_LIVE,
    reason="Live Anthropic API call - set RUN_LIVE_LLM_TESTS=1 to run (costs real API usage)",
)


def test_ask_no_context_gets_a_real_answer():
    if not config.ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY is not set")

    result = ask_no_context("Reply with exactly one word: hello")

    assert result["answer"].strip()
    assert result["sources"] == []


def test_ask_rag_gets_a_real_grounded_answer(tmp_path, monkeypatch):
    from src.ingest import build_index
    from src.query import ask_rag

    if not config.ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY is not set")

    monkeypatch.setattr(config, "STORAGE_DIR", tmp_path / "storage")

    build_index()
    result = ask_rag("How long should I soak a new filter cartridge before using it?")

    assert "15" in result["answer"]
    assert result["sources"] == ["aquaflow-200-manual.pdf"]
