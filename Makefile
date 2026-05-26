UV=uv

.PHONY: sync lint test api cli migrate seed-taxonomy docker-up docker-down

sync:
	$(UV) sync --all-extras

lint:
	$(UV) run ruff check .

test:
	$(UV) run pytest

api:
	$(UV) run uvicorn bookshelf.api.app:create_app --factory --host 0.0.0.0 --port 8000

cli:
	$(UV) run bookshelf --help

migrate:
	$(UV) run alembic upgrade head

seed-taxonomy:
	$(UV) run bookshelf seed-taxonomy

docker-up:
	docker compose up --build api

docker-down:
	docker compose down
