"""Compare offers from multiple sources and recommend the best deal."""
from __future__ import annotations

from shared.domain.external_product import ExternalOffer, ComparedDeal


def compare_and_recommend(offers: list[ExternalOffer], top_n_alternatives: int = 3) -> ComparedDeal | None:
    """Pick best offer by price (then rating), return best + alternatives."""
    if not offers:
        return None
    sorted_offers = sorted(offers, key=lambda o: (o.price, -(o.rating or 0)))
    best = sorted_offers[0]
    alternatives = [o for o in sorted_offers[1 : top_n_alternatives + 1] if o.source_id != best.source_id][:top_n_alternatives]
    reasoning = f"Best deal: {best.store_name} at ${best.price:.2f}"
    if best.rating:
        reasoning += f" (rating {best.rating})"
    if alternatives:
        reasoning += f". Other options: " + ", ".join(f"{a.store_name} ${a.price:.2f}" for a in alternatives[:3])
    return ComparedDeal(best=best, alternatives=alternatives, reasoning=reasoning)
