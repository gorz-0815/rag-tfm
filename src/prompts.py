"""Loads and fills the prompt text from SYSTEM_PROMPT.md and
PROMPT_TEMPLATE.md, kept free of heavy third-party imports.
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
