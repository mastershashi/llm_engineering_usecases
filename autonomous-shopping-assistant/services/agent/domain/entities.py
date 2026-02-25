"""Agent domain entities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolCall:
    tool: str
    args: dict[str, Any]


@dataclass
class PlanStep:
    agent: str  # search | compare | cart | recommend | checkout
    description: str
    tool_calls: list[ToolCall]


@dataclass
class AgentReply:
    text: str
    tool_calls: list[ToolCall]
    state: str  # completed | tool_calls | needs_confirmation
    structured: dict[str, Any] | None = None  # cards, actions
