# Autonomous Personal Shopping Assistant — Execution & Deployment

## 1. Execution Model

Execution is **phase-based**: each phase delivers a working vertical slice. Phases align with the requirement chunks in `03-SYSTEM-ENGINEERING-REQUIREMENTS.md`.

---

## 2. Phase Overview

| Phase | Goal | Duration (example) | Exit Criteria |
|-------|------|--------------------|---------------|
| **Phase 1** | MVP: Chat → Search → Cart (stub agent, then real tools) | 4–6 weeks | Web user can search products and add to cart via chat |
| **Phase 2** | Full agent: Planner, Memory, Checkout, Guardrails | 3–4 weeks | Multi-step tasks, preferences, order with confirmation |
| **Phase 3** | Async & channels: Alerts, Voice, Public API | 3–4 weeks | Price alerts, voice channel, documented API/SDK |
| **Phase 4** | Production SaaS: Deploy, observe, scale, tenant quotas | 2–3 weeks | All services in prod-like env; tracing; quotas |

---

## 3. Phase 1 — Detailed Execution

### 3.1 Week 1–2: Foundation

| Step | Task | Output |
|------|------|--------|
| 1.1 | Implement Tenant + User domain and DB schema | Tables: tenants, users |
| 1.2 | Tenant/User CRUD API (internal or admin) | POST/GET tenant, POST/GET user |
| 1.3 | API Gateway: auth (JWT/API key), rate limit, route to “orchestration” | Gateway returns 401/429/200 |
| 1.4 | Orchestration service skeleton: receive request, resolve tenant/user from token | Context with tenantId, userId |
| 1.5 | Session create/get/end; persist in DB | Session table; sessionId in response |

**Checkpoint**: Authenticated request → session created → sessionId returned.

### 3.2 Week 3–4: Turn + Agent Stub

| Step | Task | Output |
|------|------|--------|
| 2.1 | Turn model: store request + response per turn | Turn table |
| 2.2 | Orchestration: on message, create turn, call Agent Service (stub) | Stub returns “Hello, I’m your shopping assistant.” |
| 2.3 | Agent Service: HTTP API that accepts process request, returns fixed or simple LLM reply (no tools) | Agent Service deployable; Orchestration gets reply |
| 2.4 | Commerce: product catalog (seed data), GET /products/search | Search returns products |
| 2.5 | Agent Service: tool registry; product_search tool that calls Commerce | Tool gateway; product_search returns results |
| 2.6 | Agent: single “assistant” that can call product_search; LLM generates reply with products | “Find shoes” → products in reply |
| 2.7 | Cart API: get cart, add item | Cart per user |
| 2.8 | Agent: add_to_cart tool; CartAgent or single agent adds to cart | “Add first result to cart” works |
| 2.9 | Simple web client: input box, send to Orchestration, show reply + product cards | E2E: user types, sees products, adds to cart |

**Checkpoint**: End-to-end flow: Web → Gateway → Orchestration → Agent (with search + cart tools) → Commerce → Reply with cards.

---

## 4. Phase 2 — Full Agent & Memory

| Step | Task | Output |
|------|------|--------|
| 3.1 | Planner agent: input = user message, output = plan (list of steps) | Planner returns e.g. [search, add_to_cart] |
| 3.2 | Orchestrator in Agent Service: execute plan step-by-step; each step can be a specialist agent | Multi-step execution |
| 3.3 | Memory Service: user memory API (get/upsert facts, preferences) | Agent can read/write memory |
| 3.4 | Session history API; Orchestration or Agent fetches last N turns | Context includes history |
| 3.5 | Inject memory summary + history into Agent request | Replies reflect preferences |
| 3.6 | Checkout: create order API; CheckoutAgent with create_order tool | Order created from cart |
| 3.7 | Guardrails: create_order only if user confirmed; confirmation flow in Orchestration (e.g., “Confirm order?” → POST confirm) | No autonomous order without consent |
| 3.8 | RecommendAgent (optional): use memory + catalog to recommend | “Recommend something” uses preferences |

**Checkpoint**: Multi-step goal, memory-aware replies, checkout with confirmation, guardrails on.

---

## 5. Phase 3 — Async & Channels

| Step | Task | Output |
|------|------|--------|
| 4.1 | Event bus + worker: e.g., Kafka or SQS; worker process | Events published and consumed |
| 4.2 | “Alert” entity: user, product, condition (e.g., price &lt; X); job or cron checks and emits event | Alert registered and evaluated |
| 4.3 | Notification delivery (email/push) from event | User gets notification |
| 4.4 | Voice adapter: transcript → Orchestration API; reply → TTS | Voice channel works |
| 4.5 | Public API docs (OpenAPI); optional SDK (JS/Python) | External integration possible |

---

## 6. Phase 4 — Production SaaS

| Step | Task | Output |
|------|------|--------|
| 5.1 | Docker (or OCI) image per service; health check endpoint | All services containerized |
| 5.2 | Orchestrated deploy: K8s/ECS/Terraform; env-specific config (staging/prod) | One-command deploy |
| 5.3 | Logging: structured logs; correlation ID from gateway through all services | Logs queryable by request |
| 5.4 | Metrics: request count, latency (p50/p95), error rate per service and per tenant | Dashboard per service/tenant |
| 5.5 | Tracing: OpenTelemetry from gateway → orchestration → agent → commerce | Full trace for a request |
| 5.6 | Tenant quotas: rate limit and optional resource cap per tenant | Quota enforced |
| 5.7 | Vector search: product embeddings; semantic search in catalog | E4-C4 done |

---

## 7. Deployment Topology (Distributed SaaS)

```
                    [ CDN / WAF ]
                           │
                    [ API Gateway ]  (per region or global)
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    ▼                      ▼                      ▼
[ Orchestration ]   [ Agent Service ]   [ User/Tenant ]
    │                      │                      │
    │              ┌───────┴───────┐               │
    │              ▼               ▼               │
    │        [ Commerce ]    [ Memory ]            │
    │              │               │               │
    └──────────────┴───────────────┴───────────────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    ▼                      ▼                      ▼
[ PostgreSQL ]      [ Vector DB ]        [ Message Queue ]
(tenant, user,          (RAG,              (events, jobs)
 session, cart,          products)
 order)
```

- **Regions**: Deploy API Gateway + core services per region for latency; shared DB or replicated per region based on strategy.
- **Agent Service**: Scale horizontally; optional GPU pool for local embedding if needed.
- **Secrets**: Vault or cloud secret manager; no secrets in code or plain config.

---

## 8. CI/CD and Environments

| Environment | Purpose | Deploy trigger |
|-------------|---------|----------------|
| Dev | Local or shared dev; mock external APIs | On push to feature branch |
| Staging | Integration and E2E tests; production-like | On merge to main |
| Production | Live traffic | Tag or manual approval after staging green |

**Pipeline**: Build → Unit tests → Build images → Deploy to staging → E2E → (manual) Deploy to prod.

---

## 9. Rollback and Feature Flags

- **Rollback**: Previous image version retained; rollback = redeploy previous tag.
- **Feature flags**: Per tenant or global (e.g., “use_planner_agent”, “vector_search_enabled”) to toggle features without code deploy.

---

## 10. Document Index

- **HLD**: `01-HIGH-LEVEL-DESIGN.md`
- **LLD**: `02-LOW-LEVEL-DESIGN.md`
- **Requirements**: `03-SYSTEM-ENGINEERING-REQUIREMENTS.md`
- **This doc**: `04-EXECUTION-AND-DEPLOYMENT.md`
- **Agent Service & SaaS**: `05-AGENT-SERVICE-AND-DISTRIBUTED-SAAS.md`
