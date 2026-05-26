# API Overview

The API is still intentionally small, but it now supports the first full book management workflow needed by a future graphical client.

## Endpoints

- `GET /health`
- `GET /api/v1/books`
- `GET /api/v1/books/{book_id}`
- `POST /api/v1/books`
- `PATCH /api/v1/books/{book_id}`
- `DELETE /api/v1/books/{book_id}`
- `GET /api/v1/categories`

## Query Contract

`GET /api/v1/books` returns a paginated response envelope:

- `items`
- `page`
- `page_size`
- `total_items`
- `total_pages`

Supported query parameters:

- `status`
- `category`
- `sub_category`
- `format`
- `name_contains`
- `published_before`
- `published_after`
- `sort`
- `page`
- `page_size`

## Schema Rule

FastAPI routes use API-specific request and response schemas. Internal service DTOs remain separate so CLI-only fields such as local thumbnail paths are not part of the public HTTP contract.

## Design Rule

Routes remain thin and delegate business logic to shared services.
