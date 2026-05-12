#!/usr/bin/env bash
set -euo pipefail

# Resolve project root (directory containing this script)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"

echo "Project root: ${ROOT_DIR}"
echo ""

########################################
# Check prerequisites
########################################
if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: 'uv' not found in PATH."
  echo "Install it from https://docs.astral.sh/uv/ then re-run this script."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "ERROR: 'npm' not found in PATH."
  echo "Install Node.js from https://nodejs.org/ then re-run this script."
  exit 1
fi

########################################
# Start FastAPI backend (via uv)
########################################
echo "Syncing backend dependencies with uv ..."
(cd "${BACKEND_DIR}" && uv sync)

echo ""
echo "Starting FastAPI backend on http://localhost:8123 ..."
cd "${BACKEND_DIR}"
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8123 &
BACKEND_PID=$!
echo "Backend PID: ${BACKEND_PID}"

########################################
# Start React/Vite frontend
########################################
echo ""
echo "Starting React/Vite frontend on http://localhost:3000 ..."
cd "${FRONTEND_DIR}"

if [ ! -d "node_modules" ]; then
  echo "node_modules not found, running npm install ..."
  npm install
fi

# Run frontend dev server in foreground so you can see logs and Ctrl+C to stop
npm run dev

########################################
# Cleanup backend when frontend stops
########################################
echo ""
echo "Shutting down backend (PID ${BACKEND_PID}) ..."
kill "${BACKEND_PID}" 2>/dev/null || true

echo "Done."
