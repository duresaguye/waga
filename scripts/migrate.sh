#!/bin/sh
set -eu

exec uv run --no-sync alembic upgrade head
