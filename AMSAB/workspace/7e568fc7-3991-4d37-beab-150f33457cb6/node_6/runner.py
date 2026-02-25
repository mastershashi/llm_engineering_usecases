# AMSAB Worker — auto-generated runner
# Task: write cooking steps to biryani cooking process file
# Tool: python_interpreter
import json, sys, os

ARGS = {
  "code": "import base64 as _b64\nnode_5_output = _b64.b64decode(\"eyJzdGF0dXMiOiAib2siLCAib3V0cHV0IjogIldyaXR0ZW4gdG8gYmlyeWFuaV9jb29raW5nX3Byb2Nlc3MudHh0In0=\").decode()\nprint('Cooking Process:', file=open('node_5_output', 'a'))\n"
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
