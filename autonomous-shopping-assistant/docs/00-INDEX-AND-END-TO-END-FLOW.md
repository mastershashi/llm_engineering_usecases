# Autonomous Personal Shopping Assistant — Design Index & End-to-End Flow

## Design Package Index

| # | Document | Purpose |
|---|----------|---------|
| 0 | **00-INDEX-AND-END-TO-END-FLOW.md** | This file: index + one-page E2E flow |
| 1 | **01-HIGH-LEVEL-DESIGN.md** | System goals, architecture, subsystems, data flow, NFRs |
| 2 | **02-LOW-LEVEL-DESIGN.md** | API contracts, data models, agent internals, sequences |
| 3 | **03-SYSTEM-ENGINEERING-REQUIREMENTS.md** | Epic → Feature → Chunk breakdown; dependency order; phases |
| 4 | **04-EXECUTION-AND-DEPLOYMENT.md** | Phase-by-phase execution, deployment topology, CI/CD |
| 5 | **05-AGENT-SERVICE-AND-DISTRIBUTED-SAAS.md** | Dedicated Agent Service, multi-agent design, SaaS scaling |

**Recommended reading order**: 0 → 1 → 2 → 3 → 4 → 5 (then use 3 and 4 for execution).

---

## End-to-End Flow (One Page)

### From User Request to Reply

```
1. User sends: "Find running shoes under $100 and add the best one to my cart"
   ↓
2. Client (Web/Mobile/Voice/API) → API Gateway (auth, rate limit) → Orchestration Service
   ↓
3. Orchestration: resolve tenant + user, get/create session, create turn, call Agent Service
   ↓
4. Agent Service:
   a. Planner: plan = [ search(running shoes, maxPrice=100), compare(top results), add_to_cart(best) ]
   b. SearchAgent: tool product_search("running shoes", maxPrice=100) → Commerce → products
   c. CompareAgent: tool get_product(ids) → rank by rating/price
   d. CartAgent: tool add_to_cart(productId=best) → Commerce updates cart
   e. Reply: "I added [Product X] to your cart. Here are the 3 I considered: ..."
   ↓
5. Orchestration: persist turn (request + response), return reply to client
   ↓
6. Client: show text + product cards + "View cart" / "Checkout"
```

### From Requirement to Deployment

```
Requirements (03)          →  Chunks (E1-C1, E2-C1, …)  →  Implement
       ↓
Execution (04)             →  Phase 1 → Phase 2 → Phase 3 → Phase 4
       ↓
Agent Service (05)          →  Planner + specialists + Tool Gateway
       ↓
Deployment (04 + 05)        →  Containers → K8s/ECS → Observability → Tenant quotas
       ↓
End-to-end complete        →  User can chat, search, cart, checkout (with confirmation),
                               alerts, voice, public API, production SaaS
```

### Requirement Chunks → End-to-End Completeness

| Phase | Chunks (summary) | E2E slice delivered |
|-------|-------------------|----------------------|
| 1 | E1 (Foundation), E2 (Orchestration + stub), E3 (Agent + tools), E4 (Catalog + Cart), E7 (Web) | Chat → search → add to cart on web |
| 2 | E3 (Planner, guardrails), E4 (Order), E5 (Memory) | Multi-step, memory, checkout with confirmation |
| 3 | E6 (Events, alerts, notifications), E7 (Voice, API/SDK) | Alerts, voice, public API |
| 4 | E8 (Containers, deploy, observability, quotas), E4 (Vector search) | Production SaaS, semantic search |

---

## Quick Reference: Services

| Service | Responsibility |
|---------|----------------|
| **API Gateway** | Auth, rate limit, routing |
| **Orchestration** | Session, turn, call Agent, persist state |
| **Agent Service** | Multi-agent (Planner + specialists), tools, LLM |
| **User & Tenant** | Identity, preferences, tenant config |
| **Commerce & Catalog** | Products, search, cart, orders |
| **Memory & Context** | User memory, session history |
| **Notification & Events** | Alerts, webhooks, async jobs |

---

## Next Steps

1. **Kick off Phase 1**: Implement E1-C1 (Tenant + User) and E1-C2 (Gateway + Auth).
2. **Repository layout**: Create folders per service (e.g. `services/orchestration`, `services/agent`, `services/commerce`, `services/memory`, `clients/web`).
3. **Runbooks**: Use `04-EXECUTION-AND-DEPLOYMENT.md` for sprint planning; use `03-SYSTEM-ENGINEERING-REQUIREMENTS.md` for backlog and acceptance criteria.
4. **Agent implementation**: Use `05-AGENT-SERVICE-AND-DISTRIBUTED-SAAS.md` for Tool Gateway and multi-agent flow; use `02-LOW-LEVEL-DESIGN.md` for exact request/response shapes.
