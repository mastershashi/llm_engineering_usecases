"""Extract search query and filters from user message (no hardcoding)."""
from __future__ import annotations

import re
from typing import Any


# Common prefixes to strip so we get the actual product name
SEARCH_PREFIXES = [
    "find", "search", "search for", "show me", "get me", "look for", "i want",
    "i need", "find me", "get", "show", "look", "want", "need", "buy", "searching for",
]


def extract_search_intent(message: str) -> dict[str, Any]:
    """
    Parse user message to get:
    - query: the product they want (e.g. "running shoes", "laptop", "wireless earbuds")
    - max_price: if they said "under $50", "below 100", etc.
    - category: if mentioned (optional)
    """
    text = (message or "").strip().lower()
    if not text:
        return {"query": "", "max_price": None, "category": None}

    # Extract max price: "under $50", "under 50", "below 100", "max 200", "less than 80"
    max_price = None
    for pattern in [
        r"under\s*\$\s*(\d+(?:\.\d+)?)",
        r"under\s+(\d+(?:\.\d+)?)\s*(?:dollars?|bucks?)?",
        r"below\s+(\d+(?:\.\d+)?)",
        r"max\s+(\d+(?:\.\d+)?)",
        r"less\s+than\s+(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*(?:dollars?|bucks?)\s*or\s*less",
        r"\$\s*(\d+(?:\.\d+)?)\s*or\s*less",
    ]:
        m = re.search(pattern, text, re.I)
        if m:
            max_price = float(m.group(1))
            break

    # Remove price-related phrases so they don't end up in the query
    text_clean = re.sub(r"under\s*\$\s*\d+(?:\.\d+)?", "", text)
    text_clean = re.sub(r"under\s+\d+(?:\.\d+)?\s*(?:dollars?|bucks?)?", "", text_clean)
    text_clean = re.sub(r"below\s+\d+(?:\.\d+)?", "", text_clean)
    text_clean = re.sub(r"max\s+\d+(?:\.\d+)?", "", text_clean)
    text_clean = re.sub(r"less\s+than\s+\d+(?:\.\d+)?", "", text_clean)
    text_clean = re.sub(r"\d+(?:\.\d+)?\s*(?:dollars?|bucks?)", "", text_clean)

    # Strip prefixes to get the product part
    query = text_clean.strip()
    for prefix in SEARCH_PREFIXES:
        if query.startswith(prefix):
            query = query[len(prefix):].strip()
            break
    # Remove trailing junk
    query = re.sub(r"\s+(please|thanks|thank you|for me)?\s*$", "", query, flags=re.I).strip()
    if not query:
        # Fallback: use the original message minus numbers/price
        query = text_clean.strip() or message.strip()

    return {"query": query, "max_price": max_price, "category": None}
