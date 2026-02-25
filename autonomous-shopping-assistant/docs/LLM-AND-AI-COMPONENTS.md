# LLM and AI Components

## What is used today

| Component | Current implementation | Role |
|-----------|------------------------|------|
| **LLM / reasoning** | **StubLLM** (no real AI) | Decides which tool to call and returns short reply text. It is **rule-based**: it pattern-matches on the last user message (e.g. "find", "cart", "checkout") and returns fixed tool calls. No API call to any external model. |
| **External search** | **MockMultiStoreSearch** | Simulates searching multiple stores with different prices. No real web search. |
| **Compare & best deal** | **compare_and_recommend()** | Pure Python: sorts offers by price (then rating) and picks the best. No ML. |
| **Tool execution** | **HttpToolGateway** | Calls Commerce/Memory/HTTP; no AI. |

So **no real LLM or external AI service is used** in the default setup. The “assistant” is a stub that uses keywords + rules and structured tools.

---

## Where the LLM fits (port)

The agent talks to the “brain” via the **`ILLMProvider`** port:

- **File:** `services/agent/application/ports.py` → `ILLMProvider`
- **Method:** `chat(messages, tools?, context?)` → `(reply_text, list[ToolCall])`

Any implementation of this interface can be swapped in (Stub, OpenAI, Claude, etc.).

---

## How to use a real LLM (OpenAI)

1. Set environment variables:
   - **`LLM_BACKEND=openai`**
   - **`OPENAI_API_KEY=sk-...`** (your OpenAI API key)
   - Optional: **`OPENAI_MODEL=gpt-4o`** (default is `gpt-4o-mini`)
2. Restart the Agent service. It will use **OpenAILLM** (`services/agent/infrastructure/llm/openai_llm.py`), which calls the OpenAI API and parses tool calls from the response.

With that, the **AI component** in use is **OpenAI’s API** (e.g. GPT-4o or GPT-4o-mini). No other LLM is required for the current flow.

---

## Summary

- **Default (no API key):** **StubLLM** – rule-based, no LLM, no AI.
- **With `LLM_BACKEND=openai` + `OPENAI_API_KEY`:** **OpenAI** (e.g. GPT-4) is the LLM used for chat and tool choice.
