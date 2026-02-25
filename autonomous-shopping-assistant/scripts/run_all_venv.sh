#!/bin/bash
# Run all 5 services using .venv. Stop with Ctrl+C.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT"
export ENV=dev
PY="$ROOT/.venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "Run scripts/setup_venv.sh first."
  exit 1
fi
echo "Starting services (Gateway http://localhost:8080)..."
$PY -m uvicorn services.orchestration.main:app --host 0.0.0.0 --port 8000 &
$PY -m uvicorn services.commerce.main:app --host 0.0.0.0 --port 8001 &
$PY -m uvicorn services.memory.main:app --host 0.0.0.0 --port 8002 &
$PY -m uvicorn services.agent.main:app --host 0.0.0.0 --port 8003 &
$PY -m uvicorn services.gateway.main:app --host 0.0.0.0 --port 8080 &
wait
