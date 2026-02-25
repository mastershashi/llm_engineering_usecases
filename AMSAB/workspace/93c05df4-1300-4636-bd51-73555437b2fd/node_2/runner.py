# AMSAB Worker — auto-generated runner
# Task: fetch top performing stocks since last week
# Tool: scraper
import json, sys, os

ARGS = {
  "url": "https://example.com/stock_data"
}

def run(args):
    import urllib.request, ssl, re
    url = args.get("url", "")
    if not url:
        return "Error: no url provided"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AMSAB/1.0)"}
    req = urllib.request.Request(url, headers=headers)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
        html = r.read().decode(errors="replace")
    # Remove script/style blocks then strip remaining tags
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:6000]

if __name__ == "__main__":
    try:
        result = run(ARGS)
        print(json.dumps({"status": "ok", "output": result}))
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)
