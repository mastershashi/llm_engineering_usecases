"""Agent ports: LLM, Tool Gateway."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from shared.domain.value_objects import TenantId, UserId
from services.agent.domain.entities import AgentReply, ToolCall


class ILLMProvider(ABC):
    """Port for LLM. Adapters: StubLLM (dev), OpenAI (prod)."""

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
        context: dict[str, Any] | None = None,
    ) -> tuple[str, list[ToolCall]]:
        """Return (reply_text, tool_calls)."""
        ...


class IToolGateway(ABC):
    """Port for executing tools. Adapters: HttpToolGateway (calls Commerce/Memory)."""

    @abstractmethod
    def execute(
        self,
        tenant_id: TenantId,
        user_id: UserId,
        tool: str,
        args: dict[str, Any],
    ) -> Any:
        ...


class IPlanner(ABC):
    """Port for planning steps."""

    @abstractmethod
    def plan(self, user_message: str, context: dict[str, Any]) -> list[str]:
        """Return list of step descriptions or agent names."""
        ...
