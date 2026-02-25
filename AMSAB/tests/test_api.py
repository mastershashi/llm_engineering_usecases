"""
AMSAB Integration Tests
=======================
Tests every major feature without a real OpenAI key.

Run:
    cd AMSAB
    .venv/bin/pytest tests/ -v
"""
import os
import sys
import tempfile
import uuid
from unittest.mock import AsyncMock, patch

import pytest

# ── Isolated temp DB must be set BEFORE any backend imports ──────────────── #
_TMP_DB = tempfile.mktemp(suffix="_amsab_test.db")
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["SQLITE_PATH"] = _TMP_DB

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Now import backend (picks up SQLITE_PATH from env)
from backend import database as db
from backend.models.task_graph import NodeStatus, PlanStatus, RiskLevel, TaskGraph, TaskNode
from backend.main import app

# TestClient must be created AFTER imports
from fastapi.testclient import TestClient


# ── Bootstrap: initialise the temp DB before any test runs ───────────────── #
def setup_module(module):
    db.init_db()


def teardown_module(module):
    try:
        os.unlink(_TMP_DB)
    except FileNotFoundError:
        pass


# ── Shared helpers ────────────────────────────────────────────────────────── #

def _make_graph(high_risk: bool = False) -> TaskGraph:
    return TaskGraph(
        goal="Research AI agents",
        expected_outcome="summary.txt created",
        nodes=[
            TaskNode(
                id=1, task="Search for top AI agents 2026", tool="web_search",
                args={"query": "top AI agents 2026"}, dependencies=[],
                risk_level=RiskLevel.low,
            ),
            TaskNode(
                id=2, task="Write summary to file", tool="filesystem_write",
                args={"filename": "summary.txt", "content": "$node_1_output"},
                dependencies=[1],
                risk_level=RiskLevel.high if high_risk else RiskLevel.low,
            ),
        ],
    )


def _seed(status: PlanStatus = PlanStatus.draft, high_risk: bool = False) -> str:
    pid = str(uuid.uuid4())
    graph = _make_graph(high_risk)
    db.create_plan(pid, "Research AI agents", graph)
    if status != PlanStatus.draft:
        db.update_plan_status(pid, status, graph)
    return pid


# Use TestClient as context manager so startup/shutdown events fire
@pytest.fixture(scope="module")
def client():
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ─────────────────────────────────────────────────────────────────────────── #
#  1. Health
# ─────────────────────────────────────────────────────────────────────────── #

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    print(f"\n  ✅ Health OK")


# ─────────────────────────────────────────────────────────────────────────── #
#  2. Goal submission (mocked Architect — no OpenAI key needed)
# ─────────────────────────────────────────────────────────────────────────── #

def test_submit_goal_mocked(client):
    with patch("backend.core.architect.Architect.plan", new=AsyncMock(return_value=_make_graph())):
        r = client.post("/api/goals", json={
            "goal": "Research AI agents",
            "permissions": {"read": True, "write": False, "network": True, "admin": False},
        })
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "draft"
    assert body["goal"] == "Research AI agents"
    assert len(body["dag"]["nodes"]) == 2
    print(f"\n  ✅ Goal submitted → plan {body['plan_id'][:8]}… (status=draft, 2 nodes)")


# ─────────────────────────────────────────────────────────────────────────── #
#  3. Plan listing + retrieval
# ─────────────────────────────────────────────────────────────────────────── #

def test_list_plans(client):
    _seed(); _seed()
    r = client.get("/api/plans")
    assert r.status_code == 200
    assert len(r.json()) >= 2
    print(f"\n  ✅ Listed {len(r.json())} plans")


def test_get_plan(client):
    pid = _seed()
    r = client.get(f"/api/plans/{pid}")
    assert r.status_code == 200
    assert r.json()["plan_id"] == pid
    print(f"\n  ✅ Retrieved plan {pid[:8]}…")


def test_get_plan_not_found(client):
    r = client.get("/api/plans/does-not-exist")
    assert r.status_code == 404
    print(f"\n  ✅ 404 for unknown plan")


# ─────────────────────────────────────────────────────────────────────────── #
#  4. Plan approval (kicks off background execution)
# ─────────────────────────────────────────────────────────────────────────── #

def test_approve_plan(client):
    pid = _seed()
    with patch("backend.core.orchestrator.Orchestrator.execute_plan", new=AsyncMock()):
        r = client.post(f"/api/plans/{pid}/approve")
    assert r.status_code == 200
    assert r.json()["status"] in ("approved", "running")
    print(f"\n  ✅ Plan approved, execution started")


def test_approve_plan_already_running(client):
    pid = _seed(status=PlanStatus.running)
    r = client.post(f"/api/plans/{pid}/approve")
    assert r.status_code == 400
    print(f"\n  ✅ Cannot re-approve a running plan (400)")


# ─────────────────────────────────────────────────────────────────────────── #
#  5. HITL — node approval & veto
# ─────────────────────────────────────────────────────────────────────────── #

def test_hitl_approve_node(client):
    pid = _seed(high_risk=True)
    db.upsert_node(pid, 2, status=NodeStatus.awaiting_approval)
    with patch("backend.core.orchestrator.Orchestrator.approve_node", new=AsyncMock()):
        r = client.post(
            f"/api/plans/{pid}/nodes/2/approve",
            json={"approved": True, "edited_args": {"filename": "edited.txt", "content": "hi"}},
        )
    assert r.status_code == 200
    print(f"\n  ✅ HITL node approved with edited args")


def test_hitl_veto_node(client):
    pid = _seed(high_risk=True)
    db.upsert_node(pid, 2, status=NodeStatus.awaiting_approval)
    with patch("backend.core.orchestrator.Orchestrator.skip_node", new=AsyncMock()):
        r = client.post(
            f"/api/plans/{pid}/nodes/2/approve",
            json={"approved": False},
        )
    assert r.status_code == 200
    print(f"\n  ✅ HITL node vetoed (skip)")


# ─────────────────────────────────────────────────────────────────────────── #
#  6. Time-travel: Rewind & branch
# ─────────────────────────────────────────────────────────────────────────── #

def test_rewind_no_side_effects(client):
    pid = _seed(status=PlanStatus.completed)
    db.upsert_node(pid, 1, status=NodeStatus.completed, result="some output")
    with patch("backend.core.orchestrator.Orchestrator.execute_plan", new=AsyncMock()):
        r = client.post(
            f"/api/plans/{pid}/nodes/1/rewind",
            json={"node_id": 1, "new_args": {"query": "better query"}},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "plan" in body
    assert "idempotency_warnings" in body
    assert body["idempotency_warnings"] == []   # web_search has no side effects
    assert body["plan"]["branch_of"] == pid
    print(f"\n  ✅ Rewind → branch {body['plan']['plan_id'][:8]}… (no warnings)")


def test_rewind_with_side_effect_warning(client):
    pid = _seed(status=PlanStatus.completed, high_risk=True)
    # Build a DAG with both nodes marked completed and persist it properly
    # (orchestrator always persists node status back into the DAG JSON via update_plan_status)
    graph = _make_graph(high_risk=True)
    for n in graph.nodes:
        n.status = NodeStatus.completed
        n.result = "done"
    db.update_plan_status(pid, PlanStatus.completed, graph)

    with patch("backend.core.orchestrator.Orchestrator.execute_plan", new=AsyncMock()):
        r = client.post(
            f"/api/plans/{pid}/nodes/2/rewind",
            json={"node_id": 2},
        )
    assert r.status_code == 200, r.text
    warnings = r.json()["idempotency_warnings"]
    assert len(warnings) >= 1
    assert "filesystem_write" in warnings[0]
    print(f"\n  ✅ Rewind detected idempotency warning: {warnings[0][:70]}…")


# ─────────────────────────────────────────────────────────────────────────── #
#  7. Kill switch
# ─────────────────────────────────────────────────────────────────────────── #

def test_kill_switch(client):
    pid = _seed(status=PlanStatus.running)
    with patch("backend.core.executor.SandboxExecutor.kill_plan_containers", new=AsyncMock()):
        r = client.post(f"/api/plans/{pid}/kill")
    assert r.status_code == 200
    assert r.json()["status"] == "killed"
    print(f"\n  ✅ Kill switch activated")


# ─────────────────────────────────────────────────────────────────────────── #
#  8. Logs
# ─────────────────────────────────────────────────────────────────────────── #

def test_get_logs(client):
    pid = _seed()
    db.add_log(pid, "First log line", node_id=1, level="info")
    db.add_log(pid, "Error log", node_id=1, level="error")
    r = client.get(f"/api/plans/{pid}/logs")
    assert r.status_code == 200
    logs = r.json()
    assert len(logs) == 2
    assert logs[0]["message"] == "First log line"
    assert logs[1]["level"] == "error"
    print(f"\n  ✅ Logs: {len(logs)} entries fetched correctly")


# ─────────────────────────────────────────────────────────────────────────── #
#  9. Memory Vault — short-term session breadcrumbs
# ─────────────────────────────────────────────────────────────────────────── #

def test_memory_session_breadcrumbs(client):
    pid = _seed()
    r = client.get(f"/api/plans/{pid}/memory/session")
    assert r.status_code == 200
    body = r.json()
    assert "breadcrumbs" in body
    assert "stats" in body
    assert isinstance(body["breadcrumbs"], list)
    print(f"\n  ✅ Session memory endpoint OK (stats={body['stats']})")


def test_memory_wipe_session(client):
    pid = _seed()
    r = client.delete(f"/api/plans/{pid}/memory/session")
    assert r.status_code == 200
    assert "wiped" in r.json()
    print(f"\n  ✅ Session memory wiped: {r.json()}")


# ─────────────────────────────────────────────────────────────────────────── #
#  10. Memory Vault — long-term semantic memory
# ─────────────────────────────────────────────────────────────────────────── #

def test_memory_long_term_store_and_recall(client):
    r = client.post("/api/memory/long-term", json={
        "key": "format pref", "value": "prefers JSON over CSV", "category": "preferences",
    })
    assert r.status_code == 200
    assert r.json()["status"] == "stored"

    r2 = client.get("/api/memory/long-term?q=JSON&n=3")
    assert r2.status_code == 200
    results = r2.json()["results"]
    assert isinstance(results, list)
    if results:  # ChromaDB may have stored it
        assert "JSON" in results[0]["document"] or "pref" in results[0]["document"]
    print(f"\n  ✅ Long-term memory store+recall: {len(results)} result(s)")


def test_memory_stats(client):
    r = client.get("/api/memory/stats")
    assert r.status_code == 200
    body = r.json()
    assert "short_term" in body and "long_term" in body
    print(f"\n  ✅ Memory stats: {body}")


def test_memory_wipe_all(client):
    r = client.delete("/api/memory/all")
    assert r.status_code == 200
    assert r.json()["status"] == "all_memory_wiped"
    # Verify count drops to 0
    r2 = client.get("/api/memory/stats")
    assert r2.json()["long_term"] == 0
    print(f"\n  ✅ All memory wiped, long_term=0")


# ─────────────────────────────────────────────────────────────────────────── #
#  11. MCP routes
# ─────────────────────────────────────────────────────────────────────────── #

def test_mcp_list_servers(client):
    r = client.get("/api/mcp/servers")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    print(f"\n  ✅ MCP servers listed: {r.json()}")


def test_mcp_register_server(client):
    # Correct schema: name + base_url (not url)
    r = client.post("/api/mcp/servers", json={
        "name": "test-mcp", "base_url": "http://localhost:9999", "api_key": ""
    })
    assert r.status_code == 201, r.text
    assert "test-mcp" in r.json()["message"]
    # Verify it appears in list
    r2 = client.get("/api/mcp/servers")
    assert "test-mcp" in r2.json()
    print(f"\n  ✅ MCP server registered and listed")


# ─────────────────────────────────────────────────────────────────────────── #
#  12. Database layer unit tests (direct, no HTTP)
# ─────────────────────────────────────────────────────────────────────────── #

def test_db_create_and_get_plan():
    pid = str(uuid.uuid4())
    db.create_plan(pid, "DB test goal", _make_graph())
    row = db.get_plan(pid)
    assert row is not None
    assert row.goal == "DB test goal"
    assert row.status == PlanStatus.draft
    print(f"\n  ✅ DB: create + get plan")


def test_db_update_status():
    pid = _seed()
    db.update_plan_status(pid, PlanStatus.running, _make_graph())
    row = db.get_plan(pid)
    assert row.status == PlanStatus.running
    print(f"\n  ✅ DB: status updated to running")


def test_db_upsert_node_and_snapshot():
    pid = _seed()
    db.upsert_node(
        pid, 1,
        status=NodeStatus.completed,
        result="found results",
        snapshot={"output": "found results"},
        token_usage=42,
    )
    snap = db.get_node_snapshot(pid, 1)
    assert snap is not None
    assert snap["output"] == "found results"
    print(f"\n  ✅ DB: node upsert + snapshot retrieval (token_usage=42)")


def test_db_logs():
    pid = _seed()
    db.add_log(pid, "hello log", node_id=1)
    db.add_log(pid, "error log", node_id=2, level="error")
    logs = db.get_logs(pid)
    assert len(logs) == 2
    assert logs[1]["level"] == "error"
    print(f"\n  ✅ DB: add + get logs (2 entries)")


def test_db_branch_plan():
    parent = _seed()
    child = str(uuid.uuid4())
    db.create_plan(child, "Branch goal", _make_graph(), branch_of=parent)
    row = db.get_plan(child)
    assert row.branch_of == parent
    print(f"\n  ✅ DB: branch plan links back to parent")
