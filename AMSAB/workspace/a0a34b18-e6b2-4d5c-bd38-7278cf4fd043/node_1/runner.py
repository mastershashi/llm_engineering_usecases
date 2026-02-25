# AMSAB Worker — auto-generated runner
# Task: web_search
# Tool: web_search
import json, sys, os

ARGS = {
  "query": "stock performance"
}

def run(args):
    import urllib.request, urllib.parse, ssl
    query = urllib.parse.quote_plus(args.get("query", ""))
    url = f"https://html.duckduckgo.com/html/?q={query}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 AMSAB/1.0"})
    # Sandbox container lacks system CA bundle; bypass SSL verify inside the isolated container
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        html = r.read().decode(errors="replace")
    # Strip HTML tags for a clean text result
    import re
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:5000]

if __name__ == "__main__":
    try:
        result = run(ARGS)
        print(json.dumps({"status": "ok", "output": result}))
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)
