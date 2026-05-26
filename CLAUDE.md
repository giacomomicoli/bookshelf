# CLAUDE.md

## Purpose

This file routes coding agents through the project documentation and working rules.

## Required Read Order

1. `docs/README.md`
2. `docs/architecture/overview.md`
3. relevant ADRs in `docs/decisions/`
4. `docs/domain/books.md`
5. active sprint document in `docs/sprints/active/` for all post-bootstrap work

## Core Rules

- CLI and API are adapters only. Shared business logic belongs in services.
- Reuse existing services before adding new entrypoints.
- Any open question or decision that impacts the core design must be documented as an ADR in `docs/decisions/` before implementation continues.
- Keep taxonomy changes aligned with the versioned YAML seed file unless an ADR changes that rule.
- Completed sprints must not remain in `docs/sprints/active/`; move them to `docs/sprints/archive/` when done.

## Workflow

- Bootstrap is the only implementation phase allowed to proceed without an active sprint document.
- All follow-up work must be driven by a sprint document with scope, tasks, ADR links, exit criteria, and retrospective notes.
- Update documentation when changing architecture, domain rules, operations, or API behavior.

## Repo Map

- `src/bookshelf/api/`: FastAPI entrypoints
- `src/bookshelf/cli/`: Typer CLI entrypoints
- `src/bookshelf/services/`: application use-cases
- `src/bookshelf/repositories/`: persistence logic
- `src/bookshelf/db/`: SQLAlchemy models and session setup
- `src/bookshelf/storage/`: thumbnail storage logic
- `src/bookshelf/seeds/`: versioned seed files
- `docs/decisions/`: ADRs
- `docs/sprints/`: sprint workflow
