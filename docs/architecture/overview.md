# Architecture Overview

## Summary

Bookshelf uses a modular monolith structure with shared application services that are called by the CLI, the TUI, and the API. This keeps business logic in one place while allowing new adapters to be added without rewriting core workflows.

## Layers

- `api`: FastAPI routes and request/response schemas
- `cli`: Typer commands and interactive prompts
- `tui`: Textual full-screen terminal interface
- `services`: application use-cases
- `repositories`: persistence logic
- `domain`: entities, enums, and validation rules
- `storage`: thumbnail import and object storage
- `db`: SQLAlchemy models, session management, and migrations
- `config`: settings and environment handling

## Boundaries

- CLI commands must call services rather than perform direct persistence work.
- TUI screens must call services rather than duplicate command logic.
- API routes must call services rather than duplicate command logic.
- Core design changes require ADRs.

## Storage

- PostgreSQL stores structured book and taxonomy data.
- MinIO stores thumbnail assets imported from local files or remote URLs.

## Current Application Scope

- taxonomy seed loading from YAML
- interactive CLI book creation and editing with multi-author metadata
- book query, update, and deletion workflows
- full-screen TUI for paginated browsing, reactive filter updates, CRUD flows, note editing, and thumbnail imports
- thumbnail replacement and cleanup lifecycle
- paginated REST API with dedicated HTTP schemas

## Recent Delivery

- Sprint 002 delivered the Docker-first Textual TUI adapter, the `/app/imports` workflow for container-visible local thumbnail imports, and the corrected full-screen layout that keeps the library panes visible in normal terminal sizes.
