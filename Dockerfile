FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

ENV UV_PYTHON=python3

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
