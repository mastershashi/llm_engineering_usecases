# AMSAB Worker — auto-generated runner
# Task: generate SEO-friendly meta description
# Tool: python_interpreter
import json, sys, os

ARGS = {
  "code": "import base64 as _b64\nnode_2_output = _b64.b64decode(\"eyJzdGF0dXMiOiAib2siLCAib3V0cHV0IjogIktleSBUYWtlYXdheXM6XG57XCJzdGF0dXNcIjogXCJva1wiLCBcIm91dHB1dFwiOiBcIm1vZGVybiBmdXJuaXR1cmUgZGVzaWduIGlkZWFzIGF0IER1Y2tEdWNrR28gJm5ic3A7IER1Y2tEdWNrR28gJm5ic3A7IEFsbCBSZWdpb25zIEFyZ2VudGluYSBBdXN0cmFsaWEgQXVzdHJpYSBCZWxnaXVtIChmcikgQmVsZ2l1bSAobmwpIEJyYXppbCBCdWxnYXJpYSBDYW5hZGEgKGVuKSBDYW5hZGEgKGZyKSBDYXRhbG9uaWEgQ2hpbGUgQ2hpbmEgQ29sb21iaWEgQ3JvYXRpYSBDemVjaCBSZXB1YmxpYyBEZW5tYXJrIEVzdG9uaWEgRmlubGFuZCBGcmFuY2UgR2VybWFueSBHcmVlY2UgSG9uZyBLb25nIEh1bmdhcnkgSWNlbGFuZCBJbmRpYSAoZW4pIEluZG9uZXNpYSAoZW4pIElyZWxhbmQgSXNyYWVsIChlbikgSXRhbHkgSmFwYW4gS29yZWEgTGF0dmlhIExpdGh1YW5pYSBNYWxheXNpYSAoZW4pIE1leGljbyBOZXRoZXJsYW5kcyBOZXcgWmVhbGFuZCBOb3J3YXkgUGFraXN0YW4gKGVuKSBQZXJ1IFBoaWxpcHBpbmVzIChlbikgUG9sYW5kIFBvcnR1Z2FsIFJvbWFuaWEgUnVzc2lhIFNhdWRpIEFyYWJpYSBTaW5nYXBvcmUgU2xvdmFraWEgU2xvdmVuaWEgU291dGggQWZyaWNhIFNwYWluIChjYSkgU3BhaW4gKGVzKSBTd2VkZW4gU3dpdHplcmxhbmQgKGRlKSBTd2l0emVybGFuZCAoZnIpIFRhaXdhbiBUaGFpbGFuZCAoZW4pIFR1cmtleSBVUyAoRW5nbGlzaCkgVVMgKFNwYW5pc2gpIFVrcmFpbmUgVW5pdGVkIEtpbmdkb20gVmlldG5hbSAoZW4pIEFueSBUaW1lIFBhc3QgRGF5IFBhc3QgV2VlayBQYXN0IE1vbnRoIFBhc3QgWWVhciAmbmJzcDsgJm5ic3A7Jm5ic3A7Jm5ic3A7Jm5ic3A7ICZuYnNwOyAxLiZuYnNwOyBNb2Rlcm4gTGl2aW5nIFJvb20gSWRlYXMgJm5ic3A7Jm5ic3A7Jm5ic3A7IEJyb3dzZSBtb2Rlcm4gbGl2aW5nIHJvb20gZGVjb3JhdGluZyBpZGVhcyBhbmQgZnVybml0dXJlIGxheW91dHMuIERpc2NvdmVyIGRlc2lnbiBpbnNwaXJhdGlvbiBmcm9tIGEgdmFyaWV0eSBvZiBtb2Rlcm4gbGl2aW5nIHJvb21zLCBpbmNsdWRpbmcgY29sb3IsIGRlY29yIGFuZCBzdG9yYWdlIG9wdGlvbnMuICZuYnNwOyZuYnNwOyZuYnNwOyB3d3cuaG91enouY29tL3Bob3Rvcy9tb2Rlcm4tbGl2aW5nLXJvb20taWRlYXMtcGhicjEtYnB+dF83MTh+c18yMTA1ICZuYnNwOyAmbmJzcDsgMi4mbmJzcDsgMTcgTXVzdC1TZWUgTW9kZXJuIEludGVyaW9yIERlc2lnbiBJZGVhcyBmb3IgYSBTb3BoaXN0aWNhdGVkIExvb2sgJm5ic3A7Jm5ic3A7Jm5ic3A7IE1vZGVybiBpbnRlcmlvciBkZXNpZ24gZm9jdXNlcyBvbiBjbGVhbiBsaW5lcywgZnVuY3Rpb25hbGl0eSwgYW5kIG5hdHVyYWwgbWF0ZXJpYWxzLiBEaXNjb3ZlciBtb2Rlcm4gaW50ZXJpb3IgaWRlYXMgdGhhdCBhcmUgd2FybSwgbGl2YWJsZSwgYW5kIGN1cnJlbnQuICZuYnNwOyZuYnNwOyZuYnNwOyB3d3cudGhlc3BydWNlLmNvbS9tb2Rlcm4taW50ZXJpb3ItZGVzaWduLWlkZWFzLTExNzA1NTYzICZuYnNwOyAmbmJzcDsgMy4mbmJzcDsgNzUgRGVzaWduZXItQXBwcm92ZWQgTW9kZXJuIExpdmluZyBSb29tIElkZWFzIGZvciAyMDI1ICZuYnNwOyZuYnNwOyZuYnNwOyBUaGVzZSA3NSBtb2Rlcm4gbGl2aW5nIHJvb20gaWRlYXMgZnJvbSBkZXNpZ25lciBob21lcyB3aWxsIGluc3BpcmUgeW91IHRvIHJlZnJlc2ggYW5kIHVwZGF0ZSB5b3VyIHNwYWNlIHNvIHlvdSBjYW4gYXBwcmVjaWF0ZSB5b3VyIGZhdm9yaXRlIGdhdGhlcmluZyBzcG90IGFuZXcuICZuYnNwOyZuYnNwOyZuYnNwOyB3d3cuaG91c2ViZWF1dGlmdWwuY29tL3Jvb20tZGVjb3JhdGluZy9saXZpbmctZmFtaWx5LXJvb21zL2c0Njc3NDE2NC9tb2Rlcm4tbGl2aW5nLXJvb20tZGVzaWduLWlkZWFzLyAmbmJzcDsgJm5ic3A7IDQuJm5ic3A7IDM1IE1vZGVybiBMaXZpbmcgUm9vbSBJZGVhcyBmb3IgYSBDb250ZW1wb3JhcnkgWWV0IFRpbWVsZXNzIFNwYWNlICZuYnNwOyZuYnNwOyZuYnNwOyBNb2Rlcm4gZGVzaWduIGlzIGtub3duIGZvciBpdHMgc3RyZWEifQ==\").decode()\ndata = node_2_output\nprint('Meta Description: ' + data[:200])"
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
