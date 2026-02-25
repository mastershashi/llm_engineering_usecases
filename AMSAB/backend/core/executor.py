"""Steel-Box Executor — runs tasks inside transient Docker containers.

Each task gets a fresh, isolated container that is destroyed after completion.
The container has no network access by default and only a mounted workspace dir.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import textwrap
from pathlib import Path
from typing import Any

from ..config import settings
from ..models.task_graph import TaskNode

logger = logging.getLogger(__name__)


class ExecutionResult:
    def __init__(self, output: str, exit_code: int, token_usage: int = 0):
        self.output = output
        self.exit_code = exit_code
        self.token_usage = token_usage

    @property
    def success(self) -> bool:
        return self.exit_code == 0


class SandboxExecutor:
    """Spawns a transient Docker container per task and streams output."""

    def __init__(self) -> None:
        self._workspace = Path(settings.workspace_dir)
        self._workspace.mkdir(parents=True, exist_ok=True)

    async def run_node(
        self,
        plan_id: str,
        node: TaskNode,
        context: dict[str, Any],          # outputs from completed dependency nodes
        log_callback: Any | None = None,   # async callable(str) for live log streaming
    ) -> ExecutionResult:
        """Execute a single DAG node inside a Docker sandbox."""
        task_dir = self._workspace / plan_id / f"node_{node.id}"
        task_dir.mkdir(parents=True, exist_ok=True)

        # Resolve $node_<id>_output references in args (tool-aware for safe Python substitution)
        resolved_args = self._resolve_references(node.args, context, tool=node.tool)

        # Build the runner script
        script = self._build_script(node.tool, resolved_args, node.task)
        script_path = task_dir / "runner.py"
        script_path.write_text(script)

        cmd = self._docker_command(plan_id, node.id, str(task_dir), tool=node.tool)
        logger.info("Executing node %d (%s) in sandbox: %s", node.id, node.tool, node.task)

        output_lines: list[str] = []
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            assert proc.stdout is not None

            async def _read() -> None:
                async for line in proc.stdout:  # type: ignore[union-attr]
                    decoded = line.decode(errors="replace").rstrip()
                    output_lines.append(decoded)
                    if log_callback:
                        await log_callback(decoded)

            await asyncio.wait_for(
                asyncio.gather(proc.wait(), _read()),
                timeout=settings.docker_timeout_seconds,
            )
            exit_code = proc.returncode or 0
        except asyncio.TimeoutError:
            output_lines.append(f"[AMSAB] Timeout after {settings.docker_timeout_seconds}s")
            exit_code = 124
            if proc.returncode is None:
                proc.kill()

        output = "\n".join(output_lines)
        logger.info("Node %d finished with exit_code=%d", node.id, exit_code)
        return ExecutionResult(output=output, exit_code=exit_code)

    async def kill_plan_containers(self, plan_id: str) -> None:
        """Kill Switch: terminate any running Docker containers for this plan."""
        short_id = plan_id[:8]
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "ps", "--filter", f"name=amsab-{short_id}", "--quiet",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await proc.communicate()
            container_ids = stdout.decode().strip().splitlines()
            if container_ids:
                kill_proc = await asyncio.create_subprocess_exec(
                    "docker", "kill", *container_ids,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await kill_proc.communicate()
                logger.warning(
                    "Kill switch: terminated containers %s for plan %s",
                    container_ids, plan_id,
                )
        except Exception as exc:
            logger.error("Failed to kill containers for plan %s: %s", plan_id, exc)

    # Tools that require outbound internet access (get bridge network instead of air-gap)
    _NETWORK_TOOLS: frozenset[str] = frozenset({
        "web_search", "scraper", "http_request", "mcp_generic",
    })

    def _docker_command(self, plan_id: str, node_id: int, task_dir: str, tool: str = "") -> list[str]:
        # Use bridge network for tools that need internet; air-gap everything else
        network = "bridge" if tool in self._NETWORK_TOOLS else settings.docker_network
        return [
            "docker", "run", "--rm",
            "--name", f"amsab-{plan_id[:8]}-node{node_id}",
            "--network", network,
            "--memory", "512m",
            "--cpus", "1.0",
            "--read-only",
            "--tmpfs", "/tmp:size=64m",
            "-v", f"{task_dir}:/workspace:ro",
            "-v", f"{task_dir}:/output:rw",
            "-w", "/workspace",
            settings.docker_image,
            "python", "runner.py",
        ]

    def _resolve_references(
        self, args: dict[str, Any], context: dict[str, Any], tool: str = ""
    ) -> dict[str, Any]:
        """Replace $node_<id>_output tokens with actual values from context.

        For python_interpreter code, node outputs are injected as Python string
        variables at the top of the script (node_N_output = "...") so that raw
        substitution never produces invalid Python syntax.
        """
        def _raw_sub(text: str) -> str:
            return re.sub(
                r"\$node_(\d+)_output",
                lambda m: context.get(f"node_{m.group(1)}_output", m.group(0)),
                text,
            )

        resolved: dict[str, Any] = {}
        for key, val in args.items():
            if isinstance(val, str):
                if key == "code" and tool == "python_interpreter":
                    # Inject node outputs as Python variables using base64 to guarantee
                    # no syntax errors regardless of what special characters the output contains.
                    refs = list(dict.fromkeys(re.findall(r"\$node_(\d+)_output", val)))
                    header_lines = ["import base64 as _b64"]
                    for node_id in refs:
                        output = context.get(f"node_{node_id}_output", "")
                        import base64 as _b64
                        encoded = _b64.b64encode(output.encode()).decode()
                        header_lines.append(
                            f'node_{node_id}_output = _b64.b64decode("{encoded}").decode()'
                        )
                    # Replace $node_N_output tokens with the variable names
                    code = re.sub(r"\$node_(\d+)_output", r"node_\1_output", val)
                    resolved[key] = "\n".join(header_lines + [code]) if refs else code
                else:
                    resolved[key] = _raw_sub(val)
            elif isinstance(val, list):
                resolved[key] = [_raw_sub(str(v)) if isinstance(v, str) else v for v in val]
            else:
                resolved[key] = val
        return resolved

    def _build_script(self, tool: str, args: dict[str, Any], task: str) -> str:
        """Generate the Python runner script for a given tool + args."""
        args_json = json.dumps(args, indent=2)
        tool_body = self._tool_implementations().get(tool, self._unknown_tool(tool)).rstrip()

        # Build line-by-line to avoid textwrap.dedent mis-calculating the common
        # indent prefix when multi-line f-string substitutions (args_json, tool_body)
        # contain lines with different leading whitespace.
        parts = [
            f"# AMSAB Worker — auto-generated runner",
            f"# Task: {task}",
            f"# Tool: {tool}",
            "import json, sys, os",
            "",
            f"ARGS = {args_json}",
            "",
            tool_body,
            "",
            'if __name__ == "__main__":',
            "    try:",
            "        result = run(ARGS)",
            '        print(json.dumps({"status": "ok", "output": result}))',
            "    except Exception as exc:",
            '        print(json.dumps({"status": "error", "error": str(exc)}))',
            "        sys.exit(1)",
        ]
        return "\n".join(parts) + "\n"

    @staticmethod
    def _tool_implementations() -> dict[str, str]:
        return {
            "web_search": textwrap.dedent("""\
                def run(args):
                    import urllib.request, urllib.parse, ssl, re
                    query = urllib.parse.quote_plus(args.get("query", ""))
                    # DuckDuckGo Lite works reliably without a browser session
                    url = f"https://lite.duckduckgo.com/lite/?q={query}"
                    headers = {
                        "User-Agent": "Mozilla/5.0 (compatible; AMSAB/1.0)",
                        "Accept": "text/html",
                    }
                    req = urllib.request.Request(url, headers=headers)
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
                        html = r.read().decode(errors="replace")
                    # Extract result snippets: DDG Lite wraps results in <td class="result-snippet">
                    snippets = re.findall(r'class="result-snippet"[^>]*>(.*?)</td>', html, re.DOTALL)
                    titles = re.findall(r'class="result-link"[^>]*>(.*?)</a>', html, re.DOTALL)
                    links = re.findall(r'class="result-link"[^>]*href="([^"]+)"', html)
                    if snippets:
                        results = []
                        for i, (t, s) in enumerate(zip(titles, snippets), 1):
                            t_clean = re.sub(r"<[^>]+>", "", t).strip()
                            s_clean = re.sub(r"<[^>]+>", "", s).strip()
                            url_i = links[i-1] if i-1 < len(links) else ""
                            results.append(f"{i}. {t_clean}\\n   {s_clean}\\n   {url_i}")
                        return "\\n\\n".join(results[:10])
                    # Fallback: strip all HTML
                    text = re.sub(r"<[^>]+>", " ", html)
                    text = re.sub(r"\\s+", " ", text).strip()
                    return text[:4000]
            """),
            "scraper": textwrap.dedent("""\
                def run(args):
                    import urllib.request, urllib.error, ssl, re
                    url = args.get("url", "")
                    if not url:
                        return "Error: no url provided"
                    headers = {"User-Agent": "Mozilla/5.0 (compatible; AMSAB/1.0)"}
                    req = urllib.request.Request(url, headers=headers)
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    try:
                        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
                            html = r.read().decode(errors="replace")
                    except urllib.error.HTTPError as e:
                        raise RuntimeError(f"HTTP {e.code} fetching {url}: {e.reason}")
                    except urllib.error.URLError as e:
                        raise RuntimeError(f"Cannot reach {url}: {e.reason}")
                    # Remove script/style blocks then strip remaining tags
                    html = re.sub(r"<(script|style)[^>]*>.*?</\\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
                    text = re.sub(r"<[^>]+>", " ", html)
                    text = re.sub(r"\\s+", " ", text).strip()
                    return text[:6000]
            """),
            "filesystem_read": textwrap.dedent("""\
                def run(args):
                    import os
                    path = args.get("path", "")
                    if not path:
                        return "Error: no path provided"
                    if not os.path.exists(path):
                        available = []
                        for d in ["/output", "/workspace"]:
                            if os.path.isdir(d):
                                available += [f"{d}/{f}" for f in os.listdir(d)]
                        hint = f"Available files: {available}" if available else "No files written yet."
                        return f"File not found: {path}. {hint}"
                    with open(path) as f:
                        return f.read()
            """),
            "filesystem_write": textwrap.dedent("""\
                def run(args):
                    path = args.get("filename", args.get("path", "output.txt"))
                    content = args.get("content", "")
                    with open(f"/output/{path}", "w") as f:
                        f.write(str(content))
                    return f"Written to {path}"
            """),
            "python_interpreter": textwrap.dedent("""\
                def run(args):
                    import io, contextlib, json as _json
                    code = args.get("code", args.get("script", "")).strip()
                    input_data = args.get("input", "")
                    if not code:
                        return "Error: no code provided in args"
                    buf = io.StringIO()
                    local_vars = {"INPUT": input_data, "json": _json}
                    try:
                        compiled = compile(code, "<amsab>", "exec")
                    except SyntaxError as e:
                        lines = code.split("\\n")
                        bad = lines[e.lineno - 1].strip() if e.lineno and e.lineno <= len(lines) else "?"
                        raise SyntaxError(f"line {e.lineno}: {e.msg} — code: {bad!r}")
                    with contextlib.redirect_stdout(buf):
                        exec(compiled, local_vars)
                    stdout = buf.getvalue().strip()
                    output_var = local_vars.get("OUTPUT", "")
                    result = stdout or (str(output_var) if output_var else "")
                    return result if result else "(no output — add print() calls to your code)"
            """),
            "gmail_draft": textwrap.dedent("""\
                def run(args):
                    # Stub: In production integrate with Gmail API via MCP
                    to = args.get("to", "")
                    subject = args.get("subject", "")
                    body = args.get("body", "")
                    return f"[DRAFT] To:{to} Subject:{subject}\\n{body}"
            """),
            "mcp_generic": textwrap.dedent("""\
                def run(args):
                    import json
                    server = args.get("server", "")
                    method = args.get("method", "")
                    params = args.get("params", {})
                    return f"[MCP] Would call {server}/{method} with {json.dumps(params)}"
            """),
        }

    @staticmethod
    def _unknown_tool(tool: str) -> str:
        return textwrap.dedent(f"""\
            def run(args):
                return f"[AMSAB] Tool '{tool}' is not implemented in this worker image."
        """)


executor = SandboxExecutor()
