"""
Real web search via SerpAPI (Google Shopping). Set SERPAPI_KEY to use live product results.
Uses SerpAPI HTTP API so no extra pip package is required beyond httpx.
"""
from __future__ import annotations

import os
import httpx
from shared.ports.external_search_port import IExternalProductSearch
from shared.domain.external_product import ExternalOffer


class SerpAPISearch(IExternalProductSearch):
    """Search real products on the web via SerpAPI Google Shopping. Requires SERPAPI_KEY."""

    def __init__(self, api_key: str | None = None):
        self._api_key = (api_key or os.getenv("SERPAPI_KEY", "")).strip()
        self._base = "https://serpapi.com/search"

    def search(
        self,
        query: str,
        category: str | None = None,
        max_price: float | None = None,
        limit_per_source: int = 5,
    ) -> list[ExternalOffer]:
        if not self._api_key or not (query or "").strip():
            return []
        params = {
            "engine": "google_shopping",
            "q": query.strip(),
            "api_key": self._api_key,
            "num": min(limit_per_source * 2, 20),
        }
        if max_price is not None:
            params["max_price"] = str(int(max_price))
        try:
            r = httpx.get(self._base, params=params, timeout=15.0)
            r.raise_for_status()
            data = r.json()
        except Exception:
            return []
        offers = []
        shopping = data.get("shopping_results") or data.get("organic_results") or []
        for i, r in enumerate(shopping[: limit_per_source * 4]):
            title = (r.get("title") or "").strip()
            if not title:
                continue
            raw_price = r.get("price") or r.get("extracted_price") or r.get("price_raw")
            if raw_price is None:
                continue
            try:
                price = float(str(raw_price).replace(",", "").replace("$", "").split()[0])
            except (ValueError, IndexError):
                continue
            if max_price is not None and price > max_price:
                continue
            link = r.get("link") or r.get("product_link") or ""
            source = r.get("source") or r.get("merchant", {}).get("name", "Store")
            offers.append(ExternalOffer(
                store_name=source,
                title=title,
                price=price,
                url=link,
                source_id=f"{source}:{i}:{hash(title) % 10**8}",
                rating=None,
            ))
        return offers[: limit_per_source * 4]
