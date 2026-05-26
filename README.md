# Bookshelf

Bookshelf is a CLI-first, TUI-enabled, API-ready utility for storing information about books in a way that mirrors a physical bookshelf. Categories act like shelf compartments, and books store structured metadata that can be managed from prompt-driven commands, a full-screen terminal UI, or the HTTP API.

## Features

- store books with category and optional sub-category assignment
- store books with ordered multi-author metadata
- launch a full-screen terminal UI wired to shared services
- track reading status as `unread`, `reading`, or `read`
- attach purchase URLs as an array
- import thumbnails from local files or remote URLs into MinIO
- store long-form notes for each book
- seed and inspect a controlled taxonomy from YAML
- query books with filters, sorting, and pagination
- update or delete books from both CLI and API
- reuse the same service layer across CLI, TUI, and API adapters

## Requirements

- Python 3.12+
- `uv`
- Docker and Docker Compose for containerized infrastructure

## Environment Files

- `.env.example`: committed template for host-based commands. Copy it to `.env` for local workflows that connect to `localhost` services.
- `.env`: ignored local environment file used by host-run commands such as `make migrate`, `make seed-taxonomy`, and `make tui`.
- `.env.docker`: committed Docker Compose bootstrap config. It uses Compose service names such as `postgres` and `minio` and must remain non-secret.

If you see local commands trying to connect to `postgres` instead of `localhost`, your local `.env` is using Docker container settings and should be refreshed from `.env.example`.

## Quick Start With uv

1. Copy the environment template:

```bash
cp .env.example .env
```

This local `.env` targets `localhost` services for host-run commands.

2. Install dependencies:

```bash
make sync
```

3. Start PostgreSQL and MinIO if you want to run the app locally against containers:

```bash
docker compose up -d postgres minio minio-init
```

4. Apply migrations:

```bash
make migrate
```

5. Seed the taxonomy:

```bash
make seed-taxonomy
```

6. Launch the TUI:

```bash
make tui
uv run bookshelf tui
```

`make tui` and `uv run bookshelf tui` are host-run commands. They use your current workspace code and local `.env`. No Docker image is involved, so there is nothing to rebuild for this path.

7. Or add your first book:

```bash
uv run bookshelf add
```

## Quick Start With Docker

1. Build the shared app image:

```bash
make docker-build
```

This builds the local Docker image `bookshelf-app:local`.

The same image is used by:

- the `api` service
- the `cli` service
- `bookshelf tui` when run through Docker

2. Start the API and infrastructure:

```bash
make docker-up
```

Docker Compose uses `.env.docker` so containers resolve `postgres` and `minio` by service name.

`.env.docker` is committed because it only contains public bootstrap defaults for local development. Do not store real secrets in it.

`make docker-up` also rebuilds the API service before starting it.

3. Seed taxonomy using the CLI container:

```bash
docker compose --profile tools run --rm cli seed-taxonomy
```

4. Launch the TUI from an interactive terminal:

```bash
make docker-tui
docker compose --profile tools run --rm --build cli tui
```

`make docker-tui` now rebuilds the shared app image before starting the TUI, so Dockerized TUI runs do not keep using stale application code.

For Dockerized thumbnail file imports, place files in the repo `imports/` directory and use `/app/imports/<filename>` from the CLI or TUI.

5. Or add a book using the CLI container:

```bash
docker compose --profile tools run --rm cli add
```

When you need a rebuild:

- for `make tui`: never, because it does not use Docker
- for `make docker-tui`: yes when app code, dependencies, Dockerfile, or entrypoints changed; `make docker-tui` now does this automatically
- for `make docker-up`: the image is rebuilt automatically because the command uses `--build`

## Common Commands

### Development

```bash
make sync
make lint
make test
make migrate
make seed-taxonomy
make tui
make docker-up
make docker-build
make docker-tui
make docker-down
```

### CLI Commands

#### `bookshelf seed-taxonomy`

Load categories and sub-categories from the versioned YAML seed file.

```bash
uv run bookshelf seed-taxonomy
uv run bookshelf seed-taxonomy --path src/bookshelf/seeds/taxonomy.yaml
```

#### `bookshelf categories`

Show the available categories and sub-categories.

```bash
uv run bookshelf categories
```

#### `bookshelf tui`

Launch the full-screen TUI library view.

```bash
make tui
uv run bookshelf tui
make docker-tui
docker compose --profile tools run --rm --build cli tui
```

Image behavior:

- host-run `make tui` uses local source directly and does not use Docker
- Dockerized TUI runs use the shared image `bookshelf-app:local`
- the `api` and `cli` services reuse that same image
- `make docker-build` builds that shared image explicitly

Current behavior:

- starts a Textual app with a header and footer
- shows a book list with a selected-book detail pane
- filters by `status`, `category`, `format`, and `name_contains`
- refreshes immediately when supported TUI filters change
- supports previous and next page navigation over shared query results
- supports create, update, and delete flows against shared services with immediate in-app refresh
- supports inline note editing and `Open in $EDITOR` handoff when available
- supports thumbnail imports by URL or local file path
- press `r` to force a manual refresh and return to page 1
- press `q` to quit

Troubleshooting:

- if `make tui` does not show books you know exist, make sure you are using a reasonably sized terminal window and relaunch the TUI; the current layout is intended for normal full-screen terminal sizes
- if `make docker-tui` does not reflect recent code changes, rerun it; it now rebuilds automatically
- if you still do not see a known book, clear filters first; `r` is still available for a manual reload

Thumbnail path rules:

- host-run CLI and TUI commands can use any readable local file path
- Dockerized CLI and TUI commands must use container-visible paths, so place files in `imports/` and use `/app/imports/<filename>`

#### `bookshelf add`

Interactively create a new book entry.

```bash
uv run bookshelf add
```

You can also prefill fields with flags:

```bash
uv run bookshelf add --name "The Argonauts" --category essays --sub-category personal-essays
```

Supported flags:

- `--name`
- `--author` repeated in display order
- `--category`
- `--sub-category`
- `--published-on`
- `--edition`
- `--format`
- `--page-length`
- `--reading-status`
- `--thumbnail-path`
- `--thumbnail-url`
- `--note-file`

Notes:

- authors are stored in the order entered
- purchase URLs are collected interactively
- notes open through your configured editor unless `--note-file` is used
- only one thumbnail source can be provided at a time

#### `bookshelf list`

List books using the default query behavior. For richer filtering, use `bookshelf query`.

```bash
uv run bookshelf list
uv run bookshelf list --status unread
```

#### `bookshelf unread`

Shortcut for listing unread books.

```bash
uv run bookshelf unread
```

#### `bookshelf query`

Query books with filters, sorting, and pagination.

```bash
uv run bookshelf query --status unread --category essays
uv run bookshelf query --format hardcover --sort name_asc --page 1 --page-size 10
uv run bookshelf query --published-after 2020-01-01 --name-contains history
```

Supported filters and options:

- `--status`
- `--category`
- `--sub-category`
- `--format`
- `--name-contains`
- `--published-before`
- `--published-after`
- `--sort`
- `--page`
- `--page-size`

#### `bookshelf update <book_id>`

Update a book with targeted flags or interactive prompts.

```bash
uv run bookshelf update 11111111-1111-1111-1111-111111111111 --reading-status read
uv run bookshelf update 11111111-1111-1111-1111-111111111111 --clear-note
uv run bookshelf update 11111111-1111-1111-1111-111111111111
```

Supported update flags include:

- `--name`
- `--author` repeated to replace authors in display order
- `--category`
- `--sub-category`
- `--purchase-url` repeated to replace URLs
- `--thumbnail-path`
- `--thumbnail-url`
- `--published-on`
- `--edition`
- `--format`
- `--page-length`
- `--reading-status`
- `--note-file`
- `--clear-authors`
- `--clear-sub-category`
- `--clear-purchase-urls`
- `--clear-thumbnail`
- `--clear-published-on`
- `--clear-edition`
- `--clear-format`
- `--clear-page-length`
- `--clear-note`

Notes:

- if no update flags are passed, the command falls back to interactive editing
- replacing or clearing a thumbnail deletes the previously stored object after a successful update

#### `bookshelf delete <book_id>`

Delete a book and remove its thumbnail object from storage.

```bash
uv run bookshelf delete 11111111-1111-1111-1111-111111111111
uv run bookshelf delete 11111111-1111-1111-1111-111111111111 --yes
```

## API

The API uses the same service layer as the CLI and TUI and now exposes paginated querying plus single-book management.

Current endpoints:

- `GET /health`
- `GET /api/v1/books`
- `GET /api/v1/books/{book_id}`
- `POST /api/v1/books`
- `PATCH /api/v1/books/{book_id}`
- `DELETE /api/v1/books/{book_id}`
- `GET /api/v1/categories`

`GET /api/v1/books` supports:

- `status`
- `category`
- `sub_category`
- `format`
- `name_contains`
- `published_before`
- `published_after`
- `sort`
- `page`
- `page_size`

Example:

```bash
curl "http://localhost:8000/api/v1/books?status=unread&page=1&page_size=10"
```

Run the API locally:

```bash
make api
```

## Data Model Summary

Each book currently stores:

- name
- authors
- category
- optional sub-category
- purchase URLs
- thumbnail reference
- publishing date
- edition
- format
- page length
- reading status
- note

## Storage

- PostgreSQL stores structured book and taxonomy data
- MinIO stores imported thumbnail objects

## Documentation

Detailed project documentation lives in `docs/`.

Start with:

- `docs/README.md`
- `docs/architecture/overview.md`
- `docs/domain/books.md`
- `docs/api/overview.md`
- `docs/operations/local-development.md`

## Workflow

- Bootstrap is complete.
- All follow-up implementation work must be driven by a sprint document in `docs/sprints/active/`.
- Completed sprints must be moved to `docs/sprints/archive/`.
- Any open question that impacts the core design must be documented as an ADR in `docs/decisions/` before implementation continues.
