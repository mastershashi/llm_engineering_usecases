"""MCP Gateway — bridges AMSAB to any Model Context Protocol tool server.

MCP is the 'USB-C for AI' — being MCP-native gives instant access to
10,000+ community-built tools (Google Drive, GitHub, Slack, etc.)
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class McpServer:
    name: str
    base_url: str
    api_key: str = ""
    timeout: int = 30


@dataclass
class McpTool:
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)


class McpGateway:
    """Client for MCP-compliant tool servers."""

    def __init__(self) -> None:
        self._servers: dict[str, McpServer] = {}

    def register_server(self, server: McpServer) -> None:
        self._servers[server.name] = server
        logger.info("Registered MCP server: %s at %s", server.name, server.base_url)

    async def list_tools(self, server_name: str) -> list[McpTool]:
        server = self._servers.get(server_name)
        if not server:
            raise ValueError(f"Unknown MCP server: {server_name}")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{server.base_url}/tools/list",
                headers=self._headers(server),
                timeout=aiohttp.ClientTimeout(total=server.timeout),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return [
                    McpTool(
                        name=t["name"],
                        description=t.get("description", ""),
                        input_schema=t.get("inputSchema", {}),
                    )
                    for t in data.get("tools", [])
                ]

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """Invoke a tool on an MCP server and return the result."""
        server = self._servers.get(server_name)
        if not server:
            raise ValueError(f"Unknown MCP server: {server_name}")

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }

        logger.info("MCP call: %s/%s args=%s", server_name, tool_name, arguments)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{server.base_url}/mcp",
                json=payload,
                headers=self._headers(server),
                timeout=aiohttp.ClientTimeout(total=server.timeout),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()

        if "error" in data:
            raise RuntimeError(f"MCP error: {data['error']}")

        result = data.get("result", {})
        # Extract text content from MCP result format
        content = result.get("content", [])
        if content and isinstance(content, list):
            return "\n".join(c.get("text", "") for c in content if c.get("type") == "text")
        return json.dumps(result)

    @staticmethod
    def _headers(server: McpServer) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if server.api_key:
            headers["Authorization"] = f"Bearer {server.api_key}"
        return headers

    def list_servers(self) -> list[str]:
        return list(self._servers.keys())


mcp_gateway = McpGateway()
