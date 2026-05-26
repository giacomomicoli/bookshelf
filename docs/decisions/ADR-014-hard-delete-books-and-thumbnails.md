# ADR-014: Hard Delete Books and Remove Thumbnail Objects

## Status

Accepted

## Decision

When a book is deleted, remove the database record and clean up the associated thumbnail object from MinIO.

## Consequences

- Book deletion leaves no orphaned book rows.
- Thumbnail cleanup is part of the book lifecycle and must be handled by the service layer.
