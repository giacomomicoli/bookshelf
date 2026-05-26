from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from bookshelf.api.dependencies import get_db_session
from bookshelf.api.schemas import (
    ApiBookCreateRequest,
    ApiBookQueryParams,
    ApiBookResponse,
    ApiBookUpdateRequest,
    ApiPaginatedBooksResponse,
    ApiTaxonomyCategoryResponse,
)
from bookshelf.services.dependencies import build_book_service, build_taxonomy_service

SessionDependency = Annotated[Session, Depends(get_db_session)]
BookQueryDependency = Annotated[ApiBookQueryParams, Query()]


def create_app() -> FastAPI:
    app = FastAPI(title="Bookshelf", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/books", response_model=ApiPaginatedBooksResponse)
    def list_books(
        session: SessionDependency,
        params: BookQueryDependency,
    ) -> ApiPaginatedBooksResponse:
        service = build_book_service(session)
        result = service.query_books(params.to_service_input())
        return ApiPaginatedBooksResponse.from_service(result)

    @app.get("/api/v1/books/{book_id}", response_model=ApiBookResponse)
    def get_book(book_id: UUID, session: SessionDependency) -> ApiBookResponse:
        service = build_book_service(session)
        try:
            return ApiBookResponse.from_service(service.get_book(book_id))
        except LookupError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.post(
        "/api/v1/books",
        response_model=ApiBookResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_book(
        payload: ApiBookCreateRequest,
        session: SessionDependency,
    ) -> ApiBookResponse:
        service = build_book_service(session)
        try:
            created = service.create_book(payload.to_service_input())
            return ApiBookResponse.from_service(created)
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.errors(),
            ) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.patch("/api/v1/books/{book_id}", response_model=ApiBookResponse)
    def update_book(
        book_id: UUID,
        payload: ApiBookUpdateRequest,
        session: SessionDependency,
    ) -> ApiBookResponse:
        service = build_book_service(session)
        try:
            updated = service.update_book(book_id, payload.to_service_input())
            return ApiBookResponse.from_service(updated)
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.errors(),
            ) from exc
        except LookupError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.delete("/api/v1/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_book(book_id: UUID, session: SessionDependency) -> None:
        service = build_book_service(session)
        try:
            service.delete_book(book_id)
        except LookupError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.get("/api/v1/categories", response_model=list[ApiTaxonomyCategoryResponse])
    def list_categories(session: SessionDependency) -> list[ApiTaxonomyCategoryResponse]:
        service = build_taxonomy_service(session)
        return [
            ApiTaxonomyCategoryResponse.from_service(item)
            for item in service.list_categories()
        ]

    return app
