"""Agent HTTP API: process request."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from shared.domain.value_objects import TenantId, UserId
from services.agent.application.use_cases import ProcessRequestUseCase
from services.agent.application.ports import ILLMProvider, IToolGateway
from services.agent.infrastructure.llm.stub_llm import StubLLM
from services.agent.infrastructure.tools.http_tool_gateway import HttpToolGateway
from services.agent.config import get_commerce_url, get_memory_url, get_llm_backend


class ProcessRequestBody(BaseModel):
    requestId: str | None = None
    tenantId: str
    userId: str
    sessionId: str | None = None
    messages: list[dict[str, str]]
    context: dict | None = None
    toolsAvailable: list[str] | None = None


def get_llm() -> ILLMProvider:
    from services.agent.config import get_llm_backend
    backend = get_llm_backend()
    if backend == "openai":
        from services.agent.infrastructure.llm.openai_llm import OpenAILLM
        import os
        return OpenAILLM(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    return StubLLM()


def get_external_search():
    import os
    if os.getenv("SERPAPI_KEY"):
        from services.agent.infrastructure.external_search.serpapi_search import SerpAPISearch
        return SerpAPISearch()
    from services.agent.infrastructure.external_search.mock_multi_store_search import MockMultiStoreSearch
    return MockMultiStoreSearch()


def get_tool_gateway(external_search=Depends(get_external_search)) -> IToolGateway:
    return HttpToolGateway(get_commerce_url(), get_memory_url(), external_search=external_search)


def get_process_use_case(
    llm: ILLMProvider = Depends(get_llm),
    gateway: IToolGateway = Depends(get_tool_gateway),
) -> ProcessRequestUseCase:
    return ProcessRequestUseCase(llm, gateway)


router = APIRouter(prefix="/v1", tags=["agent"])


@router.post("/process")
def process(
    body: ProcessRequestBody,
    use_case: ProcessRequestUseCase = Depends(get_process_use_case),
):
    tid = TenantId(UUID(body.tenantId))
    uid = UserId(UUID(body.userId))
    reply = use_case.execute(
        tenant_id=tid,
        user_id=uid,
        messages=body.messages,
        context=body.context or {},
        tools_available=body.toolsAvailable,
    )
    return {
        "reply": {
            "text": reply.text,
            "toolCalls": [{"tool": tc.tool, "args": tc.args} for tc in reply.tool_calls],
            "structured": reply.structured,
        },
        "state": reply.state,
    }
