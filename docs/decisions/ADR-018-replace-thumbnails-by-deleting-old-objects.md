# ADR-018: Replace Thumbnails by Deleting Old Objects

## Status

Accepted

## Decision

When a book thumbnail is replaced or cleared, delete the previously stored MinIO object after the new state has been persisted successfully.

## Consequences

- Thumbnail storage remains consistent with current book records.
- Update services must coordinate persistence and storage cleanup carefully.
