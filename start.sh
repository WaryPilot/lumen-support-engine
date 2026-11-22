#!/usr/bin/env bash
set -e

export PYTHONUNBUFFERED=1

# Run background Gmail AI Poller with automatic restart on transient errors
(
  while true; do
    echo "[start.sh] Starting Lumen Gmail Poller..."
    uv run python -u -m app.poller || echo "[start.sh] Poller exited with error, restarting in 10s..."
    sleep 10
  done
) &

# Start FastAPI + React Admin Dashboard in foreground
exec uv run fastapi run app/main.py --host 0.0.0.0 --port "${PORT:-8000}"