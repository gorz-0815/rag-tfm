from pathlib import Path

from pypdf import PdfReader

MANUAL_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "manuals" / "aquaflow-200-manual.pdf"
)

EXPECTED_SECTIONS = [
    "Overview",
    "Setup Instructions",
    "Daily Operation",
    "Filter Replacement",
    "Cleaning and Maintenance",
    "Troubleshooting",
    "Safety Warnings",
]


def test_sample_manual_exists():
    assert MANUAL_PATH.exists()


def test_sample_manual_is_synthetic():
    metadata = PdfReader(MANUAL_PATH).metadata
    assert "synthetic" in metadata.subject.lower()


def test_sample_manual_has_expected_sections():
    text = "".join(page.extract_text() for page in PdfReader(MANUAL_PATH).pages)

    for section in EXPECTED_SECTIONS:
        assert section in text
