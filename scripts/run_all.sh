#!/usr/bin/env bash
# WardPulse: Start Backend and Frontend together (Bash)
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=========================================================="
echo "  Starting WardPulse Hospital Ward Early Warning System   "
echo "=========================================================="

# 1. Setup Python venv if missing
if [ ! -f "backend/.venv/bin/python" ]; then
    echo "[INFO] Creating virtual environment in backend/.venv..."
    python3 -m venv backend/.venv
    backend/.venv/bin/pip install -r backend/requirements.txt
fi

PYTHON="backend/.venv/bin/python"

# 2. Seed database
echo "[1/3] Seeding SQLite database from 20-bed simulator..."
(cd backend && $PYTHON -m app.db.seed)

# 3. Start backend in background
echo "[2/3] Starting FastAPI Backend on http://localhost:8000..."
(cd backend && $PYTHON -m uvicorn app.main:app --port 8000) &
BACKEND_PID=$!

trap "kill $BACKEND_PID 2>/dev/null || true; exit" SIGINT SIGTERM EXIT

# 4. Start frontend
echo "[3/3] Starting Vite React Console on http://localhost:5173..."
echo ""
echo "=========================================================="
echo "  Console:  http://localhost:5173"
echo "  API Docs: http://localhost:8000/docs"
echo "  To test:  python scripts/check_stories.py"
echo "=========================================================="
echo "Press Ctrl+C to stop both servers."

export VITE_USE_MOCK=false
export VITE_API_URL=http://localhost:8000

cd frontend
npm run dev
