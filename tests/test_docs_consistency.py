"""Catches doc/spec drift from the real CLI: if a flag gets renamed in
src/ask.py but a docs/example/spec command line still uses the old name,
this fails instead of relying on someone noticing during review.

Dependency-light: only imports src.ask (its own top-level imports are all
lightweight - see src/query.py's module docstring), no llama_index/chromadb
needed.
"""

import re
from pathlib import Path

from src.ask import build_parser

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Files that document `python -m src.ask` usage and must stay in sync with
# the real CLI flags. Add new locations here as they're introduced.
DOC_FILES = [
    PROJECT_ROOT / "docs" / "architecture.md",
    PROJECT_ROOT / "data" / "sample-questions.md",
    PROJECT_ROOT / "openspec" / "changes" / "rag-tfm-mvp" / "specs" / "manual-qa-cli" / "spec.md",
]

FLAG_RE = re.compile(r"--[a-zA-Z][\w-]*")


def _real_ask_flags() -> set[str]:
    return set(build_parser()._option_string_actions.keys())


def _documented_ask_flags() -> set[str]:
    flags: set[str] = set()
    for path in DOC_FILES:
        for line in path.read_text(encoding="utf-8").splitlines():
            if "python -m src.ask" not in line:
                continue
            flags.update(FLAG_RE.findall(line))
    return flags


def test_documented_ask_flags_exist_in_the_real_cli():
    real_flags = _real_ask_flags()
    assert real_flags, "sanity check: build_parser() should expose at least one flag"

    unknown = _documented_ask_flags() - real_flags
    assert not unknown, (
        f"Docs/specs reference python -m src.ask flag(s) that don't exist "
        f"in src/ask.py's parser: {sorted(unknown)}. Either the flag was "
        f"renamed/removed and the docs weren't updated, or DOC_FILES in "
        f"this test needs the new location added."
    )
