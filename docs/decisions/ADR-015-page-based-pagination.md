# ADR-015: Use Page-Based Pagination for Book Queries

## Status

Accepted

## Decision

Expose book query pagination through `page` and `page_size` parameters and return pagination metadata in the response payload.

## Consequences

- API consumers receive a UI-friendly pagination contract.
- Query services must calculate total item counts and total pages.
