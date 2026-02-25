"""Domain types for external (internet) product search and comparison."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ExternalOffer:
    """A product offer from an external source (store/website)."""
    store_name: str
    title: str
    price: float
    url: str
    source_id: str  # unique id for this offer (e.g. store:sku)
    rating: float | None = None
    currency: str = "USD"

    def to_dict(self) -> dict[str, Any]:
        return {
            "storeName": self.store_name,
            "title": self.title,
            "price": self.price,
            "url": self.url,
            "sourceId": self.source_id,
            "rating": self.rating,
            "currency": self.currency,
        }


@dataclass
class ComparedDeal:
    """Best deal + alternatives after comparison."""
    best: ExternalOffer
    alternatives: list[ExternalOffer]
    reasoning: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "best": self.best.to_dict(),
            "alternatives": [a.to_dict() for a in self.alternatives],
            "reasoning": self.reasoning,
        }
