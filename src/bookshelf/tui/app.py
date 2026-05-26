from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from collections.abc import Callable
from datetime import date
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from textual.app import App, ComposeResult, SuspendNotSupported
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    OptionList,
    Select,
    Static,
    TextArea,
)
from textual.widgets.option_list import Option

from bookshelf.db.session import SessionLocal
from bookshelf.domain.enums import BookFormat, ReadingStatus
from bookshelf.domain.schemas import (
    BookCreateInput,
    BookQueryInput,
    BookQueryResult,
    BookSchema,
    BookUpdateInput,
    TaxonomyCategorySchema,
)
from bookshelf.services.books import BookService
from bookshelf.services.dependencies import build_book_service, build_taxonomy_service
from bookshelf.services.taxonomy import TaxonomyService

PAGE_SIZE = 20


class ConfirmDeleteScreen(ModalScreen[bool]):
    CSS = """
    ConfirmDeleteScreen {
        align: center middle;
    }

    #confirm-delete {
        width: 60;
        max-width: 80;
        height: auto;
        border: round $error;
        background: $surface;
        padding: 1 2;
    }

    .confirm-actions {
        align-horizontal: right;
        padding-top: 1;
    }
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, book_name: str) -> None:
        super().__init__()
        self._book_name = book_name

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-delete"):
            yield Static("Delete book", id="confirm-title")
            yield Static(f"Delete '{self._book_name}'? This cannot be undone.")
            with Horizontal(classes="confirm-actions"):
                yield Button("Cancel", id="cancel-delete")
                yield Button("Delete", id="confirm-delete-button", variant="error")

    def action_cancel(self) -> None:
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-delete-button":
            self.dismiss(True)
        else:
            self.dismiss(False)


class BookFormScreen(ModalScreen[BookCreateInput | BookUpdateInput | None]):
    CSS = """
    BookFormScreen {
        align: center middle;
    }

    #book-form {
        width: 100;
        max-width: 120;
        height: 90%;
        border: round $accent;
        background: $surface;
        padding: 1;
    }

    .form-row {
        height: auto;
        padding-bottom: 1;
    }

    .form-column {
        width: 1fr;
        padding-right: 1;
    }

    .form-actions {
        height: auto;
        align-horizontal: right;
        padding-top: 1;
    }

    #form-error {
        color: $error;
        height: auto;
        padding-top: 1;
    }

    #note-field {
        height: 8;
    }
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(
        self,
        *,
        categories: list[TaxonomyCategorySchema],
        book: BookSchema | None,
    ) -> None:
        super().__init__()
        self._categories = categories
        self._category_map = {category.slug: category for category in categories}
        self._book = book

    def compose(self) -> ComposeResult:
        title = "Add book" if self._book is None else f"Edit book: {self._book.name}"
        reading_status_value = self._book.reading_status if self._book else ReadingStatus.UNREAD
        category_value = self._book.category.slug if self._book else self._categories[0].slug
        sub_category_value = (
            self._book.sub_category.slug if self._book and self._book.sub_category else Select.BLANK
        )
        format_value = self._book.format if self._book and self._book.format else Select.BLANK
        page_length_value = (
            str(self._book.page_length) if self._book and self._book.page_length else ""
        )
        published_on_value = (
            self._book.published_on.isoformat() if self._book and self._book.published_on else ""
        )
        note_value = self._book.note if self._book and self._book.note else ""
        edition_value = self._book.edition if self._book and self._book.edition else ""

        with Vertical(id="book-form"):
            yield Static(title, id="form-title")
            with VerticalScroll():
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-column"):
                        yield Static("Name")
                        yield Input(value=self._book.name if self._book else "", id="name-field")
                    with Vertical(classes="form-column"):
                        yield Static("Reading status")
                        yield Select(
                            self._build_status_options(),
                            allow_blank=False,
                            value=reading_status_value,
                            id="reading-status-field",
                        )
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-column"):
                        yield Static("Category")
                        yield Select(
                            self._build_category_options(),
                            allow_blank=False,
                            value=category_value,
                            id="category-field",
                        )
                    with Vertical(classes="form-column"):
                        yield Static("Sub-category")
                        yield Select(
                            self._build_sub_category_options(
                                category_value,
                                sub_category_value if isinstance(sub_category_value, str) else None,
                            ),
                            prompt="Optional",
                            allow_blank=False,
                            value=sub_category_value,
                            id="sub-category-field",
                        )
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-column"):
                        yield Static("Format")
                        yield Select(
                            self._build_format_options(),
                            prompt="Optional",
                            allow_blank=False,
                            value=format_value,
                            id="format-field",
                        )
                    with Vertical(classes="form-column"):
                        yield Static("Page length")
                        yield Input(
                            value=page_length_value,
                            placeholder="Optional integer",
                            id="page-length-field",
                        )
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-column"):
                        yield Static("Edition")
                        yield Input(
                            value=edition_value,
                            placeholder="Optional",
                            id="edition-field",
                        )
                    with Vertical(classes="form-column"):
                        yield Static("Published on")
                        yield Input(
                            value=published_on_value,
                            placeholder="YYYY-MM-DD",
                            id="published-on-field",
                        )
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-column"):
                        yield Static("Thumbnail file path")
                        yield Input(
                            placeholder="Optional local path. In Docker use /app/imports/...",
                            value="",
                            id="thumbnail-path-field",
                        )
                    with Vertical(classes="form-column"):
                        yield Static("Thumbnail URL")
                        yield Input(
                            placeholder="Optional remote URL",
                            value="",
                            id="thumbnail-url-field",
                        )
                if self._book is not None:
                    with Horizontal(classes="form-row"):
                        with Vertical(classes="form-column"):
                            yield Checkbox("Clear sub-category", id="clear-sub-category")
                            yield Checkbox("Clear format", id="clear-format")
                            yield Checkbox("Clear edition", id="clear-edition")
                            yield Checkbox("Clear published date", id="clear-published-on")
                        with Vertical(classes="form-column"):
                            yield Checkbox("Clear page length", id="clear-page-length")
                            yield Checkbox("Clear note", id="clear-note")
                            yield Checkbox("Clear thumbnail", id="clear-thumbnail")
                yield Static("Note")
                yield TextArea(
                    text=note_value,
                    id="note-field",
                    language=None,
                )
                with Horizontal(classes="form-actions"):
                    yield Button("Open in $EDITOR", id="edit-note-external")
            yield Static("", id="form-error")
            with Horizontal(classes="form-actions"):
                yield Button("Cancel", id="cancel-form")
                yield Button("Save", id="save-form", variant="primary")

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "category-field":
            self._update_sub_category_options(event.value)

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        checkbox_id = event.checkbox.id
        if checkbox_id == "clear-sub-category" and event.value:
            self.query_one("#sub-category-field", Select).value = Select.BLANK
        elif checkbox_id == "clear-format" and event.value:
            self.query_one("#format-field", Select).value = Select.BLANK
        elif checkbox_id == "clear-edition" and event.value:
            self.query_one("#edition-field", Input).value = ""
        elif checkbox_id == "clear-published-on" and event.value:
            self.query_one("#published-on-field", Input).value = ""
        elif checkbox_id == "clear-page-length" and event.value:
            self.query_one("#page-length-field", Input).value = ""
        elif checkbox_id == "clear-note" and event.value:
            self.query_one("#note-field", TextArea).clear()
        elif checkbox_id == "clear-thumbnail" and event.value:
            self.query_one("#thumbnail-path-field", Input).value = ""
            self.query_one("#thumbnail-url-field", Input).value = ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-form":
            self._submit()
        elif event.button.id == "edit-note-external":
            self._edit_note_externally()
        else:
            self.dismiss(None)

    def _submit(self) -> None:
        try:
            result = self._build_payload()
        except (ValidationError, ValueError) as exc:
            self.query_one("#form-error", Static).update(str(exc))
            return

        self.dismiss(result)

    def _build_payload(self) -> BookCreateInput | BookUpdateInput:
        name = self.query_one("#name-field", Input).value
        category = self._select_value("#category-field")
        sub_category = self._select_value("#sub-category-field")
        reading_status = self._select_value("#reading-status-field")
        format_value = self._select_value("#format-field")
        page_length = self._parse_optional_int(self.query_one("#page-length-field", Input).value)
        published_on = self._parse_optional_date(self.query_one("#published-on-field", Input).value)
        edition = self._normalize_optional_text(self.query_one("#edition-field", Input).value)
        note = self._normalize_optional_text(self.query_one("#note-field", TextArea).text)
        thumbnail_path = self._normalize_optional_text(
            self.query_one("#thumbnail-path-field", Input).value
        )
        thumbnail_url = self._normalize_optional_text(
            self.query_one("#thumbnail-url-field", Input).value
        )

        if self._book is None:
            return BookCreateInput(
                name=name,
                category_slug=self._require_str(category, "category"),
                sub_category_slug=sub_category if isinstance(sub_category, str) else None,
                format=format_value if isinstance(format_value, BookFormat) else None,
                page_length=page_length,
                published_on=published_on,
                edition=edition,
                reading_status=(
                    reading_status
                    if isinstance(reading_status, ReadingStatus)
                    else ReadingStatus.UNREAD
                ),
                note=note,
                thumbnail_path=thumbnail_path,
                thumbnail_url=thumbnail_url,
            )

        return BookUpdateInput(
            name=name,
            category_slug=self._require_str(category, "category"),
            sub_category_slug=(sub_category if isinstance(sub_category, str) else None),
            clear_sub_category=self._is_checked("#clear-sub-category"),
            format=format_value if isinstance(format_value, BookFormat) else None,
            clear_format=self._is_checked("#clear-format"),
            page_length=page_length,
            clear_page_length=self._is_checked("#clear-page-length"),
            published_on=published_on,
            clear_published_on=self._is_checked("#clear-published-on"),
            edition=edition,
            clear_edition=self._is_checked("#clear-edition"),
            reading_status=(reading_status if isinstance(reading_status, ReadingStatus) else None),
            note=note,
            clear_note=self._is_checked("#clear-note"),
            thumbnail_path=thumbnail_path,
            thumbnail_url=thumbnail_url,
            clear_thumbnail=self._is_checked("#clear-thumbnail"),
        )

    def _update_sub_category_options(self, category_value: object) -> None:
        category_slug = category_value if isinstance(category_value, str) else None
        sub_category_field = self.query_one("#sub-category-field", Select)
        sub_category_field.set_options(self._build_sub_category_options(category_slug, None))
        sub_category_field.value = Select.BLANK

    def _edit_note_externally(self) -> None:
        editor = os.environ.get("EDITOR")
        if not editor:
            self.query_one("#form-error", Static).update(
                "$EDITOR is not configured. Continue editing the note inline."
            )
            return

        try:
            command = shlex.split(editor)
        except ValueError as exc:
            self.query_one("#form-error", Static).update(f"Invalid $EDITOR value: {exc}")
            return

        if not command:
            self.query_one("#form-error", Static).update(
                "$EDITOR is configured but empty. Continue editing the note inline."
            )
            return

        note_field = self.query_one("#note-field", TextArea)

        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".md", delete=False
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(note_field.text)

        try:
            try:
                with self.app.suspend():
                    completed = subprocess.run([*command, str(temp_path)], check=False)
            except SuspendNotSupported:
                self.query_one("#form-error", Static).update(
                    "External editor handoff is not supported in this environment."
                )
                return
            except OSError as exc:
                self.query_one("#form-error", Static).update(
                    f"Unable to launch external editor: {exc}"
                )
                return

            if completed.returncode != 0:
                self.query_one("#form-error", Static).update(
                    f"External editor exited with status {completed.returncode}."
                )
                return

            note_field.load_text(temp_path.read_text(encoding="utf-8"))
            self.query_one("#form-error", Static).update("")
        finally:
            temp_path.unlink(missing_ok=True)

    def _build_status_options(self) -> list[tuple[str, object]]:
        return [(status.value.replace("_", " ").title(), status) for status in ReadingStatus]

    def _build_category_options(self) -> list[tuple[str, object]]:
        return [(category.name, category.slug) for category in self._categories]

    def _build_sub_category_options(
        self,
        category_slug: str | None,
        selected_slug: str | None,
    ) -> list[tuple[str, object]]:
        options: list[tuple[str, object]] = [("No sub-category", Select.BLANK)]
        if category_slug is None:
            return options

        category = self._category_map.get(category_slug)
        if category is None:
            return options

        options.extend((sub.name, sub.slug) for sub in category.subcategories)
        return options

    def _build_format_options(self) -> list[tuple[str, object]]:
        return [("No format", Select.BLANK)] + [
            (book_format.value.replace("_", " ").title(), book_format) for book_format in BookFormat
        ]

    def _select_value(self, selector: str) -> object:
        return self.query_one(selector, Select).value

    def _is_checked(self, selector: str) -> bool:
        checkbox = self.query_one(selector, Checkbox)
        return checkbox.value

    def _normalize_optional_text(self, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    def _parse_optional_int(self, value: str) -> int | None:
        stripped = value.strip()
        if not stripped:
            return None
        return int(stripped)

    def _parse_optional_date(self, value: str) -> date | None:
        stripped = value.strip()
        if not stripped:
            return None
        return date.fromisoformat(stripped)

    def _require_str(self, value: object, label: str) -> str:
        if isinstance(value, str) and value:
            return value
        raise ValueError(f"{label} is required")


class BookshelfTuiApp(App[None]):
    TITLE = "Bookshelf"
    SUB_TITLE = "Library"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("n", "next_page", "Next page"),
        Binding("p", "previous_page", "Previous page"),
        Binding("a", "create_book", "Add book"),
        Binding("e", "edit_book", "Edit book"),
        Binding("d", "delete_book", "Delete book"),
    ]
    CSS = """
    Screen {
        layout: vertical;
    }

    #filters {
        height: auto;
        max-height: 8;
        padding: 1;
    }

    #filter-inputs {
        height: auto;
    }

    .filter-column {
        width: 1fr;
        height: auto;
        min-width: 20;
        padding-right: 1;
    }

    #content {
        height: 1fr;
    }

    #book-list {
        width: 1fr;
        height: 1fr;
        border: round $accent;
    }

    #detail-pane {
        width: 1fr;
        height: 1fr;
        border: round $primary;
        padding: 1;
    }

    #status-line {
        height: auto;
        padding: 0 1;
    }

    #detail-title {
        text-style: bold;
        padding-bottom: 1;
    }

    #detail-body {
        height: 1fr;
    }

    .filter-actions {
        align-horizontal: right;
        padding-top: 1;
    }
    """

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session] = SessionLocal,
        book_service_factory: Callable[[Session], BookService] | None = None,
        taxonomy_service_factory: Callable[[Session], TaxonomyService] | None = None,
    ) -> None:
        super().__init__()
        self._session_factory = session_factory
        self._book_service_factory = book_service_factory or build_book_service
        self._taxonomy_service_factory = taxonomy_service_factory or build_taxonomy_service
        self._categories: list[TaxonomyCategorySchema] = []
        self._query_result = BookQueryResult(
            items=[],
            page=1,
            page_size=PAGE_SIZE,
            total_items=0,
            total_pages=0,
        )
        self._selected_book_id: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="filters"):
            with Horizontal(id="filter-inputs"):
                with Vertical(classes="filter-column"):
                    yield Static("Reading status")
                    yield Select(
                        self._build_status_options(),
                        prompt="Any status",
                        allow_blank=False,
                        value=Select.BLANK,
                        id="status-filter",
                    )
                with Vertical(classes="filter-column"):
                    yield Static("Category")
                    yield Select(
                        [("Any category", Select.BLANK)],
                        prompt="Any category",
                        allow_blank=False,
                        value=Select.BLANK,
                        id="category-filter",
                    )
                with Vertical(classes="filter-column"):
                    yield Static("Format")
                    yield Select(
                        self._build_format_options(),
                        prompt="Any format",
                        allow_blank=False,
                        value=Select.BLANK,
                        id="format-filter",
                    )
                with Vertical(classes="filter-column"):
                    yield Static("Name contains")
                    yield Input(placeholder="Search title", id="name-filter")
            with Horizontal(classes="filter-actions"):
                yield Button("Apply filters", id="apply-filters", variant="primary")
                yield Button("Clear filters", id="clear-filters")
                yield Button("Add", id="create-book", variant="success")
                yield Button("Edit", id="edit-book")
                yield Button("Delete", id="delete-book", variant="error")
                yield Button("Previous page", id="previous-page")
                yield Button("Next page", id="next-page")

        with Horizontal(id="content"):
            yield OptionList(id="book-list")
            with Vertical(id="detail-pane"):
                yield Static("No book selected", id="detail-title")
                yield Static("Select a book to see its details.", id="detail-body")

        yield Static("Loading library...", id="status-line")
        yield Footer()

    def on_mount(self) -> None:
        self._load_categories()
        self._refresh_books()

    def action_refresh(self) -> None:
        self._refresh_books(page=1)

    def action_next_page(self) -> None:
        if (
            self._query_result.total_pages
            and self._query_result.page < self._query_result.total_pages
        ):
            self._refresh_books(page=self._query_result.page + 1)

    def action_previous_page(self) -> None:
        if self._query_result.page > 1:
            self._refresh_books(page=self._query_result.page - 1)

    def action_create_book(self) -> None:
        self._open_book_form(book=None)

    def action_edit_book(self) -> None:
        selected_book = self._get_selected_book()
        if selected_book is None:
            self._set_status("Select a book before editing.")
            return
        self._open_book_form(book=selected_book)

    def action_delete_book(self) -> None:
        selected_book = self._get_selected_book()
        if selected_book is None:
            self._set_status("Select a book before deleting.")
            return

        self.push_screen(
            ConfirmDeleteScreen(selected_book.name),
            callback=lambda confirmed: self._delete_book(selected_book.id, confirmed),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "apply-filters":
            self._refresh_books(page=1)
        elif button_id == "clear-filters":
            self._reset_filters()
            self._refresh_books(page=1)
        elif button_id == "next-page":
            self.action_next_page()
        elif button_id == "previous-page":
            self.action_previous_page()
        elif button_id == "create-book":
            self.action_create_book()
        elif button_id == "edit-book":
            self.action_edit_book()
        elif button_id == "delete-book":
            self.action_delete_book()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "name-filter":
            self._refresh_books(page=1)

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option_list.id != "book-list":
            return

        option_id = event.option.id
        if option_id is None:
            self._selected_book_id = None
            self._render_selected_book()
            return

        self._selected_book_id = option_id
        self._render_selected_book()

    def _open_book_form(self, *, book: BookSchema | None) -> None:
        self.push_screen(
            BookFormScreen(categories=self._categories, book=book),
            callback=lambda payload: self._save_book(
                payload,
                existing_book_id=book.id if book else None,
            ),
        )

    def _save_book(
        self,
        payload: BookCreateInput | BookUpdateInput | None,
        *,
        existing_book_id: UUID | None,
    ) -> None:
        if payload is None:
            return

        try:
            with self._session_factory() as session:
                book_service = self._book_service_factory(session)
                if existing_book_id is None:
                    saved_book = book_service.create_book(payload)
                    message = f"Created book: {saved_book.name}"
                else:
                    saved_book = book_service.update_book(existing_book_id, payload)
                    message = f"Updated book: {saved_book.name}"
        except (LookupError, SQLAlchemyError, ValidationError, ValueError) as exc:
            self._set_status(f"Unable to save book: {exc}")
            return

        self._selected_book_id = saved_book.id.hex
        self._load_categories()
        self._refresh_books(reset_selection=False)
        self._set_status(message)

    def _delete_book(self, book_id: UUID, confirmed: bool) -> None:
        if not confirmed:
            self._set_status("Deletion cancelled.")
            return

        try:
            with self._session_factory() as session:
                self._book_service_factory(session).delete_book(book_id)
        except (LookupError, SQLAlchemyError, ValueError) as exc:
            self._set_status(f"Unable to delete book: {exc}")
            return

        self._selected_book_id = None
        self._refresh_books(page=1)
        self._set_status(f"Deleted book: {book_id}")

    def _load_categories(self) -> None:
        try:
            with self._session_factory() as session:
                self._categories = self._taxonomy_service_factory(session).list_categories()
        except SQLAlchemyError as exc:
            self._categories = []
            self._set_status(f"Unable to load categories: {exc}")
            return

        category_filter = self.query_one("#category-filter", Select)
        current_category = category_filter.value
        category_filter.set_options(self._build_category_options())
        if isinstance(current_category, str) and any(
            category.slug == current_category for category in self._categories
        ):
            category_filter.value = current_category
        else:
            category_filter.value = Select.BLANK

    def _refresh_books(self, *, page: int | None = None, reset_selection: bool = True) -> None:
        query_input = self._build_query_input(page=page)
        try:
            with self._session_factory() as session:
                result = self._book_service_factory(session).query_books(query_input)
        except (SQLAlchemyError, ValueError) as exc:
            self._query_result = BookQueryResult(
                items=[],
                page=query_input.page,
                page_size=query_input.page_size,
                total_items=0,
                total_pages=0,
            )
            self._render_books(error=f"Unable to load books: {exc}")
            return

        self._query_result = result
        if reset_selection:
            self._selected_book_id = result.items[0].id.hex if result.items else None
        elif self._selected_book_id not in {book.id.hex for book in result.items}:
            self._selected_book_id = result.items[0].id.hex if result.items else None

        self._render_books()

    def _build_query_input(self, *, page: int | None = None) -> BookQueryInput:
        status_filter = self.query_one("#status-filter", Select)
        category_filter = self.query_one("#category-filter", Select)
        format_filter = self.query_one("#format-filter", Select)
        name_filter = self.query_one("#name-filter", Input)

        status = status_filter.value
        category = category_filter.value
        format_value = format_filter.value

        return BookQueryInput(
            status=status if isinstance(status, ReadingStatus) else None,
            category_slug=category if isinstance(category, str) and category else None,
            format=format_value if isinstance(format_value, BookFormat) else None,
            name_contains=name_filter.value,
            page=page or self._query_result.page or 1,
            page_size=PAGE_SIZE,
        )

    def _render_books(self, *, error: str | None = None) -> None:
        book_list = self.query_one("#book-list", OptionList)
        book_list.clear_options()

        for book in self._query_result.items:
            book_list.add_option(Option(self._format_book_summary(book), id=book.id.hex))

        if self._query_result.items:
            selected_id = self._selected_book_id or self._query_result.items[0].id.hex
            selected_index = next(
                (
                    index
                    for index, book in enumerate(self._query_result.items)
                    if book.id.hex == selected_id
                ),
                0,
            )
            book_list.highlighted = selected_index
            self._selected_book_id = self._query_result.items[selected_index].id.hex
        else:
            self._selected_book_id = None

        self._render_selected_book()
        self._set_status(error or self._build_status_text())
        self._update_paging_buttons()

    def _render_selected_book(self) -> None:
        title = self.query_one("#detail-title", Static)
        body = self.query_one("#detail-body", Static)

        book = self._get_selected_book()
        if book is None:
            title.update("No book selected")
            body.update("Select a book to see its details.")
            return

        title.update(book.name)
        body.update(self._format_book_detail(book))

    def _update_paging_buttons(self) -> None:
        previous_button = self.query_one("#previous-page", Button)
        next_button = self.query_one("#next-page", Button)
        edit_button = self.query_one("#edit-book", Button)
        delete_button = self.query_one("#delete-book", Button)

        has_selection = self._get_selected_book() is not None

        previous_button.disabled = self._query_result.page <= 1
        next_button.disabled = self._query_result.total_pages == 0 or (
            self._query_result.page >= self._query_result.total_pages
        )
        edit_button.disabled = not has_selection
        delete_button.disabled = not has_selection

    def _reset_filters(self) -> None:
        self.query_one("#status-filter", Select).value = Select.BLANK
        self.query_one("#category-filter", Select).value = Select.BLANK
        self.query_one("#format-filter", Select).value = Select.BLANK
        self.query_one("#name-filter", Input).value = ""

    def _set_status(self, message: str) -> None:
        self.query_one("#status-line", Static).update(message)

    def _build_status_text(self) -> str:
        if self._query_result.total_items == 0:
            return "No books found. Adjust filters or add a book."

        return (
            f"Page {self._query_result.page}/{self._query_result.total_pages} | "
            f"showing {len(self._query_result.items)} of {self._query_result.total_items} books"
        )

    def _build_status_options(self) -> list[tuple[str, object]]:
        return [("Any status", Select.BLANK)] + [
            (status.value.replace("_", " ").title(), status) for status in ReadingStatus
        ]

    def _build_category_options(self) -> list[tuple[str, object]]:
        return [("Any category", Select.BLANK)] + [
            (category.name, category.slug) for category in self._categories
        ]

    def _build_format_options(self) -> list[tuple[str, object]]:
        return [("Any format", Select.BLANK)] + [
            (book_format.value.replace("_", " ").title(), book_format) for book_format in BookFormat
        ]

    def _get_selected_book(self) -> BookSchema | None:
        return next(
            (item for item in self._query_result.items if item.id.hex == self._selected_book_id),
            None,
        )

    def _format_book_summary(self, book: BookSchema) -> str:
        return f"{book.name} | {self._format_category_label(book)} | {book.reading_status.value}"

    def _format_book_detail(self, book: BookSchema) -> str:
        details = [
            f"ID: {book.id}",
            f"Category: {self._format_category_label(book)}",
            f"Status: {book.reading_status.value}",
            f"Format: {book.format.value if book.format else '-'}",
            f"Published: {book.published_on.isoformat() if book.published_on else '-'}",
            f"Edition: {book.edition or '-'}",
            f"Pages: {book.page_length if book.page_length is not None else '-'}",
            f"Purchase URLs: {len(book.purchase_urls)}",
            f"Thumbnail: {'yes' if book.thumbnail_object_key else 'no'}",
            "",
            "Note:",
            book.note or "-",
        ]
        return "\n".join(details)

    def _format_category_label(self, book: BookSchema) -> str:
        label = book.category.name
        if book.sub_category is not None:
            label = f"{label} / {book.sub_category.name}"
        return label


def run_tui(*, session_factory: sessionmaker[Session] = SessionLocal) -> None:
    BookshelfTuiApp(
        session_factory=session_factory,
        book_service_factory=build_book_service,
        taxonomy_service_factory=build_taxonomy_service,
    ).run()
