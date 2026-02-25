#!/bin/sh
# ─── AMSAB Frontend Startup ──────────────────────────────────────────────────
set -e

PROJ_DIR="$(cd "$(dirname "$0")/.." && pwd)"
NODE_BIN="$PROJ_DIR/.node/bin"

# Check Node.js is available (bundled or system)
if [ -x "$NODE_BIN/node" ]; then
    export PATH="$NODE_BIN:$PATH"
    echo "✅ Using bundled Node.js $(node --version)"
elif command -v node >/dev/null 2>&1; then
    echo "✅ Using system Node.js $(node --version)"
else
    echo "❌ Node.js not found. Run: ./scripts/install_frontend.sh first"
    exit 1
fi

FRONTEND_DIR="$PROJ_DIR/frontend"

# Install node_modules if missing
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm --prefix "$FRONTEND_DIR" install
fi

echo ""
echo "🚀 Starting AMSAB frontend on http://localhost:3000"
echo ""
npm --prefix "$FRONTEND_DIR" run dev
