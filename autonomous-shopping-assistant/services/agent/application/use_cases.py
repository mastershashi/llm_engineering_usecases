"""Agent use cases: search internet, compare, recommend best deal, add to cart."""
from __future__ import annotations

from typing import Any

from shared.domain.value_objects import TenantId, UserId
from shared.domain.external_product import ExternalOffer
from services.agent.domain.entities import AgentReply, ToolCall
from services.agent.application.ports import ILLMProvider, IToolGateway
from services.agent.application.compare_use_case import compare_and_recommend


def _offers_from_result(result: Any) -> list[ExternalOffer]:
    if not isinstance(result, list):
        return []
    offers = []
    for r in result:
        if isinstance(r, dict) and r.get("sourceId"):
            offers.append(ExternalOffer(
                store_name=r.get("storeName", ""),
                title=r.get("title", ""),
                price=float(r.get("price", 0)),
                url=r.get("url", ""),
                source_id=r.get("sourceId", ""),
                rating=r.get("rating"),
            ))
    return offers


class ProcessRequestUseCase:
    """Process user message: LLM + tool loop. For search_internet: compare and recommend best deal."""

    def __init__(self, llm: ILLMProvider, tool_gateway: IToolGateway):
        self._llm = llm
        self._gateway = tool_gateway

    def execute(
        self,
        tenant_id: TenantId,
        user_id: UserId,
        messages: list[dict[str, str]],
        context: dict[str, Any] | None = None,
        tools_available: list[str] | None = None,
        max_tool_rounds: int = 5,
    ) -> AgentReply:
        context = context or {}
        tools_available = tools_available or [
            "search_internet", "compare_deals", "add_external_to_cart", "get_cart", "product_search", "add_to_cart"
        ]
        system_ctx = f"User preferences: {context.get('userPreferences', {})}. Memory: {context.get('memorySummary', '')}"
        msgs = [{"role": "system", "content": system_ctx}] + messages
        text, tool_calls = self._llm.chat(msgs, context=context)
        if not tool_calls:
            return AgentReply(text=text, tool_calls=[], state="completed", structured=None)
        tool_results = []
        for tc in tool_calls[:5]:
            try:
                result = self._gateway.execute(tenant_id, user_id, tc.tool, tc.args)
                tool_results.append({"tool": tc.tool, "result": result})
            except Exception as e:
                tool_results.append({"tool": tc.tool, "error": str(e)})
        cards = []
        best_deal = None
        reasoning = ""
        for tr in tool_results:
            if tr.get("tool") == "search_internet" and isinstance(tr.get("result"), list):
                offers = _offers_from_result(tr["result"])
                compared = compare_and_recommend(offers, top_n_alternatives=3)
                if compared:
                    best_deal = compared.best.to_dict()
                    reasoning = compared.reasoning
                    cards = [compared.best.to_dict()] + [a.to_dict() for a in compared.alternatives]
                    break
            if tr.get("tool") == "product_search" and isinstance(tr.get("result"), list):
                cards = [{"productId": p.get("productId"), "title": p.get("title"), "price": p.get("price"), "sourceId": p.get("productId")} for p in tr["result"][:5]]
        reply_text = text
        if best_deal and reasoning:
            reply_text = f"{text}\n\n**Best deal:** {reasoning}\nYou can say \"Add the best one to my cart\" to add it."
        structured = {"cards": cards, "bestDeal": best_deal, "reasoning": reasoning, "toolResults": tool_results} if (cards or tool_results) else None
        return AgentReply(text=reply_text, tool_calls=tool_calls, state="completed", structured=structured)
