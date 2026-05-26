from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from bookshelf.domain.enums import BookFormat, BookSortOption, ReadingStatus


class CategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str


class SubCategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category_id: UUID
    slug: str
    name: str


class TaxonomyCategorySchema(CategorySchema):
    subcategories: list[SubCategorySchema] = Field(default_factory=list)


class BookCreateInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    authors: list[str] = Field(default_factory=list)
    category_slug: str = Field(min_length=1, max_length=100)
    sub_category_slug: str | None = Field(default=None, max_length=100)
    purchase_urls: list[HttpUrl] = Field(default_factory=list)
    thumbnail_path: str | None = None
    thumbnail_url: HttpUrl | None = None
    published_on: date | None = None
    edition: str | None = Field(default=None, max_length=255)
    format: BookFormat | None = None
    page_length: int | None = Field(default=None, ge=1)
    reading_status: ReadingStatus = ReadingStatus.UNREAD
    note: str | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be blank")
        return stripped

    @field_validator("authors")
    @classmethod
    def normalize_authors(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        for author in value:
            stripped = author.strip()
            if not stripped:
                raise ValueError("authors cannot contain blank names")
            normalized.append(stripped)
        return normalized

    @field_validator("sub_category_slug", "edition", "note")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("thumbnail_path")
    @classmethod
    def normalize_thumbnail_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("purchase_urls", mode="before")
    @classmethod
    def default_purchase_urls(cls, value: Any) -> list[str]:
        return value or []

    @model_validator(mode="after")
    def validate_thumbnail_source(self) -> BookCreateInput:
        if self.thumbnail_path and self.thumbnail_url:
            raise ValueError("choose either thumbnail_path or thumbnail_url")
        return self


class BookUpdateInput(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    authors: list[str] | None = None
    clear_authors: bool = False
    category_slug: str | None = Field(default=None, max_length=100)
    sub_category_slug: str | None = Field(default=None, max_length=100)
    clear_sub_category: bool = False
    purchase_urls: list[HttpUrl] | None = None
    clear_purchase_urls: bool = False
    thumbnail_path: str | None = None
    thumbnail_url: HttpUrl | None = None
    clear_thumbnail: bool = False
    published_on: date | None = None
    clear_published_on: bool = False
    edition: str | None = Field(default=None, max_length=255)
    clear_edition: bool = False
    format: BookFormat | None = None
    clear_format: bool = False
    page_length: int | None = Field(default=None, ge=1)
    clear_page_length: bool = False
    reading_status: ReadingStatus | None = None
    note: str | None = None
    clear_note: bool = False

    @field_validator("name")
    @classmethod
    def validate_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be blank")
        return stripped

    @field_validator("category_slug")
    @classmethod
    def validate_category_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("category_slug cannot be blank")
        return stripped

    @field_validator("authors")
    @classmethod
    def normalize_optional_authors(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        normalized: list[str] = []
        for author in value:
            stripped = author.strip()
            if not stripped:
                raise ValueError("authors cannot contain blank names")
            normalized.append(stripped)
        return normalized

    @field_validator("sub_category_slug", "edition", "note")
    @classmethod
    def normalize_optional_update_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("thumbnail_path")
    @classmethod
    def normalize_update_thumbnail_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("purchase_urls", mode="before")
    @classmethod
    def default_update_purchase_urls(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        return value

    @model_validator(mode="after")
    def validate_clear_flags(self) -> BookUpdateInput:
        if self.clear_authors and self.authors is not None:
            raise ValueError("cannot provide authors when clear_authors is true")
        if self.clear_sub_category and self.sub_category_slug is not None:
            raise ValueError("cannot provide sub_category_slug when clear_sub_category is true")
        if self.clear_purchase_urls and self.purchase_urls is not None:
            raise ValueError("cannot provide purchase_urls when clear_purchase_urls is true")
        if self.thumbnail_path and self.thumbnail_url:
            raise ValueError("choose either thumbnail_path or thumbnail_url")
        if self.clear_thumbnail and (self.thumbnail_path or self.thumbnail_url):
            raise ValueError("cannot provide a thumbnail source when clear_thumbnail is true")
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


class BookQueryInput(BaseModel):
    status: ReadingStatus | None = None
    category_slug: str | None = Field(default=None, max_length=100)
    sub_category_slug: str | None = Field(default=None, max_length=100)
    format: BookFormat | None = None
    name_contains: str | None = Field(default=None, max_length=255)
    published_before: date | None = None
    published_after: date | None = None
    sort: BookSortOption = BookSortOption.CREATED_AT_DESC
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @field_validator("category_slug", "sub_category_slug", "name_contains")
    @classmethod
    def normalize_query_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_date_range(self) -> BookQueryInput:
        if (
            self.published_before is not None
            and self.published_after is not None
            and self.published_after > self.published_before
        ):
            raise ValueError("published_after cannot be later than published_before")
        return self


class BookSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    authors: list[str] = Field(default_factory=list)
    category: CategorySchema
    sub_category: SubCategorySchema | None = None
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


class BookQueryResult(BaseModel):
    items: list[BookSchema]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class TaxonomySeedSubCategory(BaseModel):
    slug: str
    name: str


class TaxonomySeedCategory(BaseModel):
    slug: str
    name: str
    subcategories: list[TaxonomySeedSubCategory] = Field(default_factory=list)


class TaxonomySeed(BaseModel):
    categories: list[TaxonomySeedCategory]
