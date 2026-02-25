# AMSAB Worker — auto-generated runner
# Task: search for biryani recipes
# Tool: web_search
import json, sys, os

ARGS = {
  "query": "step-by-step biryani recipe"
}

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
            results.append(f"{i}. {t_clean}\n   {s_clean}\n   {url_i}")
        return "\n\n".join(results[:10])
    # Fallback: strip all HTML
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:4000]

if __name__ == "__main__":
    try:
        result = run(ARGS)
        print(json.dumps({"status": "ok", "output": result}))
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)
