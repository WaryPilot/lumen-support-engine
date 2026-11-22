#!/usr/bin/env bash
set -e

# Start the background Gmail AI Poller
uv run python -m app.poller &

# Start the FastAPI + React Admin Dashboard on Render's $PORT
exec uv run fastapi run app/main.py --host 0.0.0.0 --port "${PORT:-8000}"
