#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

echo "Building AMSAB worker Docker image..."
docker build -t amsab-worker:latest ./docker/worker
echo "✅ Worker image built: amsab-worker:latest"
