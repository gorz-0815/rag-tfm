"""Dependency-light validation helpers, kept free of heavy third-party imports
so they stay unit-testable without installing the full embeddings/vector-store stack.
"""

from pathlib import Path


def validate_manuals_dir(manuals_dir: Path) -> None:
    if not manuals_dir.exists() or not any(manuals_dir.glob("*.pdf")):
        raise SystemExit(
            f"No PDF manuals found in {manuals_dir}. "
            "Add at least one PDF file to that directory before running ingestion."
        )
