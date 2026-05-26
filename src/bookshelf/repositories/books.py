from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from bookshelf.db.models import Book, Category, SubCategory
from bookshelf.domain.enums import BookSortOption, ReadingStatus
from bookshelf.domain.schemas import BookQueryInput


class BookRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, book: Book) -> Book:
        self.session.add(book)
        self.session.flush()
        self.session.refresh(book)
        return book

    def list(self, *, status: ReadingStatus | None = None) -> list[Book]:
        statement = (
            select(Book)
            .options(joinedload(Book.category), joinedload(Book.sub_category))
            .order_by(Book.created_at.desc())
        )
        if status is not None:
            statement = statement.where(Book.reading_status == status)
        return list(self.session.scalars(statement).unique())

    def get(self, book_id: UUID) -> Book | None:
        statement = (
            select(Book)
            .options(joinedload(Book.category), joinedload(Book.sub_category))
            .where(Book.id == book_id)
        )
        return self.session.scalars(statement).unique().one_or_none()

    def query(self, query_input: BookQueryInput) -> tuple[list[Book], int]:
        statement = (
            select(Book)
            .join(Book.category)
            .outerjoin(Book.sub_category)
            .options(joinedload(Book.category), joinedload(Book.sub_category))
        )
        count_statement = (
            select(func.count(Book.id))
            .select_from(Book)
            .join(Book.category)
            .outerjoin(Book.sub_category)
        )

        statement, count_statement = self._apply_query_filters(
            statement=statement,
            count_statement=count_statement,
            query_input=query_input,
        )
        statement = statement.order_by(*self._build_sort_order(query_input.sort))
        statement = statement.limit(query_input.page_size).offset(
            (query_input.page - 1) * query_input.page_size
        )

        items = list(self.session.scalars(statement).unique())
        total_items = self.session.scalar(count_statement) or 0
        return items, total_items

    def save(self, book: Book) -> Book:
        self.session.add(book)
        self.session.flush()
        self.session.refresh(book)
        return book

    def delete(self, book: Book) -> None:
        self.session.delete(book)
        self.session.flush()

    def _apply_query_filters(
        self,
        *,
        statement,
        count_statement,
        query_input: BookQueryInput,
    ):
        if query_input.status is not None:
            statement = statement.where(Book.reading_status == query_input.status)
            count_statement = count_statement.where(Book.reading_status == query_input.status)

        if query_input.category_slug is not None:
            statement = statement.where(Category.slug == query_input.category_slug)
            count_statement = count_statement.where(Category.slug == query_input.category_slug)

        if query_input.sub_category_slug is not None:
            statement = statement.where(SubCategory.slug == query_input.sub_category_slug)
            count_statement = count_statement.where(
                SubCategory.slug == query_input.sub_category_slug
            )

        if query_input.format is not None:
            statement = statement.where(Book.format == query_input.format)
            count_statement = count_statement.where(Book.format == query_input.format)

        if query_input.name_contains is not None:
            pattern = f"%{query_input.name_contains}%"
            statement = statement.where(Book.name.ilike(pattern))
            count_statement = count_statement.where(Book.name.ilike(pattern))

        if query_input.published_before is not None:
            statement = statement.where(Book.published_on <= query_input.published_before)
            count_statement = count_statement.where(
                Book.published_on <= query_input.published_before
            )

        if query_input.published_after is not None:
            statement = statement.where(Book.published_on >= query_input.published_after)
            count_statement = count_statement.where(
                Book.published_on >= query_input.published_after
            )

        return statement, count_statement

    def _build_sort_order(self, sort: BookSortOption):
        if sort == BookSortOption.CREATED_AT_ASC:
            return (Book.created_at.asc(),)
        if sort == BookSortOption.PUBLISHED_ON_DESC:
            return (Book.published_on.desc(), Book.created_at.desc())
        if sort == BookSortOption.PUBLISHED_ON_ASC:
            return (Book.published_on.asc(), Book.created_at.asc())
        if sort == BookSortOption.NAME_ASC:
            return (Book.name.asc(),)
        if sort == BookSortOption.NAME_DESC:
            return (Book.name.desc(),)
        return (Book.created_at.desc(),)


class TaxonomyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_categories(self) -> list[Category]:
        statement = (
            select(Category).options(joinedload(Category.subcategories)).order_by(Category.name)
        )
        return list(self.session.scalars(statement).unique())

    def get_category_by_slug(self, slug: str) -> Category | None:
        statement = select(Category).where(Category.slug == slug)
        return self.session.scalars(statement).one_or_none()

    def get_sub_category_by_slug_for_category(
        self,
        *,
        category_id: UUID,
        slug: str,
    ) -> SubCategory | None:
        statement = select(SubCategory).where(
            SubCategory.category_id == category_id,
            SubCategory.slug == slug,
        )
        return self.session.scalars(statement).one_or_none()

    def upsert_category(self, *, slug: str, name: str) -> Category:
        category = self.get_category_by_slug(slug)
        if category is None:
            category = Category(slug=slug, name=name)
            self.session.add(category)
            self.session.flush()
            return category

        category.name = name
        self.session.flush()
        return category

    def replace_subcategories(self, category: Category, items: list[tuple[str, str]]) -> None:
        existing_by_slug = {sub.slug: sub for sub in category.subcategories}
        incoming_slugs = {slug for slug, _ in items}

        for slug, name in items:
            existing = existing_by_slug.get(slug)
            if existing is None:
                category.subcategories.append(SubCategory(slug=slug, name=name))
            else:
                existing.name = name

        for sub_category in list(category.subcategories):
            if sub_category.slug not in incoming_slugs:
                category.subcategories.remove(sub_category)

        self.session.flush()
