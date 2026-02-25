#!/bin/sh
# ─── AMSAB Backend Startup ───────────────────────────────────────────────────
set -e

PROJ_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Create .env from example if not present
if [ ! -f "$PROJ_DIR/.env" ]; then
    cp "$PROJ_DIR/env.example" "$PROJ_DIR/.env"
    echo "⚠  Created .env from env.example. Please add your OPENAI_API_KEY before restarting."
    exit 1
fi

# Create venv if missing
if [ ! -f "$PROJ_DIR/.venv/bin/python3" ]; then
    echo "🔧 Creating Python virtual environment..."
    python3 -m venv "$PROJ_DIR/.venv"
fi

# Install/update dependencies
echo "📦 Installing Python dependencies..."
"$PROJ_DIR/.venv/bin/pip" install -r "$PROJ_DIR/requirements.txt" --quiet \
    --trusted-host pypi.org --trusted-host files.pythonhosted.org

# Start server
echo ""
echo "🚀 Starting AMSAB backend on http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo ""
cd "$PROJ_DIR"
"$PROJ_DIR/.venv/bin/uvicorn" backend.main:app --reload --host 0.0.0.0 --port 8000
