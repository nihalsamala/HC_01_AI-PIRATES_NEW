#!/usr/bin/env bash
set -e

# Change to repo root
cd "$(dirname "$0")/.."

if [ -d "backend/.venv" ]; then
    source backend/.venv/bin/activate
fi

cd backend
exec uvicorn app.main:app --reload --port 8000
