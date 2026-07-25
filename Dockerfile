FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

ENV UV_PYTHON=python3
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

RUN chmod +x scripts/start-api.sh scripts/start-bot.sh scripts/migrate.sh

EXPOSE 8000

# Render sets PORT (default 10000). Local/docker-compose can omit it (defaults to 8000).
CMD ["./scripts/start-api.sh"]
