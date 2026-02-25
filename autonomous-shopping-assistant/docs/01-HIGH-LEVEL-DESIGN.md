# Autonomous Personal Shopping Assistant — High Level Design (HLD)

## 1. Executive Summary

An **Autonomous Personal Shopping Assistant** is an AI-powered system that helps users discover products, compare options, manage preferences, and complete purchases with minimal friction. The system uses **multi-agent orchestration**, **LLM reasoning**, and **distributed SaaS** architecture to deliver a complete end-to-end shopping experience.

---

## 2. System Goals

| Goal | Description |
|------|-------------|
| **Personalization** | Learn user preferences, budget, and past behavior to tailor recommendations. |
| **Autonomy** | Proactively suggest, reorder, or complete tasks (e.g., restock, price-drop alerts). |
| **Multi-channel** | Support voice, chat, and API integrations (web, mobile, third-party apps). |
| **Trust & Safety** | Transparent decisions, consent for purchases, and secure handling of PII and payments. |
| **Scalability** | Distributed, multi-tenant SaaS suitable for B2B and B2C. |

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Web App    │  │  Mobile App  │  │   Voice UI   │  │   API / SDK  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼─────────────────┼─────────────────┼─────────────────┼──────────────────┘
          │                 │                 │                 │
          └─────────────────┴────────┬────────┴─────────────────┘
                                      │
┌─────────────────────────────────────┼─────────────────────────────────────────────┐
│                           API GATEWAY / EDGE                                        │
│  Auth │ Rate Limit │ Routing │ API Versioning                                       │
└─────────────────────┬─────────────────────────────────────────────────────────────┘
                       │
┌──────────────────────┼─────────────────────────────────────────────────────────────┐
│                      │         CORE PLATFORM (SaaS)                                  │
│  ┌───────────────────▼───────────────────┐  ┌─────────────────────────────────────┐ │
│  │         ORCHESTRATION SERVICE         │  │      USER & TENANT SERVICE          │ │
│  │  (Session, Intent, Workflow Routing)   │  │  Identity, Preferences, Tenancy     │ │
│  └───────────────────┬───────────────────┘  └─────────────────────────────────────┘ │
│                      │                                                              │
│  ┌───────────────────▼───────────────────┐  ┌─────────────────────────────────────┐ │
│  │         AGENT SERVICE (Dedicated)      │  │      COMMERCE & CATALOG SERVICE    │ │
│  │  Multi-Agent Runtime │ Planner │ Tools │  │  Products, Search, Cart, Checkout   │ │
│  └───────────────────┬───────────────────┘  └─────────────────────────────────────┘ │
│                      │                                                              │
│  ┌───────────────────▼───────────────────┐  ┌─────────────────────────────────────┐ │
│  │         MEMORY & CONTEXT SERVICE       │  │      NOTIFICATION & EVENTS           │ │
│  │  User Memory, Session, History         │  │  Alerts, Webhooks, Async Jobs        │ │
│  └───────────────────────────────────────┘  └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                       │
┌──────────────────────┼─────────────────────────────────────────────────────────────┐
│                      │         DATA & EXTERNAL LAYER                                │
│  ┌───────────────────▼───────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │   LLM / Embedding APIs    │  │   Vector DB  │  │  Relational  │  │  Message   │ │
│  │   (OpenAI, Claude, etc.)  │  │   (RAG)     │  │     DB       │  │   Queue    │ │
│  └───────────────────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│  ┌───────────────────────────┐  ┌──────────────┐                                    │
│  │   External Merchants /    │  │   Payment &  │                                    │
│  │   Product Catalogs (APIs) │  │   Fulfillment│                                    │
│  └───────────────────────────┘  └──────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Core Subsystems

### 4.1 Orchestration Service
- **Role**: Entry point for “conversation” or “task”; maintains session and routes to Agent Service.
- **Responsibilities**: Auth, tenant resolution, intent classification (high-level), session lifecycle, workflow idempotency.

### 4.2 Agent Service (Dedicated)
- **Role**: Hosts all AI agents and tool execution.
- **Responsibilities**: Multi-agent planning, tool calls (search, cart, checkout, external APIs), LLM calls, reasoning traces, guardrails.

### 4.3 User & Tenant Service
- **Role**: Identity, profiles, preferences, and multi-tenancy (org/workspace).
- **Responsibilities**: User CRUD, preference store, tenant config, feature flags.

### 4.4 Commerce & Catalog Service
- **Role**: Product catalog, search, cart, orders, and (optionally) checkout.
- **Responsibilities**: Product ingestion, search (keyword + vector), cart/order APIs used by agents as tools.

### 4.5 Memory & Context Service
- **Role**: Persistent and session-scoped memory for the assistant.
- **Responsibilities**: User memory (facts, preferences), session history, RAG over past interactions and catalog.

### 4.6 Notification & Events Service
- **Role**: Async notifications, webhooks, and event-driven flows.
- **Responsibilities**: Price alerts, restock, order status, proactive suggestions; event bus (e.g., Kafka/SQS).

---

## 5. Data Flow (End-to-End)

1. **User** sends a request (e.g., “Find me running shoes under $100”) via any client.
2. **API Gateway** authenticates, rate-limits, and forwards to **Orchestration Service**.
3. **Orchestration** resolves tenant/user, creates or resumes **session**, and calls **Agent Service** with session context.
4. **Agent Service**:
   - Plans (e.g., search → compare → recommend),
   - Calls **Commerce/Catalog** (search, filters),
   - Calls **Memory** for user preferences and history,
   - Uses **LLM** for reasoning and response generation,
   - Returns structured response (message + suggested actions/cards).
5. **Orchestration** persists session state if needed and returns response to client.
6. **Notification Service** may trigger async jobs (e.g., “notify when price drops”) and emit events.

---

## 6. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Agent hosting** | Dedicated Agent Service | Isolates LLM/tool usage, enables scaling and versioning of agents independently. |
| **Multi-agent** | Planner + specialist agents (Search, Compare, Cart, Recommend) | Clear separation of concerns; easier to add tools and guardrails per agent. |
| **State** | Session in Orchestration; long-term memory in Memory Service | Clean separation; memory can be shared across sessions. |
| **Commerce** | Separate Commerce/Catalog service | Reusable by non-agent clients; clear ownership of product/cart/order data. |
| **Multi-tenancy** | Tenant ID in all requests; tenant-scoped data | Required for SaaS; enables per-tenant catalog and config. |

---

## 7. Non-Functional Requirements (NFRs)

- **Latency**: P95 < 3s for agent response (excluding external catalog latency).
- **Availability**: 99.9% for critical paths (orchestration + agent + commerce).
- **Security**: Encryption at rest and in transit; PII and payment data isolated and compliant (e.g., PCI scope reduction).
- **Scalability**: Horizontal scaling of Agent Service and Orchestration; async for notifications and heavy jobs.

---

## 8. Out of Scope (HLD)

- Detailed API contracts (see LLD).
- Specific LLM or vector DB vendor (abstracted behind interfaces).
- Detailed deployment topology (see System Engineering / Deployment).

---

## 9. Document Index

| Document | Purpose |
|----------|---------|
| `01-HIGH-LEVEL-DESIGN.md` | This document |
| `02-LOW-LEVEL-DESIGN.md` | APIs, data models, agent flows |
| `03-SYSTEM-ENGINEERING-REQUIREMENTS.md` | Requirement breakdown, chunks, NFRs |
| `04-EXECUTION-AND-DEPLOYMENT.md` | Phases, milestones, deployment |
| `05-AGENT-SERVICE-AND-DISTRIBUTED-SAAS.md` | Agent Service detail, multi-agent, SaaS |
