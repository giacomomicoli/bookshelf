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
- `make tui`
- `make docker-build`
- `make docker-up`
- `make docker-tui`
- `make docker-down`

## Environment

- Copy `.env.example` to `.env` for local commands and processes.
- `.env.example` targets `localhost` services for host-based workflows.
- `docker compose` uses `.env.docker` for container-based workflows so services resolve by Compose service name.
- `.env.docker` stays committed because it contains only bootstrap defaults for local development and must remain non-secret.
- If local commands try to resolve `postgres` or `minio`, refresh `.env` from `.env.example`.

## Runtime Services

- `api`: FastAPI app
- `cli`: same image, Typer command entrypoint used on demand for CLI and TUI commands
- `postgres`: primary relational database
- `minio`: thumbnail object storage

## Docker Workflow

- Build the shared local image with `make docker-build`.
- Start infrastructure and API with `make docker-up`.
- The Docker services reuse the shared app image `bookshelf-app:local`.
- Run CLI and TUI commands in containers with `docker compose --profile tools run --rm cli <command>`.
- Launch the current TUI library view with `make docker-tui`.
- `make docker-tui` rebuilds the shared app image before starting the TUI.
- The `cli` tools container mounts repo `./imports` to `/app/imports`.
- Host-run CLI and TUI commands can import thumbnails from any readable local file path.
- Dockerized CLI and TUI commands must use container-visible paths such as `/app/imports/<filename>`.
- The `imports/` directory is tracked with `.gitkeep`, but local files inside it are gitignored.

## TUI Status

- `bookshelf tui` now launches a Textual library view over shared services.
- The current implementation shows a paginated book list, selected-book details, filters for `status`, `category`, `format`, and `name_contains`, and create/update/delete flows.
- Notes can be edited inline or handed off through `$EDITOR` when the runtime supports app suspension.
- Manual refresh returns to page 1 so newly created books are visible in the first result page.
- Thumbnail imports work from remote URLs or local file paths, including Dockerized paths under `/app/imports`.
- The layout is tuned for normal full-screen terminal sizes so the list and detail panes stay visible alongside the filter bar.

## TUI Troubleshooting

- `make tui` uses local source directly and does not use Docker, so rebuilding an image cannot affect that path.
- `make docker-tui` rebuilds the shared image before launch.
- If a known book is missing in the TUI, clear filters and press `r`.
- If the layout looks wrong or content appears missing, resize to a normal full-screen terminal and relaunch.

## Useful Commands

- `uv run bookshelf seed-taxonomy`
- `uv run bookshelf categories`
- `make tui`
- `uv run bookshelf tui`
- `uv run bookshelf add`
- `uv run bookshelf list`
- `uv run bookshelf unread`
- `uv run bookshelf query --status unread --page 1 --page-size 10`
- `uv run bookshelf update <book_id> --reading-status read`
- `uv run bookshelf delete <book_id> --yes`
- `make docker-tui`

## Bootstrap Notes

Bootstrap is the only phase allowed to proceed without an active sprint document. All work after bootstrap must start in `docs/sprints/active/` and move to `docs/sprints/archive/` when complete.
