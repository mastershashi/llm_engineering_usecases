# Agent Service & Distributed SaaS — Deep Dive

## 1. Why a Dedicated Agent Service

- **Isolation**: LLM usage, token cost, and latency are contained in one service; rest of platform stays stable.
- **Scaling**: Scale agent workers independently (e.g., more replicas or GPU nodes for embedding).
- **Versioning**: Roll out new agent versions (prompts, models, tools) without touching Orchestration or Commerce.
- **Security**: Single place to enforce guardrails, redact PII from logs/traces, and control external API calls.
- **Multi-agent**: Clean home for Planner and specialist agents, tool registry, and execution loop.

---

## 2. Agent Service Architecture (Internal)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AGENT SERVICE                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     API Layer (HTTP/gRPC)                          │   │
│  │   /v1/process  │  /v1/health  │  /v1/tools (internal)              │   │
│  └────────────────────────────────┬────────────────────────────────┘   │
│                                   │                                      │
│  ┌────────────────────────────────▼────────────────────────────────┐   │
│  │                  Orchestrator (in-process)                        │   │
│  │   - Load context (memory, history)                                 │   │
│  │   - Call Planner → get plan                                        │   │
│  │   - For each step: run Specialist Agent → execute tools → next     │   │
│  │   - Aggregate reply and state                                      │   │
│  └────────────────────────────────┬────────────────────────────────┘   │
│                                   │                                      │
│  ┌────────────────────────────────▼────────────────────────────────┐   │
│  │   Agents (Planner, Search, Compare, Cart, Recommend, Checkout)     │   │
│  │   - Each: system prompt + tools + LLM client                      │   │
│  └────────────────────────────────┬────────────────────────────────┘   │
│                                   │                                      │
│  ┌────────────────────────────────▼────────────────────────────────┐   │
│  │                     Tool Gateway                                  │   │
│  │   - Validate tenant/user scope                                    │   │
│  │   - Route to: Commerce | Memory | External (e.g., payment)        │   │
│  │   - Timeout, retry, circuit breaker per downstream                 │   │
│  └────────────────────────────────┬────────────────────────────────┘   │
└───────────────────────────────────┼────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
   Commerce API               Memory API                  LLM / Embedding
   (products, cart,           (user memory,               (OpenAI, Claude,
    order)                      session history)           etc.)
```

---

## 3. Multi-Agent Design

### 3.1 Roles

| Agent | Input | Output | Tools |
|-------|--------|--------|-------|
| **Planner** | User message + context summary | Ordered list of steps (e.g., search → compare → add_to_cart) | — |
| **SearchAgent** | Step “search” + params | Natural language + structured product list | product_search, get_product |
| **CompareAgent** | Step “compare” + product IDs | Comparison summary | get_product |
| **CartAgent** | Step “cart” (add/remove/update) | Confirmation + cart snapshot | get_cart, add_to_cart, remove_from_cart |
| **RecommendAgent** | Step “recommend” + optional constraints | Recommendations with reasoning | get_recommendations (uses memory + catalog) |
| **CheckoutAgent** | Step “checkout” + confirmation | Order creation or error | create_order, get_order |

### 3.2 Flow

1. **Request** arrives with messages, context (memory summary, history), and allowed tools.
2. **Orchestrator** calls **Planner** once: “Given this goal, return steps.”
3. For each step:
   - Select **Specialist** (Search / Compare / Cart / Recommend / Checkout).
   - Run specialist: LLM may issue **tool calls**; **Tool Gateway** executes and returns results.
   - Optionally loop until specialist returns “done” (e.g., multiple tool rounds).
4. **Orchestrator** aggregates final reply (text + structured cards/actions) and **state** (completed / needs_confirmation).
5. **Guardrails**: If step is “checkout”, do not call create_order unless context has explicit user confirmation.

### 3.3 Tool Gateway

- **Input**: tool name + arguments + tenantId + userId + sessionId.
- **Validation**: Check tenant/user/session; validate args (e.g., productId exists, belongs to tenant).
- **Routing**: product_search, get_product, get_cart, add_to_cart, remove_from_cart → Commerce Service; get_memory, update_memory → Memory Service; create_order → Commerce (and optionally Payment provider).
- **Resilience**: Timeout (e.g., 5s per tool), retry with backoff for idempotent tools, circuit breaker per downstream.

---

## 4. Distributed SaaS Considerations

### 4.1 Multi-Tenancy

- **Tenant identity**: Every request carries tenantId (from API key or JWT). All data access is tenant-scoped.
- **Config per tenant**: Agent version, allowed tools, LLM model, feature flags stored in Tenant config (User/Tenant Service or config store).
- **Isolation**: No cross-tenant data access; optional separate DB schema or logical partition per tenant for compliance.

### 4.2 Scaling

| Component | Scale strategy |
|-----------|----------------|
| API Gateway | Horizontal; global or per-region LB |
| Orchestration | Stateless; scale with request volume |
| Agent Service | Stateless; scale with concurrent sessions; optional GPU pool for embeddings |
| Commerce / Memory | Stateless APIs; scale horizontally |
| DB | Primary + replicas; read replicas for search and history |
| Queue | Partitioned by tenant or topic; consumers scale with partitions |

### 4.3 Data Residency and Latency

- **Regions**: Deploy Orchestration + Agent + Commerce + Memory in same region; DB can be regional or global (trade-off: latency vs. consistency).
- **LLM**: Use regional endpoints if provider supports; else single region and accept latency.
- **Catalog**: Replicate or shard by tenant/region if catalog is large and region-specific.

### 4.4 Cost and Quotas

- **Per-tenant quotas**: Max requests/min, max agent calls/month, max orders/month (configurable).
- **LLM cost**: Track token usage per tenant; optional hard cap or alert when threshold exceeded.
- **Rate limiting**: At gateway and optionally at Agent Service for tool calls to Commerce to avoid abuse.

---

## 5. Agent Service Deployment Options

| Option | Use case | Pros | Cons |
|--------|----------|------|------|
| **Single deployment** | MVP, single region | Simple | No regional isolation |
| **Per-region Agent Service** | Low latency globally | Latency, data residency | More operational surface |
| **Dedicated Agent pool per tier** | Premium tenants get reserved capacity | Predictable performance | Cost and ops |
| **Serverless (e.g., Lambda)** | Variable load | Scale to zero | Cold start; state in external store |

**Recommendation**: Start with single deployment (or one per region); move to tiered pools if needed.

---

## 6. Security in Agent Service

- **Input**: Sanitize user message (e.g., prompt injection mitigation); validate tool args.
- **Output**: No PII or payment data in agent reply text; only IDs and non-sensitive metadata in traces.
- **Tool Gateway**: Every outbound call is scoped to tenant/user; no raw payment data to LLM.
- **Secrets**: LLM API keys and external API credentials in secret manager; never in code or logs.

---

## 7. Observability for Agents

- **Traces**: One trace per “process” request; spans for Planner, each specialist, each tool call, and LLM call.
- **Metrics**: Request count, latency (p50/p95), token usage, tool call count and failure rate per tenant/agent/tool.
- **Logs**: Request ID, tenant ID, session ID; no user message or PII in plain text; optional hashed or redacted for debugging.
- **Evaluations**: Optional pipeline for quality (e.g., “did the agent call the right tools?”) on sampled traffic.

---

## 8. Document Index

- **HLD**: `01-HIGH-LEVEL-DESIGN.md`
- **LLD**: `02-LOW-LEVEL-DESIGN.md`
- **Requirements**: `03-SYSTEM-ENGINEERING-REQUIREMENTS.md`
- **Execution & deployment**: `04-EXECUTION-AND-DEPLOYMENT.md`
- **This doc**: `05-AGENT-SERVICE-AND-DISTRIBUTED-SAAS.md`
