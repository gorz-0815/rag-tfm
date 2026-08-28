"""Discover a product's manual on the web via Claude's web search tool,
confirm it with the user, download it, then hand it to `src.ingest`.

Heavy/network-touching calls are kept inside the functions that need them,
not at module level, so this module stays importable without a live
Anthropic connection.
"""

import json

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
