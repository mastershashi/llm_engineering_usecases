#!/usr/bin/env bash
# Run all services locally for dev. Open 5 terminals or use a process manager.
# From repo root: autonomous-shopping-assistant/

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT"

# Load dev env
export ENV=dev
[ -f .env.dev ] && set -a && source .env.dev && set +a

echo "Starting services (dev). Gateway=8080, Orchestration=8000, Commerce=8001, Memory=8002, Agent=8003"
echo "Run each in a separate terminal:"
echo "  1. ENV=dev PYTHONPATH=$ROOT uvicorn services.orchestration.main:app --port 8000 --reload"
echo "  2. ENV=dev PYTHONPATH=$ROOT uvicorn services.commerce.main:app --port 8001 --reload"
echo "  3. ENV=dev PYTHONPATH=$ROOT uvicorn services.memory.main:app --port 8002 --reload"
echo "  4. ENV=dev PYTHONPATH=$ROOT uvicorn services.agent.main:app --port 8003 --reload"
echo "  5. ENV=dev PYTHONPATH=$ROOT uvicorn services.gateway.main:app --port 8080 --reload"
echo ""
echo "Then: curl -X POST http://localhost:8080/v1/tenants/00000000-0000-0000-0000-000000000001/sessions -H Content-Type:application/json -d '{\"message\":{\"type\":\"text\",\"payload\":{\"text\":\"Find running shoes\"}}}'"
