# Architecture Overview

## Summary

Bookshelf uses a modular monolith structure with shared application services that are called by both the CLI and the API. This keeps business logic in one place while allowing the current manual workflow to evolve into a future graphical client.

## Layers

- `api`: FastAPI routes and request/response schemas
- `cli`: Typer commands and interactive prompts
- `services`: application use-cases
- `repositories`: persistence logic
- `domain`: entities, enums, and validation rules
- `storage`: thumbnail import and object storage
- `db`: SQLAlchemy models, session management, and migrations
- `config`: settings and environment handling

## Boundaries

- CLI commands must call services rather than perform direct persistence work.
- API routes must call services rather than duplicate command logic.
- Core design changes require ADRs.

## Storage

- PostgreSQL stores structured book and taxonomy data.
- MinIO stores thumbnail assets imported from local files or remote URLs.

## Current Application Scope

- taxonomy seed loading from YAML
- interactive CLI book creation
- book query, update, and deletion workflows
- thumbnail replacement and cleanup lifecycle
- paginated REST API with dedicated HTTP schemas
