# ADR-019: Add a Docker-First Textual TUI Adapter Through `bookshelf tui`

## Status

Accepted

## Decision

Add a full-screen terminal UI as a third adapter alongside the CLI and API.

Implement the TUI with `Textual` under `src/bookshelf/tui/`.

Launch the TUI from the existing Typer command surface as `bookshelf tui`.

Keep the TUI as a thin adapter over shared services rather than making it a client of the local HTTP API.

For containerized runs, reuse the existing application image and Compose tools workflow. Local thumbnail file imports in Dockerized CLI or TUI sessions must use a mounted host directory exposed at `/app/imports` inside the container.

Keep separate committed environment templates for host-run and container-run workflows:

- `.env.example` remains the host-run template and uses `localhost` service addresses
- `.env.docker` remains the Docker Compose bootstrap config and uses service names such as `postgres` and `minio`

`.env.docker` stays committed because it contains only non-secret local development defaults. Real secrets must stay in ignored local environment files or deployment-specific configuration.

The first TUI release exposes filter controls for `status`, `category`, `format`, and `name_contains`, and uses next/previous navigation over the existing paginated query contract.

## Consequences

- business logic stays in shared services and repositories, consistent with `ADR-005`
- the TUI can reuse existing validation, taxonomy resolution, query, update, delete, and thumbnail lifecycle behavior
- the HTTP API remains an external integration surface, not an internal dependency of the TUI
- host-run and container-run commands no longer share a single environment template, which avoids invalid hostname resolution in local `uv` workflows
- Dockerized local thumbnail imports depend on container-visible paths; arbitrary host paths are not valid inside the container
- `.env.docker` must remain free of secrets because it is committed as part of the public repo bootstrap workflow
- operations and README documentation must describe the mounted `./imports` to `/app/imports` workflow
- adapter tests should focus on TUI behavior and service integration rather than duplicate service-layer rules
- this decision refines `ADR-013` for containerized adapter runs without changing the allowed thumbnail sources
