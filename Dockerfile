FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

ENV UV_PYTHON=python3
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install dependencies first (better layer cache), without the local project yet.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source, then install the project so app/ and telegram_bot/ are packaged.
COPY . .
RUN uv sync --frozen --no-dev

RUN uv sync --frozen --no-dev

RUN chmod +x scripts/start-api.sh scripts/start-bot.sh scripts/migrate.sh

EXPOSE 8000

# Render sets PORT (default 10000). Local/docker-compose can omit it (defaults to 8000).
CMD ["./scripts/start-api.sh"]
