#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# ── Check .env ────────────────────────────────────────────────────────────────
if [ ! -f "$ROOT/.env" ]; then
  echo "No .env found. Copying from .env.example..."
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo "Edit $ROOT/.env with your API keys, then re-run."
  exit 1
fi

# ── Backend ───────────────────────────────────────────────────────────────────
echo "Starting backend..."
cd "$ROOT/backend"
[ ! -d ".venv" ] && python -m venv .venv
source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate
pip install -q -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload &
BACKEND_PID=$!

# ── Frontend ──────────────────────────────────────────────────────────────────
echo "Starting frontend..."
cd "$ROOT/frontend"
[ ! -d "node_modules" ] && npm install
npm run dev &
FRONTEND_PID=$!

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Backend  → http://localhost:8080"
echo "  Frontend → http://localhost:5173"
echo "  API Docs → http://localhost:8080/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Press Ctrl+C to stop all services."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
