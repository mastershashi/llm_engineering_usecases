# AMSAB — Autonomous Multi-Step Agent Builder

> A Local-First, Sandbox-Native agent framework that solves the **Trust & Transparency** gap in autonomous AI agents.

## Why AMSAB?

| Feature | AutoGPT / OpenClaw | AMSAB |
|---|---|---|
| Security | Direct system access (RCE risk) | Docker sandbox ("Steel Box") by default |
| Reliability | "Best effort" loop — fragile | Stateful DAG with Checkpoint / Resume |
| Transparency | Chat-only, hard to debug | Live Visual DAG Dashboard |
| Tool Integration | Custom plugins (inconsistent) | MCP (Model Context Protocol) native |

---

## Architecture

```
Control Plane (FastAPI + LangGraph)
├── Goal Interpreter (Architect)   → Natural language → JSON DAG
├── Stateful Orchestrator          → Drives DAG lifecycle, checkpoints, HITL
├── MCP Gateway                    → Bridge to any MCP-compliant tool server
└── WebSocket Event Bus            → Live push to frontend

Execution Plane (Docker)
└── Steel-Box Worker Container     → Isolated, transient, air-gapped by default
    ├── web_search, scraper
    ├── filesystem_read/write
    ├── python_interpreter
    ├── gmail_draft
    └── mcp_generic
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 + React Flow (live DAG canvas) |
| Backend | Python 3.12 + FastAPI + LangGraph |
| Execution | Docker Python SDK (transient containers) |
| State | SQLite (plan state + checkpoints) |
| Memory | ChromaDB (vector memory, local) |
| Tools | MCP (Model Context Protocol) native |

---

## Quick Start

### 1. Prerequisites

- Python 3.12+
- Node.js 20+
- Docker (for sandboxed execution)
- An OpenAI API key

### 2. Backend

```bash
# Copy and edit environment variables
cp env.example .env
# Add your OPENAI_API_KEY

# Start backend
./scripts/start_backend.sh
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

### 3. Frontend

```bash
./scripts/start_frontend.sh
# → http://localhost:3000
```

### 4. Build the Worker Image (for sandboxed execution)

```bash
./scripts/build_worker.sh
```

---

## How It Works

### The "Architect" Pattern

Instead of an unbounded LLM loop, AMSAB forces the model to **commit to a plan** before executing:

1. **Goal** → "Research top 3 AI agents in 2026 and email me a summary"
2. **Architect** → Generates a 5-node DAG (JSON), visible instantly in the UI
3. **User Review** → See all steps on the visual board, click **"Approve All"**
4. **Worker** → Executes node-by-node in isolated Docker containers
5. **Checkpoint** → If node 3 fails, resume from node 3 — not node 1

### Human-in-the-Loop (HITL) Gates

Any tool marked as `risk_level: high` (e.g. `gmail.send`, `filesystem.delete`) triggers a **hard stop**:
- The dashboard shows a **Permission Card** with the agent's proposed action
- You can edit the args inline before approving
- Or skip the node entirely

### Time-Travel Debugging

Click any **completed or failed** node → "Rewind & Retry from here":
- Forks the plan into a new branch
- Resets the node and all downstream nodes
- You can change args, tools, or the prompt to compare outcomes

---

## Project Structure

```
AMSAB/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings (reads from .env)
│   ├── database.py          # SQLite persistence
│   ├── core/
│   │   ├── architect.py     # Goal → DAG (LLM Planner)
│   │   ├── orchestrator.py  # DAG execution + HITL + checkpoints
│   │   ├── executor.py      # Docker sandbox runner
│   │   └── mcp_gateway.py   # MCP tool server client
│   ├── models/
│   │   ├── task_graph.py    # TaskGraph, TaskNode, RiskLevel
│   │   └── state.py         # PlanRow, WsEvent, response schemas
│   └── api/routes/
│       ├── goals.py         # REST endpoints
│       ├── ws.py            # WebSocket endpoint
│       └── mcp.py           # MCP server management
├── frontend/
│   └── src/
│       ├── app/             # Next.js app router
│       ├── components/
│       │   ├── Dashboard.tsx        # Main C2 interface
│       │   ├── LiveGraph.tsx        # React Flow DAG canvas
│       │   ├── NodeInspector.tsx    # Deep-dive panel + HITL gate
│       │   ├── SandboxTerminal.tsx  # Live Docker logs
│       │   ├── ContextHeatmap.tsx   # Token usage widget
│       │   └── ThreadNavigator.tsx  # Plan/branch tabs
│       └── lib/
│           ├── api.ts               # REST client
│           └── websocket.ts         # WS client with reconnect
├── docker/worker/
│   ├── Dockerfile           # Minimal Python worker image
│   └── requirements.txt
├── scripts/
│   ├── start_backend.sh
│   ├── start_frontend.sh
│   └── build_worker.sh
├── requirements.txt
└── env.example
```

---

## 30-Day MVP Roadmap

| Phase | Days | Goal |
|---|---|---|
| 1 | 1–10 | Core Infrastructure: Container Orchestrator + MCP Gateway + State Schema |
| 2 | 11–20 | Architect & Logic: Planner + Executor + Checkpoint System |
| 3 | 21–30 | Visual Dashboard: Live React Flow + HITL Gate + Time-Travel UI |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/goals` | Submit a goal → returns a draft DAG |
| `GET` | `/api/plans` | List all plans |
| `GET` | `/api/plans/{id}` | Get plan + DAG state |
| `POST` | `/api/plans/{id}/approve` | Approve & start execution |
| `POST` | `/api/plans/{id}/nodes/{nid}/approve` | HITL: approve or skip a node |
| `POST` | `/api/plans/{id}/nodes/{nid}/rewind` | Time-travel: fork from a node |
| `GET` | `/api/plans/{id}/logs` | Get execution logs |
| `WS` | `/ws/plans/{id}` | Live events stream |
| `POST` | `/api/mcp/servers` | Register an MCP tool server |
| `GET` | `/api/mcp/servers/{name}/tools` | List tools on an MCP server |
