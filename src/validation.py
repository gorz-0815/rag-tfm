"""Dependency-light validation helpers, kept free of heavy third-party imports
so they stay unit-testable without installing the full embeddings/vector-store stack.
"""

from pathlib import Path


def validate_manual_path(manual_path: Path) -> None:
    if not manual_path.exists() or manual_path.suffix.lower() != ".pdf":
        raise SystemExit(
            f"Not a PDF file: {manual_path}. "
            "Pass the path to a single PDF manual, e.g. "
            "`python -m src.ingest data/manuals/your-manual.pdf`."
        )
