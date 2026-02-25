"""Goal Interpreter — converts natural language into a JSON DAG.

This is the "Architect" component of AMSAB. It forces the LLM to output a
structured Directed Acyclic Graph before a single execution token is spent.

Hybrid Routing:
  - Local Llama 3 (via Ollama) for fast task extraction / planning when enabled
  - GPT-4o for complex reasoning and self-correction patches
"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from openai import AsyncOpenAI

from ..config import settings
from ..models.task_graph import AVAILABLE_TOOLS, GoalRequest, GraphPatch, TaskGraph, TaskNode

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """
You are the AMSAB Architect. Your goal is to decompose a high-level user
objective into a structured, executable task graph. You do NOT execute tasks;
you design the blueprint.

Output Format: You must output STRICTLY valid JSON. No prose, no preamble.
The JSON must follow this exact schema:

{
  "goal": "string",
  "nodes": [
    {
      "id": integer,
      "task": "string",
      "tool": "tool_name",
      "args": {},
      "dependencies": [id_list],
      "risk_level": "low|high"
    }
  ],
  "expected_outcome": "string"
}

Tool Usage Rules — follow these EXACTLY:
- "web_search": Search the internet. Args: {"query": "search string"}. Returns ranked text snippets.
- "python_interpreter": Process, analyse, filter, format data. Args: {"code": "valid Python 3 script"}. The script MUST use print() to produce visible output. Reference prior node results via $node_<id>_output variable names.
- "filesystem_write": Save text to a file. Args: {"filename": "name.txt", "content": "text content here"}. The filename must be a plain string like "output.txt", never a $node reference.
- "filesystem_read": Read a file. Args: {"path": "/output/name.txt"}
- "shell_exec": Run a shell command. Args: {"command": "shell command"}
- "scraper": Fetch a specific web page. Args: {"url": "https://real.domain.com/real-path"}. NEVER invent a URL.
- "mcp_generic": ONLY for a known MCP server. Do NOT use as a catch-all.

CRITICAL RULES — VIOLATING THESE WILL CAUSE ERRORS:
1. python_interpreter "code" must be valid Python 3. Do NOT use $$ or $ prefixes in Python code. Do NOT use $variable — only $node_<id>_output is a valid reference.
2. python_interpreter code MUST call print() at least once. Without print(), output is empty.
3. python_interpreter code must be self-contained. No external packages — only Python stdlib.
4. Each statement must be on its own line. Do NOT write: print(a), print(b) — write them on separate lines.
5. NEVER use scraper with an invented URL. Use web_search for all research.
6. filesystem_write "filename" must be a plain string (e.g. "recipe.txt"), NOT a $node reference.
7. For any research task: use web_search → python_interpreter to process results.
8. Node IDs start at 1 and must be sequential integers.
9. Prefer simple 2-3 node plans: web_search → python_interpreter.

PYTHON CODE EXAMPLES — copy this style exactly:

Good code (processes $node_1_output):
"code": "data = $node_1_output\nprint('Results:')\nprint(data[:2000])"

Good code (no prior nodes):
"code": "print('Biryani recipe: rice, chicken, spices, saffron')"

BAD code — DO NOT write like this:
"code": "data = $node_1_output$$ print('x'), print(data)"   ← $$ and comma are WRONG
"code": "print $node_1_output"                               ← $ prefix in Python is WRONG
"code": "print($data[:100])"                                 ← $data is not valid

EXAMPLE — correct plan for "find biryani recipe":
{
  "goal": "find biryani recipe",
  "nodes": [
    {"id": 1, "task": "search for biryani recipe", "tool": "web_search", "args": {"query": "authentic biryani recipe ingredients steps"}, "dependencies": [], "risk_level": "low"},
    {"id": 2, "task": "extract recipe details from search results", "tool": "python_interpreter", "args": {"code": "data = $node_1_output\nprint('Biryani Recipe from search:')\nprint(data[:3000])"}, "dependencies": [1], "risk_level": "low"}
  ],
  "expected_outcome": "Biryani recipe with ingredients and cooking steps"
}
"""

_CORRECTION_PROMPT = """
Node ID {node_id} failed with error: '{error}'.
The current graph state is saved as a checkpoint.

Based on this failure, provide a Patch JSON to either:
- retry with different parameters, OR
- bypass this node with a new sub-path.

Output STRICTLY valid JSON matching this schema:
{
  "patch_nodes": [
    {
      "node_id": integer,
      "action": "retry|bypass|replace",
      "new_args": {},
      "new_tool": "optional_tool_name",
      "bypass_reason": "optional string"
    }
  ],
  "new_nodes": []
}
"""


class Architect:
    """Hierarchical planner with Hybrid Routing.

    Planning (fast, cheap): Ollama Llama3 if `use_ollama_for_planning=True`
    Self-correction patches (complex): always uses the OpenAI model.
    """

    def __init__(self) -> None:
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key)

    def _build_tool_registry(self, allowed: list[str] | None) -> str:
        tools = allowed if allowed else AVAILABLE_TOOLS
        return ", ".join(tools)

    async def plan(self, request: GoalRequest) -> TaskGraph:
        """Convert natural language goal into a TaskGraph (DAG).

        Routes to Ollama Llama3 for local-fast planning when configured,
        otherwise uses the OpenAI architect_model.
        """
        tool_registry = self._build_tool_registry(request.allowed_tools)
        permissions_note = (
            f"Enabled permissions: {', '.join(k for k, v in request.permissions.items() if v)}. "
            f"Disabled: {', '.join(k for k, v in request.permissions.items() if not v)}. "
            "Do not include tools that require disabled permissions."
        )
        user_content = (
            f"Goal: {request.goal}\n\n"
            f"Available tools: [{tool_registry}]\n"
            f"{permissions_note}"
        )

        logger.info("Architect planning goal: %s", request.goal)

        if settings.use_ollama_for_planning:
            raw = await self._plan_with_ollama(user_content)
        else:
            raw = await self._plan_with_openai(user_content)

        logger.debug("Architect raw output: %s", raw)
        data: dict[str, Any] = json.loads(raw)
        graph = TaskGraph.model_validate(data)
        graph = self._sanitize_dag(graph, request.goal)
        logger.info("Architect generated DAG with %d nodes", len(graph.nodes))
        return graph

    async def _plan_with_openai(self, user_content: str) -> str:
        response = await self._openai.chat.completions.create(
            model=settings.architect_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return response.choices[0].message.content or "{}"

    async def _plan_with_ollama(self, user_content: str) -> str:
        """Use local Llama3 via Ollama for fast, private task extraction."""
        payload = {
            "model": settings.ollama_model,
            "prompt": f"{_SYSTEM_PROMPT}\n\nUser: {user_content}\n\nOutput JSON:",
            "stream": False,
            "format": "json",
        }
        timeout = httpx.Timeout(connect=5.0, read=180.0, write=10.0, pool=5.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    f"{settings.ollama_base_url}/api/generate", json=payload
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "{}")
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {settings.ollama_base_url}. "
                "Make sure 'ollama serve' is running in a separate terminal."
            )
        except httpx.TimeoutException:
            raise RuntimeError(
                f"Ollama request timed out. The model may be overloaded. Try again."
            )

    async def patch(self, node_id: int, error: str, graph: TaskGraph) -> GraphPatch:
        """Generate a self-correction patch for a failed node.

        Always uses OpenAI (complex reasoning, not suitable for Llama3).
        """
        prompt = _CORRECTION_PROMPT.format(node_id=node_id, error=error)
        graph_context = f"Current graph:\n{graph.model_dump_json(indent=2)}"

        response = await self._openai.chat.completions.create(
            model=settings.architect_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"{graph_context}\n\n{prompt}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        raw = response.choices[0].message.content or "{}"
        return GraphPatch.model_validate_json(raw)

    @staticmethod
    def _sanitize_dag(graph: TaskGraph, goal: str) -> TaskGraph:
        """Fix common Ollama hallucinations in generated plans before execution."""
        import re as _re

        _FAKE_URL_PATTERNS = [
            r"exact[-_]?url", r"example\.com", r"placeholder", r"your[-_]?url",
            r"some[-_]?site", r"unknown", r"<url>", r"\{url\}", r"recipe[-_]?url",
            r"news[-_]?url", r"data[-_]?url", r"api[-_]?url", r"site[-_]?url",
        ]
        _FAKE_RE = _re.compile("|".join(_FAKE_URL_PATTERNS), _re.IGNORECASE)

        for node in graph.nodes:
            # Fix scraper nodes with fake/placeholder URLs → convert to web_search
            if node.tool == "scraper":
                url = node.args.get("url", "")
                if not url or _FAKE_RE.search(url) or not url.startswith("http"):
                    logger.warning("Node %d: replacing fake scraper URL %r with web_search", node.id, url)
                    node.tool = "web_search"
                    node.args = {"query": node.task}

            # Fix python_interpreter code
            if node.tool == "python_interpreter":
                code = node.args.get("code", node.args.get("script", "")).strip()
                node.args["code"] = Architect._fix_python_code(code, node.task, node.dependencies)

            # Fix filesystem_write: never use a $node_N_output reference as filename
            if node.tool == "filesystem_write":
                fname = node.args.get("filename", node.args.get("path", ""))
                if _re.search(r"\$node_\d+_output", fname) or not fname:
                    safe_name = _re.sub(r"[^a-z0-9_]", "_", node.task.lower())[:30] + ".txt"
                    node.args["filename"] = safe_name
                    logger.warning("Node %d: replaced bad filename %r with %r", node.id, fname, safe_name)

        return graph

    @staticmethod
    def _fix_python_code(code: str, task: str, deps: list) -> str:
        """Sanitize Ollama-generated Python code to remove common hallucination patterns."""
        import re as _re

        if not code:
            lines = [f"# Auto-generated fallback for: {task}", f"print('Task: {task}')"]
            for d in deps:
                lines.append(f"print('Node {d} output:', node_{d}_output[:300])")
            if not deps:
                lines.append('print("No input nodes")')
            return "\n".join(lines)

        # Fix $$ used as statement separators → newline
        code = _re.sub(r"\$\$\s*", "\n", code)
        # Remove stray $ that are NOT part of a valid $node_N_output reference
        code = _re.sub(r"\$(?!node_\d+_output)", "", code)
        # Normalize indentation: dedent the whole block so it starts at column 0
        import textwrap as _tw
        code = _tw.dedent(code).strip()

        # Fix comma-separated statements on same line: `print(a), print(b)` → two lines
        code = _re.sub(r"\),\s*print\(", ")\nprint(", code)

        # Fix print without parentheses (Python 2 style): `print "text"` → `print("text")`
        code = _re.sub(r'\bprint\s+"([^"]*)"', r'print("\1")', code)
        code = _re.sub(r"\bprint\s+'([^']*)'", r"print('\1')", code)

        # Remove backtick code fences Ollama sometimes wraps around code
        code = _re.sub(r"^```(?:python)?\s*\n?", "", code, flags=_re.MULTILINE)
        code = _re.sub(r"\n?```\s*$", "", code, flags=_re.MULTILINE)
        code = code.strip()

        # Check if code looks like plain English (no Python constructs at all)
        has_python = any(kw in code for kw in [
            "print(", "import ", "def ", " = ", "for ", "if ", "return ", "with ", "open(",
        ])
        if not has_python:
            dep_refs = ", ".join(f"node_{d}_output" for d in deps)
            return (
                f"# Auto-generated: original code was not valid Python\n"
                f"# Task: {task}\n"
                f"# Available inputs: {dep_refs or 'none'}\n"
                + (f"print(node_{deps[0]}_output[:2000])" if deps else f'print("Task: {task}")')
            )

        # If code has no print/OUTPUT, add one so the node produces visible output
        if "print(" not in code and "OUTPUT" not in code:
            dep_ref = f"node_{deps[0]}_output" if deps else '""'
            code += f"\nprint({dep_ref}[:2000] if len({dep_ref}) > 0 else 'done')" if deps else '\nprint("done")'

        # Final validation: try to compile the sanitized code (without $node refs which get injected later)
        # Replace $node_N_output with a dummy variable name for compile check
        compile_check = _re.sub(r"\$node_(\d+)_output", r"node_\1_output", code)
        try:
            compile(compile_check, "<sanitize_check>", "exec")
        except SyntaxError:
            # Code is still broken after sanitization — replace with a safe fallback
            logger.warning("Node code still has syntax error after sanitization, using fallback for: %s", task)
            if deps:
                lines = [f"# Fallback: original code had syntax errors", f"print('Task: {task}')"]
                for d in deps:
                    lines.append(f"print('Node {d} output:', node_{d}_output[:1000])")
                return "\n".join(lines)
            else:
                return f"print('Task: {task}')\nprint('No prior inputs available')"

        return code


architect = Architect()
