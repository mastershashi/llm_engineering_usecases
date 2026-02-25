# Autonomous Personal Shopping Assistant — Low Level Design (LLD)

## 1. Overview

This document details APIs, data models, and internal flows for the core services. It enables implementation and integration contracts.

---

## 2. API Contracts

### 2.1 Orchestration Service — Public API

**Base path**: `POST /v1/tenants/{tenantId}/sessions`

**Request**
```json
{
  "sessionId": "optional-resume-session-uuid",
  "channel": "web|mobile|voice|api",
  "message": {
    "type": "text|voice_transcript|structured_intent",
    "payload": { "text": "Find running shoes under $100" }
  },
  "context": {
    "userId": "user-uuid",
    "locale": "en-US",
    "deviceId": "optional"
  }
}
```

**Response**
```json
{
  "sessionId": "session-uuid",
  "turnId": "turn-uuid",
  "reply": {
    "type": "text|cards|actions",
    "text": "Here are 3 options...",
    "cards": [{ "productId": "...", "title": "...", "price": 79.99, "action": "add_to_cart" }],
    "suggestedActions": ["Add to cart", "Compare", "See more"]
  },
  "state": "awaiting_input|completed|needs_confirmation"
}
```

**Other endpoints**
- `GET /v1/tenants/{tenantId}/sessions/{sessionId}` — get session state
- `DELETE /v1/tenants/{tenantId}/sessions/{sessionId}` — end session
- `POST /v1/tenants/{tenantId}/sessions/{sessionId}/confirm` — confirm autonomous action (e.g., place order)

---

### 2.2 Agent Service — Internal API (called by Orchestration)

**Base path**: `POST /v1/process`

**Request**
```json
{
  "requestId": "idempotency-key",
  "tenantId": "tenant-uuid",
  "sessionId": "session-uuid",
  "userId": "user-uuid",
  "messages": [
    { "role": "user", "content": "Find running shoes under $100" },
    { "role": "assistant", "content": "...", "toolCalls": [] }
  ],
  "context": {
    "userPreferences": { "budgetTier": "mid", "brands": [] },
    "memorySummary": "User prefers Nike; last bought in Dec 2024"
  },
  "toolsAvailable": ["product_search", "add_to_cart", "get_cart", "compare", "get_recommendations"]
}
```

**Response**
```json
{
  "reply": {
    "text": "...",
    "toolResults": [{ "tool": "product_search", "resultSummary": "3 products" }],
    "structured": { "cards": [], "actions": [] }
  },
  "toolCalls": [{ "tool": "product_search", "args": { "query": "running shoes", "maxPrice": 100 } }],
  "state": "completed|tool_calls|needs_confirmation",
  "traceId": "for-debugging"
}
```

Agent Service may be called in a loop by Orchestration until `state: completed` or `needs_confirmation`.

---

### 2.3 Commerce & Catalog Service — Internal / Tool API

Used by Agent Service (as tools) and optionally by clients directly.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/tenants/{tenantId}/products/search?q=&category=&maxPrice=&limit=` | Product search |
| GET | `/v1/tenants/{tenantId}/products/{productId}` | Product detail |
| GET | `/v1/tenants/{tenantId}/cart` | Get cart |
| POST | `/v1/tenants/{tenantId}/cart/items` | Add to cart |
| DELETE | `/v1/tenants/{tenantId}/cart/items/{itemId}` | Remove from cart |
| POST | `/v1/tenants/{tenantId}/orders` | Create order (checkout) |
| GET | `/v1/tenants/{tenantId}/orders/{orderId}` | Order status |

---

### 2.4 Memory & Context Service — Internal API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/tenants/{tenantId}/users/{userId}/memory` | Get user memory summary + facts |
| POST | `/v1/tenants/{tenantId}/users/{userId}/memory` | Upsert facts/preferences |
| GET | `/v1/tenants/{tenantId}/sessions/{sessionId}/history` | Session message history |
| POST | `/v1/tenants/{tenantId}/sessions/{sessionId}/history` | Append turn |

---

## 3. Data Models

### 3.1 Tenant
```
TenantId (PK), Name, Config (JSON: defaultLocale, allowedChannels, agentVersion), CreatedAt
```

### 3.2 User (per tenant)
```
UserId (PK), TenantId (FK), ExternalId, DisplayName, Preferences (JSON), CreatedAt, UpdatedAt
```

### 3.3 Session
```
SessionId (PK), TenantId (FK), UserId (FK), Channel, State (active|ended), Metadata (JSON), CreatedAt, LastActivityAt
```

### 3.4 Turn (per session)
```
TurnId (PK), SessionId (FK), RequestPayload (JSON), ResponsePayload (JSON), AgentTraceId, CreatedAt
```

### 3.5 Product (per tenant)
```
ProductId (PK), TenantId (FK), ExternalId, Title, Description, Category, Price, Attributes (JSON), Embedding (vector), CreatedAt
```

### 3.6 Cart
```
CartId (PK), TenantId (FK), UserId (FK), Items (JSON or separate CartItem table), UpdatedAt
```

### 3.7 Order
```
OrderId (PK), TenantId (FK), UserId (FK), CartId (FK), Status, TotalAmount, PaymentRef, CreatedAt
```

### 3.8 User Memory
```
UserId (PK), TenantId (PK), Facts (JSON or key-value), Preferences (JSON), UpdatedAt
```

---

## 4. Agent Service — Internal Design

### 4.1 Agent Types (Multi-Agent)

| Agent | Responsibility | Tools |
|-------|----------------|-------|
| **Planner** | Decompose user goal into steps; choose which specialist to call | None (or meta-tools) |
| **SearchAgent** | Query catalog, apply filters | product_search, get_product |
| **CompareAgent** | Compare products on attributes | product_search, get_product |
| **CartAgent** | Add/remove/update cart | get_cart, add_to_cart, remove_from_cart |
| **RecommendAgent** | Personalized recommendations | get_recommendations (uses memory + catalog) |
| **CheckoutAgent** | Confirm order, payment intent | create_order, get_order |

### 4.2 Tool Execution Flow

1. Planner produces a plan: e.g., `[SearchAgent(query), CompareAgent(ids), CartAgent(add)]`.
2. Orchestrator (inside Agent Service) runs each step; each agent can call tools.
3. Tool calls are executed via **Tool Gateway** that routes to Commerce, Memory, or external APIs.
4. Results are fed back into the LLM for the next step or final reply.
5. Guardrails: no tool call with `create_order` without explicit user confirmation flag in context.

### 4.3 LLM Usage

- **Planner**: One LLM call per “plan” (or per step if iterative).
- **Specialist agents**: One or more LLM calls for reasoning + tool choice + response.
- **Abstraction**: Use a common `LLMProvider` interface (OpenAI, Claude, etc.) and prompt templates per agent.

---

## 5. Sequence Diagram — Single Turn (Search + Recommend)

```
User          Gateway    Orchestration    AgentService    Commerce    Memory
  |               |              |                |             |         |
  |-- request --->|              |                |             |         |
  |               |-- forward -->|                |             |         |
  |               |              |-- process -----|             |         |
  |               |              |                |-- search ---|         |
  |               |              |                |<-- results -|         |
  |               |              |                |-- get memory -------->|
  |               |              |                |<-- summary ----------|
  |               |              |                | (LLM reply)         |
  |               |              |<-- reply ------|             |         |
  |               |<-- response -|                |             |         |
  |<-- reply ------|              |                |             |         |
```

---

## 6. Error Handling and Idempotency

- **Orchestration**: All mutations (session update, turn persist) keyed by `sessionId` + `turnId`; idempotent by `requestId` for duplicate requests.
- **Agent Service**: `requestId` used for idempotency; timeouts (e.g., 30s) with graceful degradation (e.g., return partial reply).
- **Commerce**: Cart/order APIs idempotent via client-supplied idempotency keys where applicable.

---

## 7. Security (LLD)

- All service-to-service calls use internal auth (e.g., JWT or service account).
- PII and payment data never logged in agent traces; only IDs and non-sensitive metadata.
- Tool Gateway validates tenant and user scope for every Commerce/Memory call.

---

## 8. Document Index

- **HLD**: `01-HIGH-LEVEL-DESIGN.md`
- **LLD**: This document
- **Requirements & chunks**: `03-SYSTEM-ENGINEERING-REQUIREMENTS.md`
- **Execution & deployment**: `04-EXECUTION-AND-DEPLOYMENT.md`
- **Agent Service & SaaS**: `05-AGENT-SERVICE-AND-DISTRIBUTED-SAAS.md`
