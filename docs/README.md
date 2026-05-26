# Bookshelf Docs

## Purpose

Bookshelf is a CLI-first, TUI-enabled, API-ready utility for storing and organizing book metadata in a way that mirrors a physical bookshelf. Categories represent shelf compartments, with optional sub-categories for finer grouping.

## Read Order

1. `docs/architecture/overview.md`
2. `docs/decisions/`
3. `docs/domain/books.md`
4. `docs/api/overview.md`
5. `docs/operations/local-development.md`
6. `docs/sprints/active/` for follow-up work after bootstrap

## Index

- `docs/architecture/`: high-level system structure
- `docs/decisions/`: ADRs and design decisions
- `docs/domain/`: domain rules and entity definitions
- `docs/api/`: API surface and controller expectations
- `docs/operations/`: local development and runtime workflows
- `docs/sprints/active/`: active sprint documents
- `docs/sprints/archive/`: completed sprint documents

## Environment Notes

- `.env.example` is the committed local host-run template and is meant to be copied to `.env`.
- `.env.docker` is the committed Docker Compose bootstrap config and is kept in git because it contains only non-secret local development defaults.
- local host-run commands use `localhost` service addresses, while Compose containers use service names such as `postgres` and `minio`.

## Workflow

The bootstrap implementation establishes the first working system. Every follow-up feature or change should be driven by an active sprint document and moved to archive once complete.

Any open question or decision that impacts the core design must be captured as an ADR in `docs/decisions/` before implementation continues.

Current active follow-up work:

- none currently

Recent follow-up references:

- `docs/sprints/archive/2026-05-26-sprint-003-tui-ux-and-multi-author-books.md`
- `docs/decisions/ADR-020-multi-author-book-field.md`
- `docs/sprints/archive/2026-05-26-sprint-002-docker-first-tui.md`
- `docs/decisions/ADR-019-docker-first-tui-adapter-and-mounted-imports.md`
