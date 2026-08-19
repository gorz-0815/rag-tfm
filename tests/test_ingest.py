import pytest

from src.ingest import validate_manuals_dir


def test_validate_manuals_dir_missing(tmp_path):
    missing_dir = tmp_path / "does-not-exist"

    with pytest.raises(SystemExit):
        validate_manuals_dir(missing_dir)


def test_validate_manuals_dir_empty(tmp_path):
    empty_dir = tmp_path / "manuals"
    empty_dir.mkdir()

    with pytest.raises(SystemExit):
        validate_manuals_dir(empty_dir)


def test_validate_manuals_dir_ignores_non_pdf(tmp_path):
    manuals_dir = tmp_path / "manuals"
    manuals_dir.mkdir()
    (manuals_dir / "notes.txt").write_text("not a pdf")

    with pytest.raises(SystemExit):
        validate_manuals_dir(manuals_dir)


def test_validate_manuals_dir_with_pdf(tmp_path):
    manuals_dir = tmp_path / "manuals"
    manuals_dir.mkdir()
    (manuals_dir / "manual.pdf").write_bytes(b"%PDF-1.4 fake content")

    validate_manuals_dir(manuals_dir)
