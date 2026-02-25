"""Port: search products across the internet (multiple stores/sources)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from shared.domain.external_product import ExternalOffer


class IExternalProductSearch(ABC):
    """Search external sources (web/stores) for products. Returns offers from multiple sources for comparison."""

    @abstractmethod
    def search(
        self,
        query: str,
        category: str | None = None,
        max_price: float | None = None,
        limit_per_source: int = 5,
    ) -> list[ExternalOffer]:
        """Return product offers from multiple stores/sources (e.g. internet)."""
        ...
