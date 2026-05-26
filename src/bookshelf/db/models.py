from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from bookshelf.domain.enums import BookFormat, ReadingStatus


def enum_values(enum_class: type[BookFormat] | type[ReadingStatus]) -> list[str]:
    return [member.value for member in enum_class]


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    subcategories: Mapped[list[SubCategory]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )
    books: Mapped[list[Book]] = relationship(back_populates="category")


class SubCategory(Base, TimestampMixin):
    __tablename__ = "sub_categories"
    __table_args__ = (
        UniqueConstraint("category_id", "slug", name="uq_sub_categories_category_slug"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    category: Mapped[Category] = relationship(back_populates="subcategories")
    books: Mapped[list[Book]] = relationship(back_populates="sub_category")


class Book(Base, TimestampMixin):
    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    sub_category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sub_categories.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    authors: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    purchase_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    thumbnail_object_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumbnail_source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    edition: Mapped[str | None] = mapped_column(String(255), nullable=True)
    format: Mapped[BookFormat | None] = mapped_column(
        Enum(BookFormat, name="book_format", values_callable=enum_values)
    )
    page_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reading_status: Mapped[ReadingStatus] = mapped_column(
        Enum(ReadingStatus, name="reading_status", values_callable=enum_values),
        nullable=False,
        default=ReadingStatus.UNREAD,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped[Category] = relationship(back_populates="books")
    sub_category: Mapped[SubCategory | None] = relationship(back_populates="books")
