"""Dependency-light validation/identity helpers, kept free of heavy
third-party imports so they stay unit-testable without installing the full
embeddings/vector-store stack.
"""

import hashlib
from pathlib import Path


def manual_collection_name(manual_path: Path) -> str:
    digest = hashlib.sha256(Path(manual_path).read_bytes()).hexdigest()[:16]
    return f"manual_{digest}"


def validate_manual_path(manual_path: Path) -> None:
    if not manual_path.exists() or manual_path.suffix.lower() != ".pdf":
        raise SystemExit(
            f"Not a PDF file: {manual_path}. "
            "Pass the path to a single PDF manual, e.g. "
            "`python -m src.ingest data/manuals/your-manual.pdf`."
        )
