# Waga Backend

FastAPI backend for price submission, normalization, validation, market-price
computation, and institutional exports.

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

## Quality checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
```
