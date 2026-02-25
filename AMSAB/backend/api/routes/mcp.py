"""MCP server management routes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...core.mcp_gateway import McpServer, mcp_gateway

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


class RegisterServerRequest(BaseModel):
    name: str
    base_url: str
    api_key: str = ""


@router.post("/servers", status_code=201)
async def register_server(body: RegisterServerRequest) -> dict:
    mcp_gateway.register_server(McpServer(**body.model_dump()))
    return {"message": f"Registered MCP server '{body.name}'"}


@router.get("/servers")
async def list_servers() -> list[str]:
    return mcp_gateway.list_servers()


@router.get("/servers/{server_name}/tools")
async def list_tools(server_name: str) -> list[dict]:
    try:
        tools = await mcp_gateway.list_tools(server_name)
        return [{"name": t.name, "description": t.description} for t in tools]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
