"""Dependency-light prompt/message building, kept free of heavy third-party
imports so it stays unit-testable without installing the full RAG stack.

The prompt text itself lives in root-level markdown files, not inline in
code, so it can be reviewed/edited without touching Python: SYSTEM_PROMPT.md
holds the static instruction sent as the Anthropic API's real `system`
message (RAG and full-doc modes only - no-context mode sends no
instructions, since there's no context to constrain the answer to);
PROMPT_TEMPLATE.md holds the per-question user-turn template.
"""

from pathlib import Path

NO_CONTEXT_MESSAGE = "No relevant content found in the ingested manual."

_ROOT = Path(__file__).resolve().parent.parent
_SYSTEM_PROMPT_PATH = _ROOT / "SYSTEM_PROMPT.md"
_PROMPT_TEMPLATE_PATH = _ROOT / "PROMPT_TEMPLATE.md"


def load_system_prompt() -> str:
    return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()


def build_context_prompt(question: str, context: str) -> str:
    template = _PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
    return template.replace("{{context}}", context).replace("{{question}}", question)
