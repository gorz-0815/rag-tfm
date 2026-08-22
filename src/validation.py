"""Dependency-light validation/identity helpers, kept free of heavy
third-party imports so they stay unit-testable without installing the full
embeddings/vector-store stack.
"""

import hashlib
from pathlib import Path


def manual_hash_id(manual_path: Path) -> str:
    return hashlib.sha256(Path(manual_path).read_bytes()).hexdigest()[:16]


def validate_manual_path(manual_path: Path) -> None:
    if not manual_path.exists() or manual_path.suffix.lower() != ".pdf":
        raise SystemExit(
            f"Not a PDF file: {manual_path}. "
            "Pass the path to a single PDF manual, e.g. "
            "`python -m src.ingest data/manuals/your-manual.pdf`."
        )
