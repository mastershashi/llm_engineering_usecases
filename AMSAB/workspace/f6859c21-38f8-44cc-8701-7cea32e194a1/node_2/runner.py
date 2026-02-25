# AMSAB Worker — auto-generated runner
# Task: read project documentation and notes
# Tool: filesystem_read
import json, sys, os

ARGS = {
  "path": "/output/project-notes.txt"
}

def run(args):
    path = args.get("path", "")
    with open(path) as f:
        return f.read()

if __name__ == "__main__":
    try:
        result = run(ARGS)
        print(json.dumps({"status": "ok", "output": result}))
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)
