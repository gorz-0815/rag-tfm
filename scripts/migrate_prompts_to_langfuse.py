"""One-off script: creates the app's prompts in Langfuse from the local
SYSTEM_PROMPT.md / PROMPT_TEMPLATE.md files, labeled "production". Not part
of the app's request path - run manually once per Langfuse project:

    python scripts/migrate_prompts_to_langfuse.py
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from src.prompts import SYSTEM_PROMPT_NAME, TEMPLATE_PROMPT_NAME  # noqa: E402


def main() -> None:
    from langfuse import get_client

    client = get_client()

    system_prompt = (_ROOT / "SYSTEM_PROMPT.md").read_text(encoding="utf-8").strip()
    client.create_prompt(
        name=SYSTEM_PROMPT_NAME,
        type="text",
        prompt=system_prompt,
        labels=["production"],
    )
    print(f"Created prompt '{SYSTEM_PROMPT_NAME}' (production)")

    template = (_ROOT / "PROMPT_TEMPLATE.md").read_text(encoding="utf-8")
    client.create_prompt(
        name=TEMPLATE_PROMPT_NAME,
        type="text",
        prompt=template,
        labels=["production"],
    )
    print(f"Created prompt '{TEMPLATE_PROMPT_NAME}' (production)")


if __name__ == "__main__":
    main()
