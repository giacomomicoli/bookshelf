from __future__ import annotations

from math import ceil
from uuid import UUID

import httpx
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy.orm import Session

from bookshelf.db.models import Book
from bookshelf.domain.enums import ReadingStatus
from bookshelf.domain.schemas import (
    BookCreateInput,
    BookQueryInput,
    BookQueryResult,
    BookSchema,
    BookUpdateInput,
)
from bookshelf.repositories.books import BookRepository, TaxonomyRepository
from bookshelf.storage.thumbnails import ThumbnailStorage


class BookService:
    def __init__(self, session: Session, thumbnail_storage: ThumbnailStorage | None = None) -> None:
        self.session = session
        self.book_repository = BookRepository(session)
        self.taxonomy_repository = TaxonomyRepository(session)
        self.thumbnail_storage = thumbnail_storage

    def create_book(self, payload: BookCreateInput) -> BookSchema:
        category, sub_category = self._resolve_taxonomy(
            category_slug=payload.category_slug,
            sub_category_slug=payload.sub_category_slug,
        )
        thumbnail_object_key, thumbnail_source_url = self._upload_thumbnail(
            thumbnail_path=payload.thumbnail_path,
            thumbnail_url=str(payload.thumbnail_url) if payload.thumbnail_url else None,
        )

        book = Book(
            name=payload.name,
            authors=payload.authors,
            category_id=category.id,
            sub_category_id=sub_category.id if sub_category else None,
            purchase_urls=[str(url) for url in payload.purchase_urls],
            thumbnail_object_key=thumbnail_object_key,
            thumbnail_source_url=thumbnail_source_url,
            published_on=payload.published_on,
            edition=payload.edition,
            format=payload.format,
            page_length=payload.page_length,
            reading_status=payload.reading_status,
            note=payload.note,
        )
        try:
            self.book_repository.add(book)
            self.session.commit()
        except Exception:
            self.session.rollback()
            if thumbnail_object_key is not None:
                self._delete_thumbnail_object(thumbnail_object_key, suppress_errors=True)
            raise

        return self.get_book(book.id)

    def get_book(self, book_id: UUID) -> BookSchema:
        return self._to_schema(self._get_book_or_raise(book_id))

    def query_books(self, query_input: BookQueryInput) -> BookQueryResult:
        books, total_items = self.book_repository.query(query_input)
        total_pages = ceil(total_items / query_input.page_size) if total_items else 0
        return BookQueryResult(
            items=[self._to_schema(book) for book in books],
            page=query_input.page,
            page_size=query_input.page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

    def update_book(self, book_id: UUID, payload: BookUpdateInput) -> BookSchema:
        book = self._get_book_or_raise(book_id)
        category, sub_category = self._resolve_updated_taxonomy(book=book, payload=payload)

        previous_thumbnail_key = book.thumbnail_object_key
        new_thumbnail_key = None
        new_thumbnail_source_url = None
        if payload.thumbnail_path or payload.thumbnail_url:
            new_thumbnail_key, new_thumbnail_source_url = self._upload_thumbnail(
                thumbnail_path=payload.thumbnail_path,
                thumbnail_url=str(payload.thumbnail_url) if payload.thumbnail_url else None,
            )

        if payload.name is not None:
            book.name = payload.name

        if payload.clear_authors:
            book.authors = []
        elif payload.authors is not None:
            book.authors = payload.authors

        if payload.category_slug is not None:
            book.category_id = category.id

        if (
            payload.category_slug is not None
            or payload.sub_category_slug is not None
            or payload.clear_sub_category
        ):
            book.sub_category_id = sub_category.id if sub_category else None

        if payload.clear_purchase_urls:
            book.purchase_urls = []
        elif payload.purchase_urls is not None:
            book.purchase_urls = [str(url) for url in payload.purchase_urls]

        if payload.clear_thumbnail:
            book.thumbnail_object_key = None
            book.thumbnail_source_url = None
        elif new_thumbnail_key is not None:
            book.thumbnail_object_key = new_thumbnail_key
            book.thumbnail_source_url = new_thumbnail_source_url

        if payload.clear_published_on:
            book.published_on = None
        elif payload.published_on is not None:
            book.published_on = payload.published_on

        if payload.clear_edition:
            book.edition = None
        elif payload.edition is not None:
            book.edition = payload.edition

        if payload.clear_format:
            book.format = None
        elif payload.format is not None:
            book.format = payload.format

        if payload.clear_page_length:
            book.page_length = None
        elif payload.page_length is not None:
            book.page_length = payload.page_length

        if payload.reading_status is not None:
            book.reading_status = payload.reading_status

        if payload.clear_note:
            book.note = None
        elif payload.note is not None:
            book.note = payload.note

        try:
            self.book_repository.save(book)
            self.session.commit()
        except Exception:
            self.session.rollback()
            if new_thumbnail_key is not None:
                self._delete_thumbnail_object(new_thumbnail_key, suppress_errors=True)
            raise

        if previous_thumbnail_key and previous_thumbnail_key != book.thumbnail_object_key:
            self._delete_thumbnail_object(previous_thumbnail_key)

        return self.get_book(book_id)

    def delete_book(self, book_id: UUID) -> None:
        book = self._get_book_or_raise(book_id)
        thumbnail_key = book.thumbnail_object_key

        try:
            self.book_repository.delete(book)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        if thumbnail_key is not None:
            self._delete_thumbnail_object(thumbnail_key)

    def list_books(self, *, status: ReadingStatus | None = None) -> list[BookSchema]:
        books = self.book_repository.list(status=status)
        return [self._to_schema(book) for book in books]

    def _get_book_or_raise(self, book_id: UUID) -> Book:
        book = self.book_repository.get(book_id)
        if book is None:
            raise LookupError(f"book not found: {book_id}")
        return book

    def _resolve_taxonomy(self, *, category_slug: str, sub_category_slug: str | None):
        category = self.taxonomy_repository.get_category_by_slug(category_slug)
        if category is None:
            raise ValueError(f"unknown category: {category_slug}")

        sub_category = None
        if sub_category_slug is not None:
            sub_category = self.taxonomy_repository.get_sub_category_by_slug_for_category(
                category_id=category.id,
                slug=sub_category_slug,
            )
            if sub_category is None:
                raise ValueError(f"unknown sub-category: {sub_category_slug}")

        return category, sub_category

    def _resolve_updated_taxonomy(self, *, book: Book, payload: BookUpdateInput):
        category = book.category
        if payload.category_slug is not None:
            category = self.taxonomy_repository.get_category_by_slug(payload.category_slug)
            if category is None:
                raise ValueError(f"unknown category: {payload.category_slug}")

        if payload.clear_sub_category:
            return category, None

        if payload.sub_category_slug is not None:
            sub_category = self.taxonomy_repository.get_sub_category_by_slug_for_category(
                category_id=category.id,
                slug=payload.sub_category_slug,
            )
            if sub_category is None:
                raise ValueError(f"unknown sub-category: {payload.sub_category_slug}")
            return category, sub_category

        if payload.category_slug is not None:
            return category, None

        return category, book.sub_category

    def _upload_thumbnail(
        self,
        *,
        thumbnail_path: str | None,
        thumbnail_url: str | None,
    ) -> tuple[str | None, str | None]:
        if thumbnail_path is None and thumbnail_url is None:
            return None, None

        storage = self._require_thumbnail_storage()
        try:
            if thumbnail_path is not None:
                return storage.upload_from_path(thumbnail_path)
            if thumbnail_url is not None:
                return storage.upload_from_url(thumbnail_url)
            return None, None
        except FileNotFoundError as exc:
            raise ValueError(str(exc)) from exc
        except httpx.HTTPError as exc:
            raise ValueError(f"failed to download thumbnail: {exc}") from exc
        except (BotoCoreError, ClientError) as exc:
            raise ValueError(f"failed to store thumbnail: {exc}") from exc

    def _delete_thumbnail_object(self, object_key: str, *, suppress_errors: bool = False) -> None:
        try:
            self._require_thumbnail_storage().delete_object(object_key)
        except (BotoCoreError, ClientError) as exc:
            if suppress_errors:
                return
            raise ValueError(f"failed to remove thumbnail: {exc}") from exc

    def _require_thumbnail_storage(self) -> ThumbnailStorage:
        if self.thumbnail_storage is None:
            raise ValueError("thumbnail storage is not configured")
        return self.thumbnail_storage

    def _to_schema(self, book: Book) -> BookSchema:
        return BookSchema.model_validate(book)
