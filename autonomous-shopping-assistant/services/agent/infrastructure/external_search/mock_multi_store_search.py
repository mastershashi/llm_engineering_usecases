"""Mock adapter: simulates searching multiple online stores with different prices (for demo)."""
from __future__ import annotations

import random
from shared.ports.external_search_port import IExternalProductSearch
from shared.domain.external_product import ExternalOffer

# Simulated "internet" catalog: products at different stores with different prices
_MOCK_STORES = [
    {"name": "TechMart", "base_url": "https://techmart.example/product/", "discount": 0.95},
    {"name": "BestDeal", "base_url": "https://bestdeal.example/item/", "discount": 0.88},
    {"name": "QuickShop", "base_url": "https://quickshop.example/p/", "discount": 1.0},
    {"name": "ValueStore", "base_url": "https://valuestore.example/dp/", "discount": 0.90},
]

# Broad catalog so different prompts return different results (no single hardcoded response)
_MOCK_PRODUCTS = [
    {"title": "Running Shoes Pro", "category": "footwear", "base_price": 89.99},
    {"title": "Trail Running Shoes", "category": "footwear", "base_price": 79.99},
    {"title": "Lightweight Running Shoes", "category": "footwear", "base_price": 59.99},
    {"title": "Wireless Earbuds", "category": "electronics", "base_price": 49.99},
    {"title": "Yoga Mat", "category": "sports", "base_price": 29.99},
    {"title": "Fitness Tracker", "category": "electronics", "base_price": 39.99},
    {"title": "Water Bottle", "category": "sports", "base_price": 19.99},
    {"title": "Laptop 15 inch", "category": "electronics", "base_price": 599.99},
    {"title": "Gaming Laptop", "category": "electronics", "base_price": 899.99},
    {"title": "Budget Laptop", "category": "electronics", "base_price": 349.99},
    {"title": "Wireless Headphones", "category": "electronics", "base_price": 79.99},
    {"title": "Noise Cancelling Headphones", "category": "electronics", "base_price": 149.99},
    {"title": "Smartphone", "category": "electronics", "base_price": 399.99},
    {"title": "Phone Case", "category": "electronics", "base_price": 19.99},
    {"title": "Backpack", "category": "accessories", "base_price": 45.99},
    {"title": "Desk Lamp", "category": "home", "base_price": 34.99},
]


class MockMultiStoreSearch(IExternalProductSearch):
    """Returns the same products from multiple 'stores' with different prices so we can compare and find best deal."""

    def search(
        self,
        query: str,
        category: str | None = None,
        max_price: float | None = None,
        limit_per_source: int = 5,
    ) -> list[ExternalOffer]:
        query_lower = (query or "").lower().strip()
        # Match by words: "gaming laptop" -> match products containing "gaming" or "laptop"
        query_words = [w for w in query_lower.split() if len(w) > 1]
        matches = []
        for p in _MOCK_PRODUCTS:
            title_lower = p["title"].lower()
            cat_lower = p["category"].lower()
            # Include if any query word is in title or category (so different prompts -> different results)
            if not query_words:
                match = True
            else:
                match = any(
                    w in title_lower or w in cat_lower
                    for w in query_words
                )
            if not match:
                continue
            if category and p["category"] != category:
                continue
            base = p["base_price"]
            if max_price is not None and base > max_price:
                continue
            for i, store in enumerate(_MOCK_STORES):
                price = round(base * store["discount"] * (0.98 + random.random() * 0.06), 2)
                if max_price is not None and price > max_price:
                    continue
                sku = f"{p['title'].replace(' ', '-')[:20]}-{i}"
                offer = ExternalOffer(
                    store_name=store["name"],
                    title=p["title"],
                    price=price,
                    url=f"{store['base_url']}{sku}",
                    source_id=f"{store['name']}:{sku}",
                    rating=round(3.5 + random.random() * 1.5, 1),
                )
                matches.append(offer)
            if len(matches) >= limit_per_source * len(_MOCK_STORES):
                break
        return matches[: limit_per_source * len(_MOCK_STORES)]
