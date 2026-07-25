# Waga Backend

FastAPI backend for price submission, normalization, validation, market-price
computation, and institutional exports.

**What we are building (final product scope):** [`docs/WHAT_WE_ARE_BUILDING.md`](docs/WHAT_WE_ARE_BUILDING.md)

## Requirements

- Python 3.13 or newer
- `uv`
- Docker Desktop, or a local PostgreSQL installation

## Start locally

```bash
cp .env.example .env
docker compose up -d db
uv sync --group dev
uv run alembic upgrade head
uv run waga-create-admin --email admin@example.com
uv run uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`, with OpenAPI
documentation at `/docs`.

Set a unique `WAGA_JWT_SECRET_KEY` containing at least 32 random bytes before
running in production. Supabase is used as PostgreSQL hosting only; authentication
is managed by this API.

## Telegram bot (contributor intake)

Phase 1 structured intake bot lives in `telegram_bot/`. See `docs/telegram-bot.md`.

```bash
# requires WAGA_TELEGRAM_BOT_TOKEN in .env
uv run waga-telegram-bot
```

Default `WAGA_TELEGRAM_DRY_RUN=true` logs submissions locally. Set `false` for live API.

Deploy bot on free Render web service (webhook): [`docs/deploy-bot-webhook.md`](docs/deploy-bot-webhook.md).

## Track B (prices / affordability / heat / copilot)

Read APIs for the NGO dashboard. Frontend guide: [`docs/frontend-track-b.md`](docs/frontend-track-b.md).

## Deploy (Render + GitHub)

See [`docs/deploy-render.md`](docs/deploy-render.md). Blueprint: [`render.yaml`](render.yaml)

- Web: API (`scripts/start-api.sh`, uses `$PORT`, migrates on release)
- Worker: Telegram bot (`scripts/start-bot.sh`)

## Quality checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
```
