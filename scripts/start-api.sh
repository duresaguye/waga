#!/bin/sh
set -eu

PORT="${PORT:-8000}"

exec uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
