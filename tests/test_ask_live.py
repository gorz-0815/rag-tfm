"""Real Anthropic API smoke test - opt-in only, skipped by default.

This makes an actual billed API call, so it does not run as part of the
normal `pytest` suite. To run it:

    RUN_LIVE_LLM_TESTS=1 pytest tests/test_ask_live.py

Requires ANTHROPIC_API_KEY set (via .env or the environment) and the full
requirements.txt stack installed.
"""

import os

import pytest

from src import config
from src.query import ask_no_rag

RUN_LIVE = os.getenv("RUN_LIVE_LLM_TESTS") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_LIVE,
    reason="Live Anthropic API call - set RUN_LIVE_LLM_TESTS=1 to run (costs real API usage)",
)


def test_ask_no_rag_gets_a_real_answer():
    if not config.ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY is not set")

    result = ask_no_rag("Reply with exactly one word: hello")

    assert result["answer"].strip()
    assert result["sources"] == []
