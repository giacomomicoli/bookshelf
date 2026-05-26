# Local Development

## Tooling

- Python 3.12+
- `uv` for dependency and task management
- Docker and Docker Compose for infrastructure and containerized runs

## Common Commands

- `make sync`
- `make lint`
- `make test`
- `make migrate`
- `make seed-taxonomy`
- `make docker-up`
- `make docker-down`

## Environment

- `docker compose` uses `.env.example` by default for the bootstrap setup.
- Copy it to `.env` when you want to customize local values for non-container runs.

## Runtime Services

- `api`: FastAPI app
- `cli`: same image, Typer command entrypoint used on demand
- `postgres`: primary relational database
- `minio`: thumbnail object storage

## Docker Workflow

- Start infrastructure and API with `make docker-up`.
- Run CLI commands in containers with `docker compose run --rm cli <command>`.
- For local file thumbnail imports, the simplest bootstrap workflow is running the CLI locally with `uv run bookshelf ...`.

## Useful CLI Commands

- `uv run bookshelf seed-taxonomy`
- `uv run bookshelf categories`
- `uv run bookshelf add`
- `uv run bookshelf list`
- `uv run bookshelf unread`
- `uv run bookshelf query --status unread --page 1 --page-size 10`
- `uv run bookshelf update <book_id> --reading-status read`
- `uv run bookshelf delete <book_id> --yes`

## Bootstrap Notes

Bootstrap is the only phase allowed to proceed without an active sprint document. All work after bootstrap must start in `docs/sprints/active/` and move to `docs/sprints/archive/` when complete.
