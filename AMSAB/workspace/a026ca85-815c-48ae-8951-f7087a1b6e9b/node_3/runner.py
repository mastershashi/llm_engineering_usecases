# AMSAB Worker — auto-generated runner
# Task: generate business plan outline
# Tool: python_interpreter
import json, sys, os

ARGS = {
  "code": "import base64 as _b64\nnode_2_output = _b64.b64decode(\"eyJzdGF0dXMiOiAib2siLCAib3V0cHV0IjogIlJlc3RhdXJhbnQgSW5kdXN0cnkgSW5zaWdodHM6XG57XCJzdGF0dXNcIjogXCJva1wiLCBcIm91dHB1dFwiOiBcInJlc3RhdXJhbnQgaW5kdXN0cnkgdHJlbmRzLCBzdGF0aXN0aWNzLCBhbmQgYmVzdCBwcmFjdGljZXMgYXQgRHVja0R1Y2tHbyAmbmJzcDsgRHVja0R1Y2tHbyAmbmJzcDsgQWxsIFJlZ2lvbnMgQXJnZW50aW5hIEF1c3RyYWxpYSBBdXN0cmlhIEJlbGdpdW0gKGZyKSBCZWxnaXVtIChubCkgQnJhemlsIEJ1bGdhcmlhIENhbmFkYSAoZW4pIENhbmFkYSAoZnIpIENhdGFsb25pYSBDaGlsZSBDaGluYSBDb2xvbWJpYSBDcm9hdGlhIEN6ZWNoIFJlcHVibGljIERlbm1hcmsgRXN0b25pYSBGaW5sYW5kIEZyYW5jZSBHZXJtYW55IEdyZWVjZSBIb25nIEtvbmcgSHVuZ2FyeSBJY2VsYW5kIEluZGlhIChlbikgSW5kb25lc2lhIChlbikgSXJlbGFuZCBJc3JhZWwgKGVuKSBJdGFseSBKYXBhbiBLb3JlYSBMYXR2aWEgTGl0aHVhbmlhIE1hbGF5c2lhIChlbikgTWV4aWNvIE5ldGhlcmxhbmRzIE5ldyBaZWFsYW5kIE5vcndheSBQYWtpc3RhbiAoZW4pIFBlcnUgUGhpbGlwcGluZXMgKGVuKSBQb2xhbmQgUG9ydHVnYWwgUm9tYW5pYSBSdXNzaWEgU2F1ZGkgQXJhYmlhIFNpbmdhcG9yZSBTbG92YWtpYSBTbG92ZW5pYSBTb3V0aCBBZnJpY2EgU3BhaW4gKGNhKSBTcGFpbiAoZXMpIFN3ZWRlbiBTd2l0emVybGFuZCAoZGUpIFN3aXR6ZXJsYW5kIChmcikgVGFpd2FuIFRoYWlsYW5kIChlbikgVHVya2V5IFVTIChFbmdsaXNoKSBVUyAoU3BhbmlzaCkgVWtyYWluZSBVbml0ZWQgS2luZ2RvbSBWaWV0bmFtIChlbikgQW55IFRpbWUgUGFzdCBEYXkgUGFzdCBXZWVrIFBhc3QgTW9udGggUGFzdCBZZWFyICZuYnNwOyAmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsgJm5ic3A7IDEuJm5ic3A7IFBERiBTdGF0ZSBvZiBUaGUgUmVzdGF1cmFudCBJbmR1c3RyeSAyMDI1ICZuYnNwOyZuYnNwOyZuYnNwOyBUaGUgQXNzb2NpYXRpb24mI3gyNztzIHJlc2VhcmNoIGlzIGNvbnNpZGVyZWQgdGhlIHNvdXJjZSBmb3IgcmVzdGF1cmFudCBpbmR1c3RyeSBzYWxlcyBwcm9qZWN0aW9ucyBhbmQgSXQgaXMgYmFzZWQgb24gYW5hbHlzaXMgb2YgdGhlIGxhdGVzdCBlY29ub21pYyBkYXRhIGV4dGVuc2l2ZSBzdXJ2ZXlzIG9mIHJlc3RhdXJhbnQgb3BlcmF0b3JzIGFuZCAmbmJzcDsmbmJzcDsmbmJzcDsgZ28ucmVzdGF1cmFudC5vcmcvcnMvMDc4LVpMQS00NjEvaW1hZ2VzL1NPSS0yMDI1LVJlcG9ydC5wZGY/dmVyc2lvbj0wICZuYnNwOyAmbmJzcDsgMi4mbmJzcDsgVGhlIHRvcCByZXN0YXVyYW50IGluZHVzdHJ5IHRyZW5kcyBmb3IgMjAyNiB8IE1jS2luc2V5ICZuYnNwOyZuYnNwOyZuYnNwOyBBIG5ldyBkZXRhaWxlZCBNY0tpbnNleSBhbmFseXNpcyBsb29rcyBhdCB0aGUgbGF0ZXN0IHJlc3RhdXJhbnQgaW5kdXN0cnkgdHJlbmRzIHRoYXQgYXJlIHBvaXNlZCB0byByZXNoYXBlIHRoZSBjb25zdW1lciBsYW5kc2NhcGUgaW4gMjAyNiBhbmQgYmV5b25kLiAmbmJzcDsmbmJzcDsmbmJzcDsgd3d3Lm1ja2luc2V5LmNvbS9pbmR1c3RyaWVzL3JldGFpbC9vdXItaW5zaWdodHMvd2hhdC11cy1jb25zdW1lcnMtd2FudC1mcm9tLXJlc3RhdXJhbnRzLWluLTIwMjYgJm5ic3A7ICZuYnNwOyAzLiZuYnNwOyAzMCsgUmVzdGF1cmFudCBJbmR1c3RyeSBUcmVuZHMgYW5kIFN0YXRpc3RpY3MgLSBTY290dG1heC5jb20gJm5ic3A7Jm5ic3A7Jm5ic3A7IEZhY3QgY2hlY2tlZCB8IFRoZSByZXN0YXVyYW50IGluZHVzdHJ5IGlzIHBvaXNlZCBmb3Igc2lnbmlmaWNhbnQgZ3Jvd3RoIGluIHJlY2VudCB5ZWFycywgd2l0aCBzYWxlcyBwcm9qZWN0ZWQgdG8gcmVhY2ggJDEuNSB0cmlsbGlvbiBhbmQgZW1wbG95bWVudCBleHBlY3RlZCB0byBpbmNyZWFzZSBieSAyMDAsMDAwIGpvYnMsIHRvdGFsaW5nIDE1LjkgbWlsbGlvbiB3b3JrZXJzIG5hdGlvbndpZGUuIFRoaXMgZ3Jvd3RoIGlzIGRyaXZlbiBieSBzdHJvbmcgY29uc3VtZXIgZGVtYW5kIGFuZCBhIGZvY3VzIG9uIGVuaGFuY2luZyBkaW5pbmcgZXhwZXJpZW5jZXMgdGgifQ==\").decode()\ndata = node_2_output\nprint('Business Plan Outline:')\nprint(data[:3000])"
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
