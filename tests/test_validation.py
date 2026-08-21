import pytest

from src.validation import validate_manual_path


def test_validate_manual_path_missing(tmp_path):
    missing_path = tmp_path / "does-not-exist.pdf"

    with pytest.raises(SystemExit):
        validate_manual_path(missing_path)


def test_validate_manual_path_rejects_non_pdf(tmp_path):
    notes_path = tmp_path / "notes.txt"
    notes_path.write_text("not a pdf")

    with pytest.raises(SystemExit):
        validate_manual_path(notes_path)


def test_validate_manual_path_with_pdf(tmp_path):
    manual_path = tmp_path / "manual.pdf"
    manual_path.write_bytes(b"%PDF-1.4 fake content")

    validate_manual_path(manual_path)
