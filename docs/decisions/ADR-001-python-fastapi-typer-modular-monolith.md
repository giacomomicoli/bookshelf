# ADR-001: Adopt Python + FastAPI + Typer Modular Monolith

## Status

Accepted

## Decision

Use Python for the implementation language, FastAPI for the HTTP API, and Typer for the CLI. Structure the application as a modular monolith with shared services.

## Consequences

- CLI and API can share the same application layer.
- Future UI integration can call the API without a rewrite of the core logic.
