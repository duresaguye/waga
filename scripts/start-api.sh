#!/bin/sh
set -eu

PORT="${PORT:-8000}"

./scripts/migrate.sh

if [ "${WAGA_ENVIRONMENT:-development}" = "development" ]; then
  uv run --no-sync python -m app.commands.seed_admin
fi

exec uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
