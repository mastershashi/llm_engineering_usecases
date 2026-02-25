#!/bin/bash
# Create virtualenv and install dependencies. Run from autonomous-shopping-assistant/.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "Created .venv"
fi
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
echo "Installed dependencies. Activate with: source .venv/bin/activate"
echo "Or run services with: ./scripts/run_all_venv.sh"
