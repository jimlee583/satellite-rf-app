#!/usr/bin/env bash
set -euo pipefail

# Resolve project root (directory containing this script)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"
VENV_DIR="${ROOT_DIR}/.venv"

echo "Project root: ${ROOT_DIR}"
echo ""

########################################
# Activate Python virtual environment
########################################
if [ -d "${VENV_DIR}" ]; then
  if [ -f "${VENV_DIR}/bin/activate" ]; then
    echo "Activating Python virtual environment at ${VENV_DIR} ..."
    # shellcheck disable=SC1091
    source "${VENV_DIR}/bin/activate"
  else
    echo "WARNING: ${VENV_DIR}/bin/activate not found."
    echo "         Your virtual environment may not be set up correctly."
  fi
else
  echo "WARNING: No .venv directory found at ${VENV_DIR}."
  echo "         Backend may fail if dependencies are not installed."
  echo "         To create one:  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
fi

# Ensure uvicorn is available
if ! command -v uvicorn >/dev/null 2>&1; then
  echo ""
  echo "ERROR: 'uvicorn' not found in PATH."
  echo "Make sure your virtual environment is activated and dependencies are installed:"
  echo "  source .venv/bin/activate"
  echo "  pip install -r requirements.txt"
  exit 1
fi

########################################
# Start FastAPI backend
########################################
echo ""
echo "Starting FastAPI backend on http://localhost:8000 ..."
cd "${BACKEND_DIR}"

# Assumes dependencies are already installed (see README.md)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Backend PID: ${BACKEND_PID}"

########################################
# Start React/Vite frontend
########################################
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

########################################
# Cleanup backend when frontend stops
########################################
echo ""
echo "Shutting down backend (PID ${BACKEND_PID}) ..."
kill "${BACKEND_PID}" 2>/dev/null || true

echo "Done."


