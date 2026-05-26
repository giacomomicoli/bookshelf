# Sprint 003 - TUI UX Refresh and Multi-Author Books

## Status

Completed

## Goal

Fix the current TUI action-bar visibility issue, make core TUI list updates happen immediately after filter and CRUD actions, and extend the book model to support multiple authors.

## Scope

- fix the TUI filter and action-bar layout so button labels remain visible in normal terminal sizes
- keep the action controls only slightly larger if needed to restore readable labels
- refresh the TUI book list immediately when `status`, `category`, or `format` filters change
- refresh the TUI book list immediately when the name filter is submitted
- refresh the TUI book list immediately after create, update, and delete flows
- keep TUI behavior as a thin adapter over shared services
- add multi-author book metadata across the shared domain, persistence model, CLI, TUI, and API
- preserve entered author order on the book record
- add automated tests for the new TUI behavior and multi-author support
- update end-user and project documentation

## Out of Scope

- new TUI filters beyond the current `status`, `category`, `format`, and `name_contains` set
- author-specific query filters or sorting
- a normalized author table or separate person entity
- author deduplication or canonicalization rules
- live search on every keystroke in the TUI name filter

## Decisions

- `ADR-005`: shared service layer remains the only place for business logic
- `ADR-016`: API-specific schemas remain separate from internal service DTOs
- `ADR-017`: shared query filters remain the source of truth for TUI filtering
- `ADR-019`: the TUI remains a thin Textual adapter launched as `bookshelf tui`
- `ADR-020`: authors are stored as an ordered multi-value field on books

## Tasks

1. adjust the TUI layout in `src/bookshelf/tui/app.py` so the action buttons no longer overlap the main content or hide their labels at normal terminal sizes
2. keep the TUI footer help and content panes visible after the layout change
3. wire TUI filter `Select` changes for `status`, `category`, and `format` to reload page 1 immediately
4. keep name-filter submit behavior aligned with the new immediate-refresh model
5. make TUI create, update, and delete flows reload the visible list without requiring manual refresh
6. choose consistent page-reset and selection behavior for post-write refreshes so newly created books are visible and edited books remain discoverable
7. extend the book database model and migration history to store ordered authors on each book
8. extend internal book DTOs and service logic to accept, persist, update, and return multiple authors
9. update CLI add and update workflows to collect and edit multiple authors
10. update TUI create and edit forms plus detail rendering to support multiple authors
11. update API request and response schemas to expose authors as a list
12. add or update tests for TUI layout, reactive filtering, post-write refresh behavior, and multi-author CRUD flows across service, CLI, TUI, and API layers
13. update `README.md`, `docs/README.md`, `docs/domain/books.md`, `docs/api/overview.md`, `docs/architecture/overview.md`, and `docs/operations/local-development.md`

## TUI Notes

- manual refresh can remain available on `r`, but it should no longer be required for the common in-app flows covered by this sprint
- filter changes should reload the first page to avoid stale pagination and empty-looking result sets after a narrower query
- create, update, and delete should leave the library view in a coherent state without extra user steps
- layout verification should continue to use realistic full-screen terminal dimensions rather than only widget-state assertions

## Data Notes

- authors are stored as an ordered list of strings on the book record
- a book may have zero, one, or many authors
- no separate author entity is introduced in this sprint
- no author normalization, merge, or search rules are added in this sprint

## API Notes

- API request and response contracts must expose `authors` as a list field
- API-specific schemas must continue to exclude CLI-only fields such as `thumbnail_path`

## Exit Criteria

- the TUI shows readable action labels at normal terminal sizes
- changing a supported TUI filter updates the list without pressing `Apply filters`
- creating, updating, or deleting a book in the TUI updates the visible list without pressing `r`
- books support ordered multi-author metadata across persistence, services, CLI, TUI, and API
- tests cover the new behavior across the affected layers
- documentation reflects the new TUI behavior and book metadata contract

## Outcome

- completed
- books now store ordered multi-author metadata across the database model, internal DTOs, shared services, CLI, TUI, and API
- added migration `202605261030_add_authors_to_books.py` to introduce the new `authors` field in persisted book records
- the TUI now refreshes immediately when supported filters change and after create, update, and delete flows, while keeping manual `r` refresh available
- the TUI layout now keeps the action bar readable at normal terminal sizes without obscuring the main panes
- tests were expanded for multi-author CRUD coverage plus TUI layout and reactive refresh behavior
- documentation was updated to reflect the new author contract and the reduced need for manual refresh in the TUI
- verification passed with `uv run pytest` and `uv run ruff check .`

## Retrospective Notes

- reactive terminal UI behavior still benefits from explicit page-reset rules after writes, especially when pagination and filters are active at the same time
- storing authors as an ordered list kept the change small while still supporting common real-world book metadata cases
- size-based TUI tests remain important because label overlap and clipped controls are not reliably caught by widget-state assertions alone
