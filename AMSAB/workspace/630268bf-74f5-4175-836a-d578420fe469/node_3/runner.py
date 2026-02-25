# AMSAB Worker — auto-generated runner
# Task: write biryani recipe steps to a file
# Tool: filesystem_write
import json, sys, os

ARGS = {
  "filename": "biryani_recipe.txt",
  "content": "[FAILED] {\"status\": \"error\", \"error\": \"invalid syntax (<amsab>, line 2)\"}"
}

def run(args):
    path = args.get("filename", args.get("path", "output.txt"))
    content = args.get("content", "")
    with open(f"/output/{path}", "w") as f:
        f.write(str(content))
    return f"Written to {path}"

if __name__ == "__main__":
    try:
        result = run(ARGS)
        print(json.dumps({"status": "ok", "output": result}))
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)
