# ADR-016: Separate API Schemas from Internal Service DTOs

## Status

Accepted

## Decision

Use API-specific request and response schemas instead of exposing internal service DTOs directly from FastAPI routes.

## Consequences

- The HTTP contract can evolve independently from CLI and service concerns.
- CLI-only fields such as local thumbnail file paths stay outside the API surface.
