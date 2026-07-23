# Waga Backend

FastAPI backend for price submission, normalization, validation, market-price
computation, Telegram integration, and institutional exports.

## Requirements

- Python 3.14
- `uv`
- Docker Desktop, or a local PostgreSQL installation

## Start locally

```powershell
Copy-Item .env.example .env
docker compose up -d db
py -m uv run alembic upgrade head
py -m uv run uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`, with OpenAPI
documentation at `/docs`.

## Quality checks

```powershell
py -m uv run ruff check .
py -m uv run ruff format --check .
py -m uv run mypy app
py -m uv run pytest
```
