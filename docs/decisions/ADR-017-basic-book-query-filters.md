# ADR-017: Support Basic Book Query Filters and Sorting

## Status

Accepted

## Decision

The first query implementation supports filtering by reading status, category, sub-category, format, name substring, and publishing date range, plus explicit sorting options.

## Consequences

- Query logic must be centralized in shared services and repositories.
- CLI and API can expose the same query capabilities without duplicating business rules.
