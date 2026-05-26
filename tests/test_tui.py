import asyncio
import subprocess
from contextlib import contextmanager
from pathlib import Path

from textual.app import SuspendNotSupported
from textual.widgets import Button, Input, OptionList, Select, Static, TextArea

from bookshelf.domain.enums import ReadingStatus
from bookshelf.domain.schemas import BookCreateInput
from bookshelf.services.books import BookService
from bookshelf.services.taxonomy import TaxonomyService
from bookshelf.tui.app import BookshelfTuiApp
from tests.support import TAXONOMY_PATH, FakeThumbnailStorage


def test_tui_app_shows_empty_state(session_factory) -> None:
    async def run_test() -> None:
        app = BookshelfTuiApp(session_factory=session_factory)

        async with app.run_test() as pilot:
            await pilot.pause()
            detail_title = app.query_one("#detail-title", Static)
            status_line = app.query_one("#status-line", Static)

        assert "No book selected" in str(detail_title.content)
        assert "No books found." in str(status_line.content)

    asyncio.run(run_test())


def test_tui_app_lists_books_and_details(session_factory) -> None:
    with session_factory() as session:
        TaxonomyService(session).seed_from_file(TAXONOMY_PATH)
        BookService(session).create_book(
            BookCreateInput(
                name="The Left Hand of Darkness",
                category_slug="science-fiction",
                sub_category_slug="space-opera",
                reading_status=ReadingStatus.READING,
                note="A cold and precise world-building study.",
            )
        )

    async def run_test() -> None:
        app = BookshelfTuiApp(session_factory=session_factory)

        async with app.run_test() as pilot:
            await pilot.pause()
            book_list = app.query_one("#book-list", OptionList)
            detail_title = app.query_one("#detail-title", Static)
            detail_body = app.query_one("#detail-body", Static)
            status_line = app.query_one("#status-line", Static)

        assert book_list.option_count == 1
        assert "The Left Hand of Darkness" in str(detail_title.content)
        assert "Science Fiction / Space Opera" in str(detail_body.content)
        assert "A cold and precise world-building study." in str(detail_body.content)
        assert "showing 1 of 1 books" in str(status_line.content)

    asyncio.run(run_test())


def test_tui_app_applies_filters(session_factory) -> None:
    with session_factory() as session:
        TaxonomyService(session).seed_from_file(TAXONOMY_PATH)
        service = BookService(session)
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
            )
        )

    async def run_test() -> None:
        app = BookshelfTuiApp(session_factory=session_factory)

        async with app.run_test() as pilot:
            await pilot.pause()

            status_filter = app.query_one("#status-filter", Select)
            name_filter = app.query_one("#name-filter", Input)
            apply_button = app.query_one("#apply-filters", Button)

            status_filter.value = ReadingStatus.READ
            name_filter.value = "Book B"
            apply_button.press()
            await pilot.pause()

            book_list = app.query_one("#book-list", OptionList)
            detail_title = app.query_one("#detail-title", Static)
            status_line = app.query_one("#status-line", Static)

        assert book_list.option_count == 1
        assert "Book B" in str(detail_title.content)
        assert "showing 1 of 1 books" in str(status_line.content)

    asyncio.run(run_test())


def test_tui_app_updates_paging_buttons(session_factory) -> None:
    with session_factory() as session:
        TaxonomyService(session).seed_from_file(TAXONOMY_PATH)
        service = BookService(session)
        for index in range(25):
            service.create_book(
                BookCreateInput(
                    name=f"Book {index:02d}",
                    category_slug="essays",
                    reading_status=ReadingStatus.UNREAD,
                )
            )

    async def run_test() -> None:
        app = BookshelfTuiApp(session_factory=session_factory)

        async with app.run_test() as pilot:
            await pilot.pause()

            previous_button = app.query_one("#previous-page", Button)
            next_button = app.query_one("#next-page", Button)
            status_line = app.query_one("#status-line", Static)

            assert previous_button.disabled is True
            assert next_button.disabled is False
            assert "Page 1/2" in str(status_line.content)

            next_button.press()
            await pilot.pause()

            assert previous_button.disabled is False
            assert next_button.disabled is True
            assert "Page 2/2" in str(status_line.content)

    asyncio.run(run_test())


def test_tui_layout_keeps_content_visible_at_normal_terminal_size(session_factory) -> None:
    with session_factory() as session:
        TaxonomyService(session).seed_from_file(TAXONOMY_PATH)
        BookService(session).create_book(
            BookCreateInput(
                name="Visible Book",
                category_slug="essays",
                reading_status=ReadingStatus.UNREAD,
            )
        )

    async def run_test() -> None:
        app = BookshelfTuiApp(session_factory=session_factory)

        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()

            content = app.query_one("#content")
            book_list = app.query_one("#book-list", OptionList)
            detail_title = app.query_one("#detail-title", Static)
            content_height = content.size.height
            book_list_height = book_list.region.height
            detail_text = str(detail_title.content)

        assert content_height >= 10
        assert book_list_height >= 10
        assert "Visible Book" in detail_text

    asyncio.run(run_test())


def test_tui_refresh_shows_book_created_outside_tui(session_factory) -> None:
    with session_factory() as session:
        TaxonomyService(session).seed_from_file(TAXONOMY_PATH)
        BookService(session).create_book(
            BookCreateInput(
                name="Earlier Book",
                category_slug="essays",
                reading_status=ReadingStatus.UNREAD,
            )
        )

    async def run_test() -> None:
        app = BookshelfTuiApp(session_factory=session_factory)

        async with app.run_test() as pilot:
            await pilot.pause()

            with session_factory() as session:
                BookService(session).create_book(
                    BookCreateInput(
                        name="Externally Added Book",
                        category_slug="science-fiction",
                        sub_category_slug="space-opera",
                        reading_status=ReadingStatus.READ,
                    )
                )

            await pilot.press("r")
            await pilot.pause()

            detail_title = app.query_one("#detail-title", Static)
            book_list = app.query_one("#book-list", OptionList)
            status_line = app.query_one("#status-line", Static)
            book_names = [
                str(book_list.get_option_at_index(index).prompt)
                for index in range(book_list.option_count)
            ]

        assert book_list.option_count == 2
        assert "Earlier Book" in str(detail_title.content) or "Externally Added Book" in str(
            detail_title.content
        )
        assert any("Externally Added Book" in name for name in book_names)
        assert "Page 1/1" in str(status_line.content)

    asyncio.run(run_test())


def test_tui_app_creates_book(session_factory) -> None:
    with session_factory() as session:
        TaxonomyService(session).seed_from_file(TAXONOMY_PATH)

    async def run_test() -> None:
        app = BookshelfTuiApp(session_factory=session_factory)

        async with app.run_test() as pilot:
            await pilot.pause()

            app.query_one("#create-book", Button).press()
            await pilot.pause()

            form = app.screen

            form.query_one("#name-field", Input).value = "The Dispossessed"
            form.query_one("#category-field", Select).value = "science-fiction"
            await pilot.pause()
            form.query_one("#sub-category-field", Select).value = "space-opera"
            form.query_one("#reading-status-field", Select).value = ReadingStatus.READ
            form.query_one("#note-field", TextArea).load_text("An austere political classic.")

            form.query_one("#save-form", Button).press()
            await pilot.pause()

            detail_title = app.query_one("#detail-title", Static)
            detail_body = app.query_one("#detail-body", Static)
            status_line = app.query_one("#status-line", Static)
            book_list = app.query_one("#book-list", OptionList)

        assert book_list.option_count == 1
        assert "The Dispossessed" in str(detail_title.content)
        assert "An austere political classic." in str(detail_body.content)
        assert "Created book: The Dispossessed" in str(status_line.content)

    asyncio.run(run_test())


def test_tui_note_external_editor_requires_editor_env(session_factory, monkeypatch) -> None:
    with session_factory() as session:
        TaxonomyService(session).seed_from_file(TAXONOMY_PATH)

    monkeypatch.delenv("EDITOR", raising=False)

    async def run_test() -> None:
        app = BookshelfTuiApp(session_factory=session_factory)

        async with app.run_test() as pilot:
            await pilot.pause()

            app.query_one("#create-book", Button).press()
            await pilot.pause()

            form = app.screen
            form.query_one("#edit-note-external", Button).press()
            await pilot.pause()

            error = form.query_one("#form-error", Static)

        assert "$EDITOR is not configured" in str(error.content)

    asyncio.run(run_test())


def test_tui_note_external_editor_updates_note(session_factory, monkeypatch) -> None:
    with session_factory() as session:
        TaxonomyService(session).seed_from_file(TAXONOMY_PATH)

    monkeypatch.setenv("EDITOR", "fake-editor --wait")

    def fake_run(command: list[str], check: bool) -> subprocess.CompletedProcess[str]:
        note_path = Path(command[-1])
        note_path.write_text("Edited in external editor.\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("bookshelf.tui.app.subprocess.run", fake_run)

    @contextmanager
    def fake_suspend():
        yield

    async def run_test() -> None:
        app = BookshelfTuiApp(session_factory=session_factory)

        async with app.run_test() as pilot:
            await pilot.pause()

            app.query_one("#create-book", Button).press()
            await pilot.pause()

            form = app.screen
            monkeypatch.setattr(form.app, "suspend", fake_suspend)
            form.query_one("#edit-note-external", Button).press()
            await pilot.pause()

            note_field = form.query_one("#note-field", TextArea)
            error = form.query_one("#form-error", Static)

        assert note_field.text == "Edited in external editor.\n"
        assert str(error.content) == ""

    asyncio.run(run_test())


def test_tui_note_external_editor_handles_suspend_not_supported(
    session_factory,
    monkeypatch,
) -> None:
    with session_factory() as session:
        TaxonomyService(session).seed_from_file(TAXONOMY_PATH)

    monkeypatch.setenv("EDITOR", "fake-editor")

    @contextmanager
    def fake_suspend():
        raise SuspendNotSupported("not supported")
        yield

    async def run_test() -> None:
        app = BookshelfTuiApp(session_factory=session_factory)

        async with app.run_test() as pilot:
            await pilot.pause()

            app.query_one("#create-book", Button).press()
            await pilot.pause()

            form = app.screen
            monkeypatch.setattr(form.app, "suspend", fake_suspend)
            form.query_one("#edit-note-external", Button).press()
            await pilot.pause()

            error = form.query_one("#form-error", Static)

        assert str(error.content) == "External editor handoff is not supported in this environment."

    asyncio.run(run_test())


def test_tui_app_creates_book_with_thumbnail_path(session_factory, tmp_path) -> None:
    with session_factory() as session:
        TaxonomyService(session).seed_from_file(TAXONOMY_PATH)

    cover_path = tmp_path / "cover.jpg"
    cover_path.write_bytes(b"cover-bytes")
    storage = FakeThumbnailStorage()

    def book_service_factory(session):
        return BookService(session, thumbnail_storage=storage)

    async def run_test() -> None:
        app = BookshelfTuiApp(
            session_factory=session_factory,
            book_service_factory=book_service_factory,
        )

        async with app.run_test() as pilot:
            await pilot.pause()

            app.query_one("#create-book", Button).press()
            await pilot.pause()

            form = app.screen
            form.query_one("#name-field", Input).value = "Cover Book"
            form.query_one("#category-field", Select).value = "essays"
            form.query_one("#thumbnail-path-field", Input).value = str(cover_path)

            form.query_one("#save-form", Button).press()
            await pilot.pause()

            detail_body = app.query_one("#detail-body", Static)
            status_line = app.query_one("#status-line", Static)

        assert storage.uploads == [("path", str(cover_path))]
        assert "Thumbnail: yes" in str(detail_body.content)
        assert "Created book: Cover Book" in str(status_line.content)

    asyncio.run(run_test())


def test_tui_app_updates_book(session_factory) -> None:
    with session_factory() as session:
        TaxonomyService(session).seed_from_file(TAXONOMY_PATH)
        BookService(session).create_book(
            BookCreateInput(
                name="Original Title",
                category_slug="essays",
                reading_status=ReadingStatus.UNREAD,
                note="Old note.",
            )
        )

    async def run_test() -> None:
        app = BookshelfTuiApp(session_factory=session_factory)

        async with app.run_test() as pilot:
            await pilot.pause()

            app.query_one("#edit-book", Button).press()
            await pilot.pause()

            form = app.screen

            form.query_one("#name-field", Input).value = "Updated Title"
            form.query_one("#reading-status-field", Select).value = ReadingStatus.READING
            form.query_one("#note-field", TextArea).load_text("Updated note.")

            form.query_one("#save-form", Button).press()
            await pilot.pause()

            detail_title = app.query_one("#detail-title", Static)
            detail_body = app.query_one("#detail-body", Static)
            status_line = app.query_one("#status-line", Static)

        assert "Updated Title" in str(detail_title.content)
        assert "Status: reading" in str(detail_body.content)
        assert "Updated note." in str(detail_body.content)
        assert "Updated book: Updated Title" in str(status_line.content)

    asyncio.run(run_test())


def test_tui_app_deletes_book(session_factory) -> None:
    with session_factory() as session:
        TaxonomyService(session).seed_from_file(TAXONOMY_PATH)
        BookService(session).create_book(
            BookCreateInput(
                name="Delete Me",
                category_slug="essays",
                reading_status=ReadingStatus.UNREAD,
            )
        )

    async def run_test() -> None:
        app = BookshelfTuiApp(session_factory=session_factory)

        async with app.run_test() as pilot:
            await pilot.pause()

            app.query_one("#delete-book", Button).press()
            await pilot.pause()

            confirm = app.screen
            confirm.query_one("#confirm-delete-button", Button).press()
            await pilot.pause()

            detail_title = app.query_one("#detail-title", Static)
            status_line = app.query_one("#status-line", Static)
            book_list = app.query_one("#book-list", OptionList)

        assert book_list.option_count == 0
        assert "No book selected" in str(detail_title.content)
        assert "Deleted book:" in str(status_line.content)

    asyncio.run(run_test())
