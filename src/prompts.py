"""Dependency-light prompt/message building, kept free of heavy third-party
imports so it stays unit-testable without installing the full RAG stack.

The prompt text itself lives in the root-level PROMPT_TEMPLATE.md, not
inline in code, so it can be reviewed/edited without touching Python.
"""

from pathlib import Path

NO_CONTEXT_MESSAGE = "No relevant content found in the ingested manuals."

_PROMPT_TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "PROMPT_TEMPLATE.md"


def build_context_prompt(question: str, context: str) -> str:
    template = _PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
    return template.replace("{{context}}", context).replace("{{question}}", question)
