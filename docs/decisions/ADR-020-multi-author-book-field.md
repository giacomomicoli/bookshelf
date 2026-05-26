# ADR-020: Store Authors as a Multi-Value Field on Books

## Status

Accepted

## Decision

Represent authors as an ordered list of free-text names stored directly on the book record.

## Consequences

- Books can support one or many authors without introducing a separate person entity.
- CLI, TUI, API, services, persistence, and documentation must treat authors as a list rather than a single string.
- Author order is preserved as entered by the user.
- This decision does not add author-specific filtering, search, normalization, or deduplication rules.
