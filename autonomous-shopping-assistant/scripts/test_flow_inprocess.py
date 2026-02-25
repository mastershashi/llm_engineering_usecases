#!/usr/bin/env python3
"""
Run the agent + compare flow in one process (no HTTP). Verifies search_internet -> compare -> best deal.
"""
import os
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("ENV", "dev")

from uuid import UUID
from shared.domain.value_objects import TenantId, UserId
from services.agent.infrastructure.external_search.mock_multi_store_search import MockMultiStoreSearch
from services.agent.application.compare_use_case import compare_and_recommend
from services.agent.application.use_cases import ProcessRequestUseCase, _offers_from_result
from services.agent.infrastructure.llm.stub_llm import StubLLM
from shared.domain.external_product import ExternalOffer


def test_external_search_and_compare():
    search = MockMultiStoreSearch()
    offers = search.search("running shoes", limit_per_source=3)
    assert len(offers) > 0, "Mock search should return offers"
    compared = compare_and_recommend(offers, top_n_alternatives=2)
    assert compared is not None
    assert compared.best.price <= min(o.price for o in offers)
    assert "Best deal" in compared.reasoning or compared.best.store_name in compared.reasoning
    print("[OK] External search + compare:", compared.reasoning[:60], "...")


def test_stub_llm_returns_search_tool():
    llm = StubLLM()
    text, tool_calls = llm.chat([{"role": "user", "content": "Find running shoes"}], context={})
    assert len(tool_calls) == 1
    assert tool_calls[0].tool == "search_internet"
    assert "query" in tool_calls[0].args
    print("[OK] StubLLM returns search_internet for 'Find running shoes'")


def test_process_request_use_case_search():
    class MockGateway:
        def execute(self, tenant_id, user_id, tool, args):
            if tool == "search_internet":
                search = MockMultiStoreSearch()
                offers = search.search(args.get("query", ""), limit_per_source=3)
                return [o.to_dict() for o in offers]
            return None

    llm = StubLLM()
    gateway = MockGateway()
    use_case = ProcessRequestUseCase(llm, gateway)
    tid = TenantId(UUID("00000000-0000-0000-0000-000000000001"))
    uid = UserId(UUID("00000000-0000-0000-0000-000000000002"))
    reply = use_case.execute(tid, uid, [{"role": "user", "content": "Find running shoes"}])
    assert reply.text
    assert reply.structured is not None
    assert reply.structured.get("bestDeal") is not None
    assert len(reply.structured.get("cards", [])) > 0
    print("[OK] ProcessRequestUseCase: got bestDeal and cards")
    print("    Best:", reply.structured["bestDeal"].get("storeName"), reply.structured["bestDeal"].get("price"))
    return True


if __name__ == "__main__":
    print("Testing flow in-process (no servers)...")
    test_external_search_and_compare()
    test_stub_llm_returns_search_tool()
    test_process_request_use_case_search()
    print("\nAll checks passed. To run the full stack:")
    print("  1. pip install -r requirements.txt")
    print("  2. export PYTHONPATH=$(pwd) ENV=dev")
    print("  3. Start 5 terminals with uvicorn (see README), or: python3 scripts/run_all_dev.py")
    print("  4. Open http://localhost:8080 and try 'Find running shoes'")
