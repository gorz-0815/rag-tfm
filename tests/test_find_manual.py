from src.find_manual import (
    confirm_candidate,
    filename_for,
    is_pdf_response,
    needs_selection,
    parse_candidates,
)


def test_parse_candidates_plain_json():
    text = '[{"url": "https://x.com/a.pdf", "title": "t", "confidence": "high", "note": "n"}]'

    assert parse_candidates(text) == [
        {"url": "https://x.com/a.pdf", "title": "t", "confidence": "high", "note": "n"}
    ]


def test_parse_candidates_strips_markdown_fence():
    text = 'Sure, here you go:\n```json\n[{"url": "https://x.com/a.pdf"}]\n```'

    assert parse_candidates(text) == [{"url": "https://x.com/a.pdf"}]


def test_parse_candidates_empty_array():
    assert parse_candidates("[]") == []


def test_parse_candidates_no_json_present():
    assert parse_candidates("I could not find anything.") == []


def test_parse_candidates_drops_entries_without_url():
    text = '[{"title": "no url here"}, {"url": "https://x.com/a.pdf"}]'

    assert parse_candidates(text) == [{"url": "https://x.com/a.pdf"}]


def test_needs_selection_false_for_single_high_confidence():
    assert needs_selection([{"url": "https://x.com/a.pdf", "confidence": "high"}]) is False


def test_needs_selection_true_for_single_low_confidence():
    assert needs_selection([{"url": "https://x.com/a.pdf", "confidence": "low"}]) is True


def test_needs_selection_true_for_multiple_candidates():
    candidates = [
        {"url": "https://x.com/a.pdf", "confidence": "high"},
        {"url": "https://x.com/b.pdf", "confidence": "high"},
    ]

    assert needs_selection(candidates) is True


def test_confirm_candidate_no_candidates_returns_none():
    assert confirm_candidate([], input_func=lambda _: "y") is None


def test_confirm_candidate_single_confirmed():
    candidate = {"url": "https://x.com/a.pdf", "confidence": "high"}

    assert confirm_candidate([candidate], input_func=lambda _: "y") == candidate


def test_confirm_candidate_single_declined():
    candidate = {"url": "https://x.com/a.pdf", "confidence": "high"}

    assert confirm_candidate([candidate], input_func=lambda _: "n") is None


def test_confirm_candidate_list_picks_by_number():
    candidates = [
        {"url": "https://x.com/a.pdf", "confidence": "medium"},
        {"url": "https://x.com/b.pdf", "confidence": "medium"},
    ]

    assert confirm_candidate(candidates, input_func=lambda _: "2") == candidates[1]


def test_confirm_candidate_list_declined_on_blank():
    candidates = [
        {"url": "https://x.com/a.pdf", "confidence": "medium"},
        {"url": "https://x.com/b.pdf", "confidence": "medium"},
    ]

    assert confirm_candidate(candidates, input_func=lambda _: "") is None


def test_confirm_candidate_list_out_of_range_returns_none():
    candidates = [{"url": "https://x.com/a.pdf", "confidence": "medium"}]

    assert confirm_candidate(candidates, input_func=lambda _: "5") is None


def test_is_pdf_response_by_content_type():
    assert is_pdf_response(b"not really pdf bytes", "application/pdf") is True


def test_is_pdf_response_by_magic_bytes():
    assert is_pdf_response(b"%PDF-1.4 ...", "text/html") is True


def test_is_pdf_response_rejects_html():
    assert is_pdf_response(b"<html></html>", "text/html; charset=utf-8") is False


def test_filename_for_uses_url_basename_when_pdf():
    candidate = {"title": "Ignored Title"}

    assert filename_for(candidate, "https://x.com/path/manual.pdf") == "manual.pdf"


def test_filename_for_falls_back_to_slugified_title():
    candidate = {"title": "My Cool Manual!"}

    assert filename_for(candidate, "https://x.com/download?id=123") == "My-Cool-Manual.pdf"


def test_filename_for_falls_back_to_generic_name_without_title():
    candidate = {}

    assert filename_for(candidate, "https://x.com/download") == "manual.pdf"
