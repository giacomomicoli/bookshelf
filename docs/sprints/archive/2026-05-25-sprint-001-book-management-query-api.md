# Sprint 001 - Book Management, Query, and API Contract Separation

## Status

Completed

## Goal

Extend the bootstrap bookshelf system with full book lifecycle management, richer querying, and a cleaner API contract ready for future UI integration.

## Scope

- add CLI `update`, `delete`, and `query` commands for books
- keep `list` and `unread` as convenience wrappers over the shared query flow
- add API request and response schema separation from internal service DTOs
- add `page` and `page_size` pagination to book query responses
- add single-book fetch, update, and delete API endpoints
- add thumbnail replacement and cleanup behavior during update and delete
- add root `README.md` for end-user setup and command usage
- update architecture, API, and operations docs to reflect the new surface area

## Out of Scope

- soft delete
- full-text search in notes
- authentication or multi-user behavior
- API-based file upload for thumbnails
- taxonomy CRUD workflows
- cursor pagination

## Decisions

- `ADR-014`: hard delete books and remove thumbnails
- `ADR-015`: page-based pagination
- `ADR-016`: separate API schemas from service DTOs
- `ADR-017`: basic book query filters and sorting
- `ADR-018`: replace thumbnails by deleting old objects

## Tasks

1. add internal query and update DTOs plus pagination result models
2. extend repositories for filtered queries, counts, updates, and deletes
3. implement shared services for `get_book`, `query_books`, `update_book`, and `delete_book`
4. extend thumbnail storage with object deletion support
5. add API request and response schema modules distinct from internal DTOs
6. implement paginated `GET /api/v1/books`
7. implement `GET /api/v1/books/{book_id}`
8. implement `PATCH /api/v1/books/{book_id}`
9. implement `DELETE /api/v1/books/{book_id}`
10. implement CLI `query`
11. implement CLI `update <book_id>` with prompts plus flags
12. implement CLI `delete <book_id>` with confirmation and `--yes`
13. add tests for repository, service, CLI, and API behavior
14. update root and `docs/` documentation to match the new command and API surface

## Query Contract

### Filters

- `status`
- `category`
- `sub_category`
- `format`
- `name_contains`
- `published_before`
- `published_after`

### Sort Options

- `created_at_desc`
- `created_at_asc`
- `published_on_desc`
- `published_on_asc`
- `name_asc`
- `name_desc`

## CLI Notes

- `update` supports flags for targeted changes and interactive prompts for manual edits
- pressing Enter during interactive update keeps the current value
- note editing should open `$EDITOR` prefilled with current content
- `delete` prompts for confirmation unless `--yes` is provided

## API Notes

- `GET /api/v1/books` should return a paginated envelope, not a bare list
- API request/response schemas must not expose CLI-only fields such as `thumbnail_path`
- `DELETE /api/v1/books/{book_id}` should return `204 No Content`

## Exit Criteria

- CLI supports book query, update, and delete workflows
- API supports paginated querying, single-book fetch, update, and delete
- API routes use dedicated request and response schemas
- thumbnail replacement and deletion clean up old objects consistently
- root `README.md` documents setup and command usage
- tests cover the new behavior across service, CLI, and API layers

## Outcome

- shared services now support book query, fetch, update, and deletion
- CLI now exposes `query`, `update`, and `delete`
- API now exposes paginated book queries plus single-book fetch, update, and delete routes
- HTTP request and response schemas are separated from internal service DTOs
- root and `docs/` documentation were updated to reflect the implemented surface
- verification passed with `uv run ruff check .` and `uv run pytest`

## Retrospective Notes

- Keeping query/update/delete logic in shared services avoided CLI and API drift.
- Separating API schemas from service DTOs was necessary once pagination and HTTP-only contract rules were introduced.
- Thumbnail lifecycle cleanup now matches the ADRs, but real MinIO integration tests would still be useful as a follow-up.
