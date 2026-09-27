#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend"
# Dependencies must already be installed. Both processes share the same cwd/.env.
python -m uvicorn app.main:app --host 127.0.0.1 --port "${PORT:-8000}" &
API_PID=$!
cleanup() { kill "$API_PID" "${WORKER_PID:-}" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
# Let local SQLite initialization/seed complete before the worker opens it.
for i in $(seq 1 30); do
  if python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${PORT:-8000}/api/v1/health')" 2>/dev/null; then break; fi
  sleep 1
done
python -m app.worker &
WORKER_PID=$!
wait "$API_PID" "$WORKER_PID"
