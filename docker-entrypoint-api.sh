#!/bin/sh
set -eu

uv run alembic upgrade head
exec uv run uvicorn bookshelf.api.app:create_app --factory --host 0.0.0.0 --port 8000
