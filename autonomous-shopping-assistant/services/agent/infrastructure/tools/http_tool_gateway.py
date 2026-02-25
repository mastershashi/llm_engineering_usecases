"""Tool gateway: external search, Commerce, Memory."""
from __future__ import annotations

from typing import Any

import httpx
from shared.domain.value_objects import TenantId, UserId
from shared.domain.external_product import ExternalOffer
from services.agent.application.ports import IToolGateway


class HttpToolGateway(IToolGateway):
    def __init__(
        self,
        commerce_base_url: str,
        memory_base_url: str,
        external_search: Any = None,
    ):
        self._commerce = commerce_base_url.rstrip("/")
        self._memory = memory_base_url.rstrip("/")
        self._external_search = external_search

    def execute(
        self,
        tenant_id: TenantId,
        user_id: UserId,
        tool: str,
        args: dict[str, Any],
    ) -> Any:
        tid, uid = str(tenant_id), str(user_id)
        if tool == "search_internet" and self._external_search:
            from services.agent.infrastructure.external_search.mock_multi_store_search import MockMultiStoreSearch
            offers = self._external_search.search(
                query=args.get("query", ""),
                category=args.get("category"),
                max_price=args.get("maxPrice"),
                limit_per_source=args.get("limit", 5),
            )
            # If real search (e.g. SerpAPI) returns nothing, fall back to mock so user still gets results
            if not offers and self._external_search.__class__.__name__ != "MockMultiStoreSearch":
                mock = MockMultiStoreSearch()
                offers = mock.search(
                    query=args.get("query", ""),
                    max_price=args.get("maxPrice"),
                    limit_per_source=args.get("limit", 5),
                )
            return [o.to_dict() for o in offers]
        if tool == "add_external_to_cart":
            r = httpx.post(
                f"{self._commerce}/v1/tenants/{tid}/users/{uid}/cart/items/external",
                json={
                    "sourceId": args.get("sourceId", ""),
                    "title": args.get("title", ""),
                    "price": args.get("price", 0),
                    "quantity": args.get("quantity", 1),
                },
                timeout=10.0,
            )
            r.raise_for_status()
            return r.json()
        if tool == "product_search":
            r = httpx.get(
                f"{self._commerce}/v1/tenants/{tid}/products/search",
                params={
                    "q": args.get("query"),
                    "maxPrice": args.get("maxPrice"),
                    "limit": args.get("limit", 10),
                },
                timeout=10.0,
            )
            r.raise_for_status()
            return r.json()
        if tool == "get_product":
            pid = args.get("productId")
            if not pid:
                return None
            r = httpx.get(f"{self._commerce}/v1/tenants/{tid}/products/{pid}", timeout=10.0)
            r.raise_for_status()
            return r.json()
        if tool == "get_cart":
            r = httpx.get(f"{self._commerce}/v1/tenants/{tid}/users/{uid}/cart", timeout=10.0)
            r.raise_for_status()
            return r.json()
        if tool == "add_to_cart":
            pid = args.get("productId")
            qty = args.get("quantity", 1)
            if not pid:
                return {"error": "missing productId"}
            r = httpx.post(
                f"{self._commerce}/v1/tenants/{tid}/users/{uid}/cart/items",
                json={"productId": pid, "quantity": qty},
                timeout=10.0,
            )
            r.raise_for_status()
            return r.json()
        if tool == "get_memory":
            r = httpx.get(f"{self._memory}/v1/tenants/{tid}/users/{uid}/memory", timeout=10.0)
            r.raise_for_status()
            return r.json()
        if tool == "create_order":
            r = httpx.post(f"{self._commerce}/v1/tenants/{tid}/users/{uid}/orders", timeout=10.0)
            r.raise_for_status()
            return r.json()
        if tool == "confirm_payment":
            order_id = args.get("orderId")
            if not order_id:
                return {"error": "missing orderId"}
            r = httpx.post(
                f"{self._commerce}/v1/tenants/{tid}/users/{uid}/orders/{order_id}/confirm-payment",
                timeout=10.0,
            )
            r.raise_for_status()
            return r.json()
        return {"error": f"Unknown tool: {tool}"}
