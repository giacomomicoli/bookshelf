from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, model_validator

from bookshelf.domain.enums import BookFormat, BookSortOption, ReadingStatus
from bookshelf.domain.schemas import (
    BookCreateInput,
    BookQueryInput,
    BookQueryResult,
    BookSchema,
    BookUpdateInput,
    TaxonomyCategorySchema,
)


class ApiCategoryResponse(BaseModel):
    id: UUID
    slug: str
    name: str

    @classmethod
    def from_service(cls, payload) -> ApiCategoryResponse:
        return cls(id=payload.id, slug=payload.slug, name=payload.name)


class ApiSubCategoryResponse(BaseModel):
    id: UUID
    category_id: UUID
    slug: str
    name: str

    @classmethod
    def from_service(cls, payload) -> ApiSubCategoryResponse:
        return cls(
            id=payload.id,
            category_id=payload.category_id,
            slug=payload.slug,
            name=payload.name,
        )


class ApiTaxonomyCategoryResponse(ApiCategoryResponse):
    subcategories: list[ApiSubCategoryResponse] = Field(default_factory=list)

    @classmethod
    def from_service(cls, payload: TaxonomyCategorySchema) -> ApiTaxonomyCategoryResponse:
        return cls(
            id=payload.id,
            slug=payload.slug,
            name=payload.name,
            subcategories=[
                ApiSubCategoryResponse.from_service(item)
                for item in payload.subcategories
            ],
        )


class ApiBookResponse(BaseModel):
    id: UUID
    name: str
    category: ApiCategoryResponse
    sub_category: ApiSubCategoryResponse | None = None
    purchase_urls: list[str]
    thumbnail_object_key: str | None = None
    thumbnail_source_url: str | None = None
    published_on: date | None = None
    edition: str | None = None
    format: BookFormat | None = None
    page_length: int | None = None
    reading_status: ReadingStatus
    note: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_service(cls, payload: BookSchema) -> ApiBookResponse:
        return cls(
            id=payload.id,
            name=payload.name,
            category=ApiCategoryResponse.from_service(payload.category),
            sub_category=(
                ApiSubCategoryResponse.from_service(payload.sub_category)
                if payload.sub_category is not None
                else None
            ),
            purchase_urls=payload.purchase_urls,
            thumbnail_object_key=payload.thumbnail_object_key,
            thumbnail_source_url=payload.thumbnail_source_url,
            published_on=payload.published_on,
            edition=payload.edition,
            format=payload.format,
            page_length=payload.page_length,
            reading_status=payload.reading_status,
            note=payload.note,
            created_at=payload.created_at,
            updated_at=payload.updated_at,
        )


class ApiPaginatedBooksResponse(BaseModel):
    items: list[ApiBookResponse]
    page: int
    page_size: int
    total_items: int
    total_pages: int

    @classmethod
    def from_service(cls, payload: BookQueryResult) -> ApiPaginatedBooksResponse:
        return cls(
            items=[ApiBookResponse.from_service(item) for item in payload.items],
            page=payload.page,
            page_size=payload.page_size,
            total_items=payload.total_items,
            total_pages=payload.total_pages,
        )


class ApiBookCreateRequest(BaseModel):
    name: str
    category_slug: str
    sub_category_slug: str | None = None
    purchase_urls: list[HttpUrl] = Field(default_factory=list)
    thumbnail_url: HttpUrl | None = None
    published_on: date | None = None
    edition: str | None = None
    format: BookFormat | None = None
    page_length: int | None = Field(default=None, ge=1)
    reading_status: ReadingStatus = ReadingStatus.UNREAD
    note: str | None = None

    def to_service_input(self) -> BookCreateInput:
        return BookCreateInput(
            name=self.name,
            category_slug=self.category_slug,
            sub_category_slug=self.sub_category_slug,
            purchase_urls=self.purchase_urls,
            thumbnail_url=self.thumbnail_url,
            published_on=self.published_on,
            edition=self.edition,
            format=self.format,
            page_length=self.page_length,
            reading_status=self.reading_status,
            note=self.note,
        )


class ApiBookUpdateRequest(BaseModel):
    name: str | None = None
    category_slug: str | None = None
    sub_category_slug: str | None = None
    clear_sub_category: bool = False
    purchase_urls: list[HttpUrl] | None = None
    clear_purchase_urls: bool = False
    thumbnail_url: HttpUrl | None = None
    clear_thumbnail: bool = False
    published_on: date | None = None
    clear_published_on: bool = False
    edition: str | None = None
    clear_edition: bool = False
    format: BookFormat | None = None
    clear_format: bool = False
    page_length: int | None = Field(default=None, ge=1)
    clear_page_length: bool = False
    reading_status: ReadingStatus | None = None
    note: str | None = None
    clear_note: bool = False

    @model_validator(mode="after")
    def validate_flags(self) -> ApiBookUpdateRequest:
        if self.clear_sub_category and self.sub_category_slug is not None:
            raise ValueError("cannot provide sub_category_slug when clear_sub_category is true")
        if self.clear_purchase_urls and self.purchase_urls is not None:
            raise ValueError("cannot provide purchase_urls when clear_purchase_urls is true")
        if self.clear_thumbnail and self.thumbnail_url is not None:
            raise ValueError("cannot provide thumbnail_url when clear_thumbnail is true")
        if self.clear_published_on and self.published_on is not None:
            raise ValueError("cannot provide published_on when clear_published_on is true")
        if self.clear_edition and self.edition is not None:
            raise ValueError("cannot provide edition when clear_edition is true")
        if self.clear_format and self.format is not None:
            raise ValueError("cannot provide format when clear_format is true")
        if self.clear_page_length and self.page_length is not None:
            raise ValueError("cannot provide page_length when clear_page_length is true")
        if self.clear_note and self.note is not None:
            raise ValueError("cannot provide note when clear_note is true")
        return self

    def to_service_input(self) -> BookUpdateInput:
        return BookUpdateInput(
            name=self.name,
            category_slug=self.category_slug,
            sub_category_slug=self.sub_category_slug,
            clear_sub_category=self.clear_sub_category,
            purchase_urls=self.purchase_urls,
            clear_purchase_urls=self.clear_purchase_urls,
            thumbnail_url=self.thumbnail_url,
            clear_thumbnail=self.clear_thumbnail,
            published_on=self.published_on,
            clear_published_on=self.clear_published_on,
            edition=self.edition,
            clear_edition=self.clear_edition,
            format=self.format,
            clear_format=self.clear_format,
            page_length=self.page_length,
            clear_page_length=self.clear_page_length,
            reading_status=self.reading_status,
            note=self.note,
            clear_note=self.clear_note,
        )


class ApiBookQueryParams(BaseModel):
    status: ReadingStatus | None = None
    category: str | None = None
    sub_category: str | None = None
    format: BookFormat | None = None
    name_contains: str | None = None
    published_before: date | None = None
    published_after: date | None = None
    sort: BookSortOption = BookSortOption.CREATED_AT_DESC
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def validate_date_range(self) -> ApiBookQueryParams:
        if (
            self.published_before is not None
            and self.published_after is not None
            and self.published_after > self.published_before
        ):
            raise ValueError("published_after cannot be later than published_before")
        return self

    def to_service_input(self) -> BookQueryInput:
        return BookQueryInput(
            status=self.status,
            category_slug=self.category,
            sub_category_slug=self.sub_category,
            format=self.format,
            name_contains=self.name_contains,
            published_before=self.published_before,
            published_after=self.published_after,
            sort=self.sort,
            page=self.page,
            page_size=self.page_size,
        )
