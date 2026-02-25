# AMSAB Worker — auto-generated runner
# Task: filter and rank high-gain stocks
# Tool: python_interpreter
import json, sys, os

ARGS = {
  "code": "import base64 as _b64\nnode_2_output = _b64.b64decode(\"eyJzdGF0dXMiOiAib2siLCAib3V0cHV0IjogIlNob3J0LXRlcm0gZ2FpbiBzdG9ja3MgaW4gSW5kaWE6XG57XCJzdGF0dXNcIjogXCJva1wiLCBcIm91dHB1dFwiOiBcInNob3J0IHRlcm0gZ2FpbnMgc3RvY2tzIGluZGlhIGF0IER1Y2tEdWNrR28gJm5ic3A7IER1Y2tEdWNrR28gJm5ic3A7IEFsbCJ9\").decode()\ndata = node_2_output\nprint('High-gain stocks in India:');\nfor line in data.split('\\n'): print(line[:100])"
}

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
        lines = code.split("\n")
        bad = lines[e.lineno - 1].strip() if e.lineno and e.lineno <= len(lines) else "?"
        raise SyntaxError(f"line {e.lineno}: {e.msg} — code: {bad!r}")
    with contextlib.redirect_stdout(buf):
        exec(compiled, local_vars)
    stdout = buf.getvalue().strip()
    output_var = local_vars.get("OUTPUT", "")
    result = stdout or (str(output_var) if output_var else "")
    return result if result else "(no output — add print() calls to your code)"

if __name__ == "__main__":
    try:
        result = run(ARGS)
        print(json.dumps({"status": "ok", "output": result}))
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)
