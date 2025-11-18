#!/usr/bin/env bash
set -euo pipefail

# Resolve project root (directory containing this script)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"

echo "Project root: ${ROOT_DIR}"

echo ""
echo "Starting FastAPI backend on http://localhost:8000 ..."
cd "${BACKEND_DIR}"

# Assumes dependencies are already installed (see README.md)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Backend PID: ${BACKEND_PID}"

echo ""
echo "Starting React/Vite frontend on http://localhost:3000 ..."
cd "${FRONTEND_DIR}"

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
  echo "node_modules not found, running npm install ..."
  npm install
fi

# Run frontend dev server in foreground so you can see logs and Ctrl+C to stop
npm run dev

echo ""
echo "Shutting down backend (PID ${BACKEND_PID}) ..."
kill "${BACKEND_PID}" 2>/dev/null || true

echo "Done."


