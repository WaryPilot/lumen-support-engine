#!/usr/bin/env bash
set -e

uv run python -m app.poller &

exec uv run fastapi run app/main.py --host 0.0.0.0 --port "${PORT:-8000}"