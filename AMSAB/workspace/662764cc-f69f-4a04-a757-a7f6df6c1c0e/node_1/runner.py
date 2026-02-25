# AMSAB Worker — auto-generated runner
# Task: web_search
# Tool: web_search
import json, sys, os

ARGS = {
  "query": "stock performance"
}

def run(args):
    import urllib.request, urllib.parse
    query = urllib.parse.quote_plus(args.get("query", ""))
    url = f"https://html.duckduckgo.com/html/?q={query}"
    req = urllib.request.Request(url, headers={"User-Agent": "AMSAB/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode()[:4000]

if __name__ == "__main__":
    try:
        result = run(ARGS)
        print(json.dumps({"status": "ok", "output": result}))
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)
