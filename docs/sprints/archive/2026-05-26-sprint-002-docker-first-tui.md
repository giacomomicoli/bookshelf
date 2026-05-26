# Sprint 002 - Docker-First Full-Screen TUI

## Status

Completed

## Goal

Add a full-screen terminal UI launched as `bookshelf tui` that reuses shared services, runs locally or through the existing Docker tools workflow, and supports browsing saved books plus the current book management operations.

## Scope

- add a `tui` adapter package under `src/bookshelf/tui/`
- launch the TUI through the existing Typer surface as `bookshelf tui`
- use `Textual` for the full-screen interface
- keep the TUI as a thin adapter over shared services, not an API client
- reuse the current application image and Compose tools workflow for Dockerized runs
- support a library screen with saved-book list, current selection, and details pane
- support initial filters for `status`, `category`, `format`, and `name_contains`
- use next/previous navigation over the existing paginated query contract
- support create, update, and delete workflows from the TUI
- support note editing inline and through external `$EDITOR` handoff when available
- support thumbnail import by URL and by local file path
- support Dockerized local thumbnail imports through a mounted host `./imports` directory exposed as `/app/imports`
- add automated tests for TUI behavior and adapter wiring
- update end-user and operations documentation

## Out of Scope

- using the HTTP API as the TUI backend
- new book-management capabilities beyond current shared services
- TUI controls for `sub_category`, `published_before`, `published_after`, or explicit `sort` selection in v1
- thumbnail preview rendering in the terminal
- a separate TUI image or standalone orchestration path outside the existing Compose workflow
- authentication or multi-user behavior

## Decisions

- `ADR-005`: shared service layer remains the only place for business logic
- `ADR-013`: thumbnails still import from local paths or remote URLs
- `ADR-014`: deleting a book removes its thumbnail object
- `ADR-017`: shared query filters remain the source of truth for TUI filtering
- `ADR-018`: replacing or clearing a thumbnail deletes the previous object
- `ADR-019`: add a Docker-first Textual TUI adapter through `bookshelf tui`

## Tasks

1. add `Textual` and create the `src/bookshelf/tui/` adapter package
2. add the `bookshelf tui` command to the existing Typer app
3. add TUI dependency wiring that reuses the shared book and taxonomy services
4. implement the main library screen with book list, details pane, filter bar, and footer help
5. connect initial filters for `status`, `category`, `format`, and `name_contains`
6. implement next/previous page navigation over the existing paginated query service
7. implement create-book flow from the TUI
8. implement update-book flow, including existing clear-field semantics
9. implement delete confirmation and deletion flow
10. implement note editing with inline editing plus external editor handoff
11. handle missing `$EDITOR` gracefully and keep inline note editing available in all environments
12. implement thumbnail handling for URL imports and local-path imports
13. update the Docker tools workflow so `bookshelf tui` runs interactively and sees `/app/imports`
14. add automated tests for empty state, browse/filter flow, create, update, delete, validation, and narrow-layout behavior
15. update `README.md`, `docs/README.md`, `docs/architecture/overview.md`, `docs/operations/local-development.md`, `docs/api/overview.md`, and `AGENTS.md`
16. keep host-run and container-run environment defaults separate so local commands use `localhost` while Compose containers use service names

## TUI Notes

- launch locally with `uv run bookshelf tui`
- launch in Docker with `docker compose --profile tools run --rm cli tui`
- initial filter controls expose `status`, `category`, `format`, and `name_contains`
- the initial query experience uses the existing default service sort and next/previous page navigation
- long-form notes can be edited inline or handed off to `$EDITOR` when available in the runtime environment
- in Dockerized runs, local thumbnail files must come from `/app/imports`

## Docker Notes

- keep one application image for API, CLI, and TUI
- reuse the existing Compose tools profile rather than adding a separate deployment path
- mount host `./imports` to `/app/imports` for container-visible thumbnail files
- document that arbitrary host file paths are not visible inside the container
- keep migrations and service bootstrapping aligned with the existing entrypoint pattern
- keep `.env.example` focused on host-run commands and `.env.docker` focused on Compose service names
- keep `.env.docker` committed only while it contains non-secret bootstrap defaults

## Current Progress

- added `Textual` and created the initial `src/bookshelf/tui/` adapter shell
- added `bookshelf tui`, `make tui`, and `make docker-tui`
- implemented the first real library screen with a paginated book list, selected-book detail pane, and footer help
- connected TUI filters for `status`, `category`, `format`, and `name_contains`
- implemented previous and next page navigation over the shared query service
- implemented create, update, and delete flows through modal dialogs over shared services
- implemented inline note editing plus external `$EDITOR` handoff with graceful fallback when `$EDITOR` is missing or suspend is unsupported
- wired the TUI through the shared service dependency builders so thumbnail imports use configured storage
- implemented thumbnail handling for URL imports and local-path imports in the TUI form
- fixed manual refresh to reload page 1 so externally created books are visible again
- fixed the full-screen layout so the filter bar no longer collapses the visible library list pane in normal terminal sizes
- mounted repo `./imports` to `/app/imports` for Dockerized CLI and TUI thumbnail-path imports
- expanded TUI tests for refresh behavior, editor handoff, thumbnail create flow, and normal-terminal layout visibility
- added CLI and TUI tests for empty state, list rendering, filters, page navigation, and CRUD behavior
- updated local and Docker environment defaults so host-run commands use `.env` from `.env.example` and Compose services use `.env.docker`
- corrected the initial Alembic migration to use PostgreSQL enum types without duplicate creation during upgrade

## Findings

- `.env.example` could not serve both host-run and container-run workflows because local commands need `localhost` while Compose containers need service names such as `postgres` and `minio`
- container-created workspace virtual environments can break local `uv` commands due to ownership and interpreter path mismatches; verification should avoid writing a container-owned `.venv` into the shared repo
- the initial migration needed explicit PostgreSQL enum handling to avoid duplicate enum creation during `make migrate`
- TUI refresh should return to page 1 because preserved pagination can hide newly created books from the visible result set
- adapter defaults must reuse the shared dependency builders, otherwise thumbnail uploads fail because storage is not configured
- full-screen terminal layouts need explicit height constraints for filter chrome, otherwise the main content panes can render with effectively zero visible height

## Exit Criteria

- `bookshelf tui` exists and launches locally
- `bookshelf tui` works through the existing Docker tools workflow
- the TUI shows paginated saved books with initial filters and selection details
- the TUI supports create, update, and delete using shared services
- note editing works inline and through `$EDITOR` when available
- Dockerized local thumbnail imports work from `/app/imports`
- tests cover the primary TUI workflows and adapter error states
- documentation explains local and Docker TUI usage without contradicting existing CLI/API workflows

## Outcome

- completed
- local `make migrate`, `make seed-taxonomy`, `make test`, and `make lint` are working with the corrected host-run environment settings
- the TUI now supports paginated browsing, filtering, create/update/delete flows, inline note editing, `$EDITOR` handoff, and thumbnail imports through the shared service layer
- the TUI is launchable through both CLI and Make targets locally and through the Docker tools workflow
- Docker tools runs mount `./imports` to `/app/imports` for container-visible local thumbnail files
- full verification is green with `22 passed`

## Retrospective Notes

- separate host and container environment files were necessary once both local `uv` workflows and Dockerized adapter runs became first-class paths
- migration verification against a real PostgreSQL instance exposed an enum-creation bug that unit tests alone did not cover
- refreshing paginated UIs after external writes needs an explicit page-reset policy, otherwise users can miss freshly created records
- headless widget-state checks were not enough on their own; layout regressions needed explicit size-based tests against realistic terminal dimensions
