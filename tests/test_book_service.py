from datetime import date

import pytest

from bookshelf.domain.enums import BookFormat, BookSortOption, ReadingStatus
from bookshelf.domain.schemas import BookCreateInput, BookQueryInput, BookUpdateInput
from bookshelf.services.books import BookService
from tests.support import FakeThumbnailStorage


def test_create_book_and_filter_by_status(seeded_session, tmp_path) -> None:
    cover_path = tmp_path / "cover.jpg"
    cover_path.write_bytes(b"cover-bytes")
    storage = FakeThumbnailStorage()
    service = BookService(seeded_session, thumbnail_storage=storage)

    created = service.create_book(
        BookCreateInput(
            name="The Argonauts",
            authors=["Maggie Nelson"],
            category_slug="essays",
            sub_category_slug="personal-essays",
            purchase_urls=["https://example.com/books/the-argonauts"],
            thumbnail_path=str(cover_path),
            published_on=date(2015, 5, 1),
            edition="First edition",
            format=BookFormat.HARDCOVER,
            page_length=160,
            reading_status=ReadingStatus.READING,
            note="A sharp and personal essay collection.",
        )
    )

    filtered = service.list_books(status=ReadingStatus.READING)
    unread = service.list_books(status=ReadingStatus.UNREAD)

    assert created.name == "The Argonauts"
    assert created.authors == ["Maggie Nelson"]
    assert created.thumbnail_object_key == "thumbnails/fake-path-object-1"
    assert created.purchase_urls == ["https://example.com/books/the-argonauts"]
    assert storage.uploads == [("path", str(cover_path))]
    assert [book.id for book in filtered] == [created.id]
    assert unread == []


def test_create_book_rejects_unknown_subcategory(seeded_session) -> None:
    service = BookService(seeded_session, thumbnail_storage=FakeThumbnailStorage())

    with pytest.raises(ValueError, match="unknown sub-category"):
        service.create_book(
            BookCreateInput(
                name="Misfiled Book",
                category_slug="essays",
                sub_category_slug="space-opera",
                purchase_urls=[],
            )
        )


def test_query_books_supports_filters_and_pagination(seeded_session) -> None:
    service = BookService(seeded_session, thumbnail_storage=FakeThumbnailStorage())

    service.create_book(
        BookCreateInput(
            name="Book A",
            category_slug="essays",
            reading_status=ReadingStatus.UNREAD,
        )
    )
    service.create_book(
        BookCreateInput(
            name="Book B",
            category_slug="narratives",
            sub_category_slug="historical-fiction",
            reading_status=ReadingStatus.READ,
            format=BookFormat.PAPERBACK,
        )
    )

    result = service.query_books(
        BookQueryInput(
            status=ReadingStatus.READ,
            category_slug="narratives",
            sort=BookSortOption.NAME_ASC,
            page=1,
            page_size=10,
        )
    )

    assert result.total_items == 1
    assert result.total_pages == 1
    assert [item.name for item in result.items] == ["Book B"]


def test_update_book_replaces_thumbnail_and_deletes_previous_object(
    seeded_session,
    tmp_path,
) -> None:
    initial_cover = tmp_path / "initial.jpg"
    replacement_cover = tmp_path / "replacement.jpg"
    initial_cover.write_bytes(b"initial")
    replacement_cover.write_bytes(b"replacement")

    storage = FakeThumbnailStorage()
    service = BookService(seeded_session, thumbnail_storage=storage)
    created = service.create_book(
        BookCreateInput(
            name="Replaceable Cover",
            category_slug="essays",
            thumbnail_path=str(initial_cover),
        )
    )

    updated = service.update_book(
        created.id,
        BookUpdateInput(
            name="Updated Cover",
            thumbnail_path=str(replacement_cover),
            clear_note=True,
        ),
    )

    assert updated.name == "Updated Cover"
    assert updated.thumbnail_object_key == "thumbnails/fake-path-object-2"
    assert storage.deletions == ["thumbnails/fake-path-object-1"]


def test_update_book_replaces_authors(seeded_session) -> None:
    service = BookService(seeded_session, thumbnail_storage=FakeThumbnailStorage())
    created = service.create_book(
        BookCreateInput(
            name="Collaboration",
            authors=["Author One"],
            category_slug="essays",
        )
    )

    updated = service.update_book(
        created.id,
        BookUpdateInput(
            authors=["Author One", "Author Two"],
        ),
    )

    assert updated.authors == ["Author One", "Author Two"]


def test_delete_book_removes_thumbnail_object(seeded_session, tmp_path) -> None:
    cover_path = tmp_path / "delete-cover.jpg"
    cover_path.write_bytes(b"cover")

    storage = FakeThumbnailStorage()
    service = BookService(seeded_session, thumbnail_storage=storage)
    created = service.create_book(
        BookCreateInput(
            name="Delete Me",
            category_slug="essays",
            thumbnail_path=str(cover_path),
        )
    )

    service.delete_book(created.id)

    with pytest.raises(LookupError):
        service.get_book(created.id)
    assert storage.deletions == ["thumbnails/fake-path-object-1"]
