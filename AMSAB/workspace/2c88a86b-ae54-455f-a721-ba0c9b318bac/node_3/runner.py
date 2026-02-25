# AMSAB Worker — auto-generated runner
# Task: evaluate business opportunities in India
# Tool: python_interpreter
import json, sys, os

ARGS = {
  "code": "import base64 as _b64\nnode_2_output = _b64.b64decode(\"eyJzdGF0dXMiOiAib2siLCAib3V0cHV0IjogIk1hcmtldCBUcmVuZHM6XG57XCJzdGF0dXNcIjogXCJva1wiLCBcIm91dHB1dFwiOiBcIkluZGlhbiBidXNpbmVzcyB0cmVuZHMgMjAyMy0yMDI1IGF0IER1Y2tEdWNrR28gJm5ic3A7IER1Y2tEdWNrR28gJm5ic3A7IEFsbCBSZWdpb25zIEFyZ2VudGluYSBBdXN0cmFsaWEgQXVzdHJpYSBCZWxnaXVtIChmcikgQmVsZ2l1bSAobmwpIEJyYXppbCBCdWxnYXJpYSBDYW5hZGEgKGVuKSBDYW5hZGEgKGZyKSBDYXRhbG9uaWEgQ2hpbGUgQ2hpbmEgQ29sb21iaWEgQ3JvYXRpYSBDemVjaCBSZXB1YmxpYyBEZW5tYXJrIEVzdG9uaWEgRmlubGFuZCBGcmFuY2UgR2VybWFueSBHcmVlY2UgSG9uZyBLb25nIEh1bmdhcnkgSWNlbGFuZCBJbmRpYSAoZW4pIEluZG9uZXNpYSAoZW4pIElyZWxhbmQgSXNyYWVsIChlbikgSXRhbHkgSmFwYW4gS29yZWEgTGF0dmlhIExpdGh1YW5pYSBNYWxheXNpYSAoZW4pIE1leGljbyBOZXRoZXJsYW5kcyBOZXcgWmVhbGFuZCBOb3J3YXkgUGFraXN0YW4gKGVuKSBQZXJ1IFBoaWxpcHBpbmVzIChlbikgUG9sYW5kIFBvcnR1Z2FsIFJvbWFuaWEgUnVzc2lhIFNhdWRpIEFyYWJpYSBTaW5nYXBvcmUgU2xvdmFraWEgU2xvdmVuaWEgU291dGggQWZyaWNhIFNwYWluIChjYSkgU3BhaW4gKGVzKSBTd2VkZW4gU3dpdHplcmxhbmQgKGRlKSBTd2l0emVybGFuZCAoZnIpIFRhaXdhbiBUaGFpbGFuZCAoZW4pIFR1cmtleSBVUyAoRW5nbGlzaCkgVVMgKFNwYW5pc2gpIFVrcmFpbmUgVW5pdGVkIEtpbmdkb20gVmlldG5hbSAoZW4pIEFueSBUaW1lIFBhc3QgRGF5IFBhc3QgV2VlayBQYXN0IE1vbnRoIFBhc3QgWWVhciAmbmJzcDsgJm5ic3A7Jm5ic3A7Jm5ic3A7Jm5ic3A7ICZuYnNwOyAxLiZuYnNwOyBJbmRpYSBlY29ub21pYyBvdXRsb29rIHwgRGVsb2l0dGUgSW5zaWdodHMgJm5ic3A7Jm5ic3A7Jm5ic3A7IFRocm91Z2ggMjAyNCBhbmQgZWFybHkgMjAyNSAsIEluZGlhIGV4cGVyaWVuY2VkIGFuIHVuZXhwZWN0ZWQgc2xvd2Rvd24gaW4gY3JlZGl0IGdyb3d0aCwgcGFydGljdWxhcmx5IGluIHBlcnNvbmFsIGxvYW5zIGFuZCBzbWFsbC0gYnVzaW5lc3MgbGVuZGluZy4gVGhlIFJCSSByZWNvZ25pemVkIHRoYXQsIHdpdGhvdXQgc3Ryb25nZXIgY3JlZGl0IHRyYW5zbWlzc2lvbiwgY29uc3VtZXIgc3BlbmRpbmcgcmVjb3Zlcnkgd291bGQgbG9zZSBtb21lbnR1bS4gJm5ic3A7Jm5ic3A7Jm5ic3A7IHd3dy5kZWxvaXR0ZS5jb20vdXMvZW4vaW5zaWdodHMvdG9waWNzL2Vjb25vbXkvYXNpYS1wYWNpZmljL2luZGlhLWVjb25vbWljLW91dGxvb2suaHRtbCAmbmJzcDsgJm5ic3A7IDIuJm5ic3A7IFRoZSBwcm9taXNlIG9mIGludGVybmF0aW9uYWwgYnVzaW5lc3MgZ3Jvd3RoIGluIEluZGlhIHwgTWNLaW5zZXkgJm5ic3A7Jm5ic3A7Jm5ic3A7IFN1Y2Nlc3Mgc3RvcmllcyBHbG9iYWwgaW50ZXJlc3QgaW4gSW5kaWEgaXMgYWxyZWFkeSBncm93aW5nLiBGcm9tIDIwMjEgdG8gMjAyMyAsIDk4NCBpbnRlcm5hdGlvbmFsIGNvbXBhbmllcyByZWdpc3RlcmVkIHRvIG9wZXJhdGUgaW4gSW5kaWEsIHVwIGZyb20gMzIwIGJldHdlZW4gMjAxOSBhbmQgMjAyMS4gVGhlcmUgYXJlIG5vdyBvdmVyIDEsNTAwIGdsb2JhbCBjYXBhYmlsaXR5IGNlbnRlcnMgaW4gdGhlIGNvdW50cnksIGFib3V0IDYwIHBlcmNlbnQgb2Ygd2hpY2ggZm9jdXMgb24gSVQsIGJ1c2luZXNzIHByb2Nlc3MgbWFuYWdlbWVudCwgb3IgZW5naW5lZXJpbmcsIHJlc2VhcmNoLCBhbmQgZGV2ZWxvcG1lbnQuIDEyIEFuYWx5c3RzIHByZWRpY3QgdGhhdCBjb21wYW5pZXMgd2lsbCAuLi4gJm5ic3A7Jm5ic3A7Jm5ic3A7IHd3dy5tY2tpbnNleS5jb20vaW5kdXN0cmllcy9pbmR1c3RyaWFscy9vdXItaW5zaWdodHMvaW5kaWEtdGhlLXByb21pc2UtYW5kLXBvc3NpYmlsaXRpZXMtZm9yLWdsb2JhbC1jb21wYW5pZXMgJm5ic3A7ICZuYnNwOyAzLiZuYnNwOyAyMDI1IGFuZCBCZXlvbmQ6IDggQnVzaW5lc3MgVHJlbmRzIEluZGlhbiBMZWFkZXJzIE11c3QgUHJlcGFyZSBGb3IgJm5ic3A7Jm5ic3AifQ==\").decode()\ndata = node_2_output\nprint('Business Opportunities:')\nprint(data[:2000])"
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
