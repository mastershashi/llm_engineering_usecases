"""Stub LLM adapter: uses actual user message as search query, no hardcoded response."""
from __future__ import annotations

from typing import Any

from services.agent.application.ports import ILLMProvider
from services.agent.application.query_parser import extract_search_intent
from services.agent.domain.entities import ToolCall


class StubLLM(ILLMProvider):
    def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
        context: dict[str, Any] | None = None,
    ) -> tuple[str, list[ToolCall]]:
        last = messages[-1] if messages else {}
        content = (last.get("content") or "").strip()
        context = context or {}
        last_best = context.get("lastBestDeal") or {}
        content_lower = content.lower()

        # Don't treat cart/checkout/pay as search
        if "cart" in content_lower or "checkout" in content_lower or ("pay" in content_lower and "payment" not in content_lower):
            pass  # handle below
        # Any message that looks like a product search: use THEIR words as the query
        elif any(
            w in content_lower for w in (
                "find", "search", "show", "get", "look", "want", "need", "buy",
                "shoe", "earbud", "laptop", "phone", "headphone", "yoga", "mat",
                "product", "item", "something", "running", "wireless"
            )
        ) or (len(content.split()) <= 5 and "add" not in content_lower):
            # Short product-like message (e.g. "laptop under 500") but not "add X to cart"
            if content.strip():
                intent = extract_search_intent(content)
                query = (intent.get("query") or content).strip()
                if not query:
                    query = content.strip()
                args = {"query": query, "limit": 5}
                if intent.get("max_price") is not None:
                    args["maxPrice"] = intent["max_price"]
                return (
                    f"Searching across stores for: {query}...",
                    [ToolCall(tool="search_internet", args=args)],
                )
        if ("add" in content_lower and "cart" in content_lower) or "add the best" in content_lower or "add best" in content_lower:
            if last_best and last_best.get("sourceId"):
                return (
                    "Adding the best deal to your cart.",
                    [ToolCall(tool="add_external_to_cart", args={
                        "sourceId": last_best.get("sourceId"),
                        "title": last_best.get("title"),
                        "price": last_best.get("price"),
                        "quantity": 1,
                    })],
                )
            return ("I'll add that to your cart. (First search for a product so I can add the best deal.)", [])
        if "cart" in content_lower and ("what" in content_lower or "show" in content_lower or "view" in content_lower):
            return ("Checking your cart.", [ToolCall(tool="get_cart", args={})])
        if "checkout" in content_lower or "pay" in content_lower:
            order_id = context.get("lastOrderId") or last_best.get("orderId")
            if order_id:
                return (
                    "Completing your payment.",
                    [ToolCall(tool="confirm_payment", args={"orderId": order_id})],
                )
            return (
                "Creating your order for payment.",
                [ToolCall(tool="create_order", args={})],
            )
        return (
            "I search the internet across stores, compare prices, and recommend the best deal. "
            "Try: \"Find running shoes\" or \"Add the best one to my cart\" after a search.",
            [],
        )
