# Autonomous Personal Shopping Assistant

AI-powered personal shopping assistant with **multi-agent orchestration**, **LLM reasoning**, and **distributed SaaS** design. Supports discovery, comparison, cart, checkout, and proactive actions (e.g., price alerts).

---

## What it can do

| Capability | Description |
|------------|-------------|
| **Search over the internet** | Ask e.g. “Find running shoes” or “Wireless earbuds”. The system searches **multiple (simulated) stores** and returns offers with different prices. |
| **Compare and best deal** | Results are compared; the assistant recommends the **best deal** (lowest price, then rating) and shows reasoning (e.g. “Best deal: BestDeal at $72.50”). |
| **Add best to cart** | Say “Add the best one to my cart” (or use the button). The chosen offer is added to your cart. |
| **View cart** | Ask “What’s in my cart?” to see current items. |
| **Checkout** | Say “Checkout” to create an order from your cart. |
| **Payment** | Say “Pay” after checkout; the order is marked paid (mock today; Stripe can be wired for real payment). |
| **Conversation memory** | Session is kept so “Add the best one” uses the last search’s best deal. |
| **Chat UI** | Web UI at the Gateway URL: prompts, product cards with store name and “Best deal” badge, suggestions (Find running shoes, Add best to cart, Checkout). |
| **API-only** | All actions via REST (e.g. `POST /v1/tenants/{tenant_id}/sessions` with message payload). |

**Seeded products (dev):** Running shoes (3), Wireless earbuds, Yoga mat — so you can try search and cart without loading data.

### Internet search, compare, best deal, then pay

The assistant is built to **search across multiple sources**, **compare prices**, **recommend the best deal**, and **complete payment**:

1. **Search over the internet** – You say e.g. “Find running shoes”. The agent uses **external search** (mock: multiple simulated stores with different prices; production: plug in real APIs or scrapers).
2. **Compare and best deal** – Results from several “stores” are compared; the assistant picks the **best deal** (lowest price, then rating) and shows it with a **Best deal** badge and reasoning (e.g. “Best deal: BestDeal at $72.50”).
3. **Add to cart** – You say “Add the best one to my cart” (or use the suggestion). The chosen offer is added to your cart (external offer: title, price, source).
4. **Checkout and payment** – You say “Checkout”. The assistant creates an order from your cart. You then say “Pay” (or use the Pay button); **payment** is confirmed (mock: order marked paid; production: integrate Stripe/real provider).

So the flow is: **search → compare → best choice → add to cart → checkout → pay**.

### Your prompt = search query (no hardcoded response)

Whatever you type is used as the **search query** and **filters**:

- “Find **laptops**” → searches for **laptops**
- “**Wireless headphones** under **$100**” → searches for wireless headphones and only shows results under $100
- “**Running shoes**”, “**yoga mat**”, “**gaming laptop**” → each returns different products

The assistant parses your message to extract the product name and any “under $X” / “below X” price limit, then searches and filters by that. So changing your prompt changes the results.

### Real web search (products listed online)

By default the app uses a **mock** catalog (simulated stores) so it works without any API key. To search **real products on the web** (Google Shopping):

1. Get an API key from [SerpAPI](https://serpapi.com/) (they have a free tier).
2. Set: `export SERPAPI_KEY=your_key`
3. Restart the Agent service. It will call SerpAPI’s Google Shopping API and show live product results from the web. If the API returns no results, the app falls back to the mock catalog.

---

## How to run it

### Prerequisites

- **Python 3.11+**
- Project root: `autonomous-shopping-assistant/` (inside `llm_engineering_usecases`)

### 1. Create virtualenv and install dependencies

```bash
cd autonomous-shopping-assistant
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Or use the script:

```bash
./scripts/setup_venv.sh
source .venv/bin/activate
```

### 2. Set environment

```bash
export PYTHONPATH=$(pwd)    # or: export PYTHONPATH=/path/to/autonomous-shopping-assistant
export ENV=dev
```

### 3. Start all five services

Run each command in its own terminal (or use Option B below).

**Terminal 1 – Orchestration**
```bash
uvicorn services.orchestration.main:app --port 8000 --reload
```

**Terminal 2 – Commerce**
```bash
uvicorn services.commerce.main:app --port 8001 --reload
```

**Terminal 3 – Memory**
```bash
uvicorn services.memory.main:app --port 8002 --reload
```

**Terminal 4 – Agent**
```bash
uvicorn services.agent.main:app --port 8003 --reload
```

**Terminal 5 – Gateway (API + UI)**
```bash
uvicorn services.gateway.main:app --port 8080 --reload
```

Use the venv’s Python if you created one: `.venv/bin/python -m uvicorn ...` (and set `PYTHONPATH`).

**Option B – run all at once**
```bash
python scripts/run_all_dev.py
# or, with venv: ./scripts/run_all_venv.sh
```
(Make sure `PYTHONPATH` is set to the project root. Stop with Ctrl+C.)

### 4. Use the app

- **Chat UI:** Open **http://localhost:8080** in a browser. Type prompts (e.g. “Find running shoes”, “Add the first one to my cart”, “What’s in my cart?”) or use the suggestion buttons.
- **API:** Send `POST` requests to `http://localhost:8080/v1/tenants/00000000-0000-0000-0000-000000000001/sessions` with a JSON body: `{"message":{"type":"text","payload":{"text":"Your prompt here"}}}`.

### 5. Quick health check

```bash
curl http://localhost:8080/health
# Expect: {"status":"ok","service":"gateway"}
```

### Port summary

| Port | Service       | Purpose                          |
|------|---------------|----------------------------------|
| 8080 | Gateway       | Entry point: API + Chat UI (/)  |
| 8000 | Orchestration | Sessions, routing to Agent      |
| 8001 | Commerce      | Products, cart, orders           |
| 8002 | Memory        | User memory, session history    |
| 8003 | Agent         | LLM + tools (search, cart)     |

---

## Design Docs (Start Here)

All design is in **`docs/`**. Read in this order for full picture:

| Document | What you get |
|----------|----------------|
| [**00-INDEX-AND-END-TO-END-FLOW.md**](docs/00-INDEX-AND-END-TO-END-FLOW.md) | Index + one-page E2E flow |
| [**01-HIGH-LEVEL-DESIGN.md**](docs/01-HIGH-LEVEL-DESIGN.md) | HLD: architecture, subsystems, data flow |
| [**02-LOW-LEVEL-DESIGN.md**](docs/02-LOW-LEVEL-DESIGN.md) | LLD: APIs, data models, agent flows |
| [**03-SYSTEM-ENGINEERING-REQUIREMENTS.md**](docs/03-SYSTEM-ENGINEERING-REQUIREMENTS.md) | Requirement chunks, epic/feature breakdown, phases |
| [**04-EXECUTION-AND-DEPLOYMENT.md**](docs/04-EXECUTION-AND-DEPLOYMENT.md) | Execution steps, deployment topology, CI/CD |
| [**05-AGENT-SERVICE-AND-DISTRIBUTED-SAAS.md**](docs/05-AGENT-SERVICE-AND-DISTRIBUTED-SAAS.md) | Dedicated Agent Service, multi-agent, SaaS scaling |

## High-Level Stack

- **Orchestration** – Session, turn, routing to Agent Service  
- **Agent Service** – Planner + specialists (Search, Compare, Cart, Recommend, Checkout), tools, LLM  
- **Commerce & Catalog** – Products, search, cart, orders  
- **Memory & Context** – User memory, session history  
- **Notification & Events** – Alerts, async jobs  

## Execution Path

1. **Phase 1 (MVP)**: Foundation → Orchestration → Agent with search/cart tools → Web client → E2E: chat → search → add to cart.  
2. **Phase 2**: Planner, Memory, Checkout, guardrails.  
3. **Phase 3**: Alerts, voice, public API.  
4. **Phase 4**: Containers, deploy, observability, tenant quotas, vector search.  

Detailed steps and checkpoints are in `docs/04-EXECUTION-AND-DEPLOYMENT.md`; requirement chunks and acceptance criteria in `docs/03-SYSTEM-ENGINEERING-REQUIREMENTS.md`.

## Repository Layout (Suggested)

```
autonomous-shopping-assistant/
├── docs/                    # Design (this package)
├── services/
│   ├── gateway/             # API Gateway
│   ├── orchestration/       # Session, turn, routing
│   ├── agent/               # Multi-agent service
│   ├── user-tenant/         # Identity, preferences
│   ├── commerce/            # Catalog, cart, orders
│   ├── memory/              # User memory, session history
│   └── notifications/      # Events, alerts
├── clients/
│   └── web/                 # Simple chat UI
└── deploy/                  # K8s/ECS/Terraform (Phase 4)
```

Implementation can follow the chunks in `03-SYSTEM-ENGINEERING-REQUIREMENTS.md` and the week-by-week plan in `04-EXECUTION-AND-DEPLOYMENT.md`.

---

## Implementation (Hexagonal Architecture)

The codebase is implemented with **hexagonal (ports & adapters)** structure per service.

### Shared kernel (`shared/`)

- **`domain/`** – Value objects (`TenantId`, `UserId`, …), exceptions.
- **`ports/`** – Interfaces: `ILogger`, `IAuthProvider`, `ICache`, `IMessageQueue`, `IUnitOfWork`.
- **`adapters/`** – Implementations:
  - **Logging**: `ConsoleLogger` (dev), `JsonLogger` (prod).
  - **Auth**: `MockAuthProvider` (dev), `JwtAuthProvider` (prod).
  - **Cache**: `MemoryCache` (dev), `RedisCache` (prod).
  - **Queue**: `MemoryQueue` (dev), `RedisQueue` (prod).
- **`config/`** – `ENV=dev` vs `ENV=prod`; `AppSettings` with DB, cache, logging, auth, queue (different per env).

### Per-service layout

Each service follows:

- **`domain/`** – Entities and value objects.
- **`application/`** – Ports (interfaces) and use cases.
- **`infrastructure/`** – Adapters: HTTP (FastAPI), persistence (SQLAlchemy with dev SQLite / prod Postgres), external clients (HTTP to other services).

### Dev vs prod

| Layer   | Dev                    | Prod                          |
|--------|-------------------------|-------------------------------|
| DB     | SQLite (single file)    | PostgreSQL (`DATABASE_URL`)   |
| Cache  | In-memory               | Redis                         |
| Queue  | In-memory               | Redis                         |
| Auth   | Mock (fixed tenant/user)| JWT                           |
| Logging| Console                 | JSON                          |

Set `ENV=dev` or `ENV=prod` (and optionally copy `env.example` to `.env.dev` / `.env.prod`).

### Run locally (dev)

From **project root** `autonomous-shopping-assistant/`:

```bash
# Install deps (from repo root or autonomous-shopping-assistant)
pip install -r requirements.txt

# Option A: run each service in a separate terminal (PYTHONPATH = project root)
export PYTHONPATH=/path/to/autonomous-shopping-assistant
export ENV=dev

uvicorn services.orchestration.main:app --port 8000 --reload
uvicorn services.commerce.main:app      --port 8001 --reload
uvicorn services.memory.main:app       --port 8002 --reload
uvicorn services.agent.main:app        --port 8003 --reload
uvicorn services.gateway.main:app      --port 8080 --reload
```

**Option B**: Run all at once (e.g. `python scripts/run_all_dev.py` from project root; requires `PYTHONPATH` set to project root).

**Entry point for clients**: `http://localhost:8080` (Gateway).

### Chat UI

Open **http://localhost:8080** in a browser to use the **Personal Shopping Assistant** chat UI:

- Type prompts like “Find running shoes under $100” or “Add the first one to my cart”.
- See assistant replies and product cards; use “Add to cart” on a card or the suggestion buttons.
- Session is kept so you can continue the conversation (e.g. “What’s in my cart?”).

The UI is a single-page app served by the Gateway at `/`; the API remains at `/v1/...` and `/health`.

**API-only example:**

```bash
curl -X POST http://localhost:8080/v1/tenants/00000000-0000-0000-0000-000000000001/sessions \
  -H "Content-Type: application/json" \
  -d '{"message":{"type":"text","payload":{"text":"Find running shoes"}}}'
```

Commerce seeds a few products on startup (dev); the agent uses a stub LLM and calls Commerce/Memory over HTTP.
