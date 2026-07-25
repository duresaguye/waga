#!/bin/sh
set -eu

# Prefer explicit API URL; else build from Render-linked web service URL.
if [ -z "${WAGA_API_BASE_URL:-}" ] && [ -n "${WAGA_API_EXTERNAL_URL:-}" ]; then
  WAGA_API_BASE_URL="${WAGA_API_EXTERNAL_URL%/}/api/v1"
  export WAGA_API_BASE_URL
fi

# On Render web services, default to webhook so free tier can wake on Telegram POSTs.
if [ -z "${WAGA_TELEGRAM_MODE:-}" ] && [ -n "${RENDER_EXTERNAL_URL:-}" ]; then
  WAGA_TELEGRAM_MODE=webhook
  export WAGA_TELEGRAM_MODE
fi

if [ -z "${WAGA_TELEGRAM_WEBHOOK_URL:-}" ] && [ -n "${RENDER_EXTERNAL_URL:-}" ]; then
  WAGA_TELEGRAM_WEBHOOK_URL="${RENDER_EXTERNAL_URL}"
  export WAGA_TELEGRAM_WEBHOOK_URL
fi

exec uv run --no-sync waga-telegram-bot
