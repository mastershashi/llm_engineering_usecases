"""OpenAI LLM adapter: uses OpenAI API for chat and tool choice."""
from __future__ import annotations

from typing import Any

from services.agent.application.ports import ILLMProvider
from services.agent.domain.entities import ToolCall


# Tool definitions for OpenAI function calling (optional; used when tools passed)
TOOLS_OPENAI = [
    {"type": "function", "function": {"name": "search_internet", "description": "Search for products across stores", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "maxPrice": {"type": "number"}}}}},
    {"type": "function", "function": {"name": "add_external_to_cart", "description": "Add an external offer to cart", "parameters": {"type": "object", "properties": {"sourceId": {"type": "string"}, "title": {"type": "string"}, "price": {"type": "number"}, "quantity": {"type": "integer"}}}}},
    {"type": "function", "function": {"name": "get_cart", "description": "Get current cart"}},
    {"type": "function", "function": {"name": "create_order", "description": "Create order from cart"}},
    {"type": "function", "function": {"name": "confirm_payment", "description": "Confirm payment for an order", "parameters": {"type": "object", "properties": {"orderId": {"type": "string"}}}}},
]


class OpenAILLM(ILLMProvider):
    """Real LLM: OpenAI API (gpt-4o-mini or gpt-4o). Set OPENAI_API_KEY and LLM_BACKEND=openai."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        import os
        self._model = model
        self._client = None
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
        context: dict[str, Any] | None = None,
    ) -> tuple[str, list[ToolCall]]:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY not set. Use StubLLM for dev or set the key.")
        client = self._get_client()
        openai_messages = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in messages]
        if context and (context.get("lastBestDeal") or context.get("lastOrderId")):
            ctx = "Last best deal: " + str(context.get("lastBestDeal", "")) + ". Last order ID: " + str(context.get("lastOrderId", ""))
            openai_messages = [{"role": "system", "content": ctx}] + openai_messages
        use_tools = tools if tools is not None else TOOLS_OPENAI
        response = client.chat.completions.create(
            model=self._model,
            messages=openai_messages,
            tools=use_tools,
            tool_choice="auto",
        )
        choice = response.choices[0] if response.choices else None
        if not choice:
            return ("I couldn't process that.", [])
        text = (choice.message.content or "").strip()
        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                name = tc.function.name if hasattr(tc.function, "name") else getattr(tc.function, "name", "")
                import json
                args = {}
                if hasattr(tc.function, "arguments") and tc.function.arguments:
                    try:
                        args = json.loads(tc.function.arguments)
                    except Exception:
                        pass
                tool_calls.append(ToolCall(tool=name, args=args))
        return (text, tool_calls)
