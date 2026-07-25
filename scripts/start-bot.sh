#!/bin/sh
set -eu

# Prefer explicit API URL; else build from Render-linked web service URL.
if [ -z "${WAGA_API_BASE_URL:-}" ] && [ -n "${WAGA_API_EXTERNAL_URL:-}" ]; then
  WAGA_API_BASE_URL="${WAGA_API_EXTERNAL_URL%/}/api/v1"
  export WAGA_API_BASE_URL
fi

exec uv run --no-sync waga-telegram-bot
