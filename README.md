# Bookshelf

Bookshelf is a CLI-first, API-ready utility for storing information about books in a way that mirrors a physical bookshelf. Categories act like shelf compartments, and books store structured metadata that can later be exposed through a graphical interface.

## Features

- store books with category and optional sub-category assignment
- track reading status as `unread`, `reading`, or `read`
- attach purchase URLs as an array
- import thumbnails from local files or remote URLs into MinIO
- store long-form notes for each book
- seed and inspect a controlled taxonomy from YAML
- query books with filters, sorting, and pagination
- update or delete books from both CLI and API
- use the CLI today and build on the same service layer through the API later

## Requirements

- Python 3.12+
- `uv`
- Docker and Docker Compose for containerized infrastructure

## Quick Start With uv

1. Copy the environment template:

```bash
cp .env.example .env
```

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

6. Add your first book:

```bash
uv run bookshelf add
```

## Quick Start With Docker

1. Start the API and infrastructure:

```bash
make docker-up
```

2. Seed taxonomy using the CLI container:

```bash
docker compose run --rm --profile tools cli seed-taxonomy
```

3. Add a book using the CLI container:

```bash
docker compose run --rm --profile tools cli add
```

## Common Commands

### Development

```bash
make sync
make lint
make test
make migrate
make seed-taxonomy
make docker-up
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

The API uses the same service layer as the CLI and now exposes paginated querying plus single-book management.

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
