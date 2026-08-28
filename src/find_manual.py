"""Discover a product's manual on the web via Claude's web search tool,
confirm it with the user, download it, then hand it to `src.ingest`.

Heavy/network-touching calls are kept inside the functions that need them,
not at module level, so this module stays importable without a live
Anthropic connection.
"""

import json
from pathlib import Path

from src import config

SEARCH_SYSTEM_PROMPT = (
    "You find official technical manuals for products on the web. Given a "
    "product name, use web search to locate its official PDF manual or "
    "documentation. Respond with ONLY a JSON array (no prose, no markdown "
    "fences) of candidate objects, most likely correct first: "
    '[{"url": "...", "title": "...", "confidence": "high|medium|low", '
    '"note": "..."}]. Only include candidates whose url links directly to a '
    'PDF document. "confidence": "high" means you are confident this is the '
    "correct, official manual for the named product, not a different "
    "product, a retailer listing, a forum post, or a review. If nothing "
    "plausible is found, respond with an empty JSON array []."
)


def _build_client():
    import anthropic

    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def search_candidates(product_name: str) -> list[dict]:
    """Ask Claude to search the web and rank candidate manual PDFs for
    `product_name`. Returns a list of {url, title, confidence, note} dicts,
    most likely correct first; empty if nothing plausible was found.
    """
    client = _build_client()
    response = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=2048,
        system=SEARCH_SYSTEM_PROMPT,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": f"Find the official manual for: {product_name}"}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return parse_candidates(text)


def parse_candidates(text: str) -> list[dict]:
    """Extract the JSON candidate array from Claude's reply text.

    Tolerates surrounding prose/markdown fences the model may add despite
    being asked not to. Returns [] if no valid JSON array is present.
    """
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        return []

    try:
        candidates = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []

    if not isinstance(candidates, list):
        return []
    return [c for c in candidates if isinstance(c, dict) and c.get("url")]


def needs_selection(candidates: list[dict]) -> bool:
    """A single high-confidence candidate gets a yes/no confirmation;
    anything else (multiple candidates, or one at less than high
    confidence) gets a numbered pick-list instead.
    """
    return not (len(candidates) == 1 and candidates[0].get("confidence") == "high")


def confirm_single(candidate: dict, input_func=input) -> dict | None:
    print(f"Found: {candidate.get('title', candidate['url'])}")
    print(f"  {candidate['url']}")
    if candidate.get("note"):
        print(f"  {candidate['note']}")
    answer = input_func("Use this manual? [y/N] ").strip().lower()
    return candidate if answer == "y" else None


def select_from_list(candidates: list[dict], input_func=input) -> dict | None:
    print("Multiple possible manuals found:")
    for i, candidate in enumerate(candidates, start=1):
        print(f"  {i}. {candidate.get('title', candidate['url'])}")
        print(f"     {candidate['url']}")
        if candidate.get("note"):
            print(f"     {candidate['note']}")
    answer = input_func("Pick a number, or press Enter to skip: ").strip()
    if not answer.isdigit():
        return None
    index = int(answer)
    if not (1 <= index <= len(candidates)):
        return None
    return candidates[index - 1]


def confirm_candidate(candidates: list[dict], input_func=input) -> dict | None:
    """Run the full confirmation flow and return the user-picked candidate,
    or None if the user declined or there was nothing to pick from.
    """
    if not candidates:
        return None
    if needs_selection(candidates):
        return select_from_list(candidates, input_func=input_func)
    return confirm_single(candidates[0], input_func=input_func)


PDF_MAGIC = b"%PDF-"


class ManualDownloadError(Exception):
    """Raised when a confirmed candidate can't be fetched as a real PDF."""


def is_pdf_response(content: bytes, content_type: str) -> bool:
    """A candidate's URL can carry a `.pdf`-looking path yet actually serve
    an HTML page (seen in practice with some manual-hosting sites) - check
    both the declared content-type and the file's own magic bytes rather
    than trusting either alone.
    """
    return "pdf" in content_type.lower() or content.startswith(PDF_MAGIC)


def filename_for(candidate: dict, url: str) -> str:
    from urllib.parse import urlparse

    name = Path(urlparse(url).path).name
    if name.lower().endswith(".pdf"):
        return name
    title = candidate.get("title") or "manual"
    slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in title).strip("-")
    return f"{slug or 'manual'}.pdf"


def download_manual(candidate: dict, dest_dir: Path | None = None) -> Path:
    """Fetch the confirmed candidate's URL and, once confirmed to actually
    be a PDF, write it to `dest_dir` (default: config.MANUALS_DIR).

    Raises ManualDownloadError on any network failure or non-PDF response;
    nothing is written to disk unless the response passes validation.
    """
    import httpx

    dest_dir = Path(dest_dir) if dest_dir is not None else config.MANUALS_DIR
    url = candidate["url"]

    try:
        response = httpx.get(url, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ManualDownloadError(f"Failed to download {url}: {exc}") from exc

    content_type = response.headers.get("content-type", "")
    if not is_pdf_response(response.content, content_type):
        raise ManualDownloadError(
            f"{url} did not return a PDF (content-type: {content_type or 'unknown'})"
        )

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename_for(candidate, url)
    dest_path.write_bytes(response.content)
    return dest_path
