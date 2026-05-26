UV=uv

.PHONY: sync lint test api cli tui migrate seed-taxonomy docker-build docker-up docker-tui docker-down

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

tui:
	$(UV) run bookshelf tui

migrate:
	$(UV) run alembic upgrade head

seed-taxonomy:
	$(UV) run bookshelf seed-taxonomy

docker-up:
	docker compose up --build api

docker-build:
	docker compose --profile tools build api

docker-tui:
	docker compose --profile tools run --rm --build cli tui

docker-down:
	docker compose down
