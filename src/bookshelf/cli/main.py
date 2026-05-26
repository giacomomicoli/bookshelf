from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Annotated
from uuid import UUID

import typer
from pydantic import ValidationError

from bookshelf.db.session import SessionLocal
from bookshelf.domain.enums import BookFormat, BookSortOption, ReadingStatus
from bookshelf.domain.schemas import (
    BookCreateInput,
    BookQueryInput,
    BookQueryResult,
    BookSchema,
    BookUpdateInput,
)
from bookshelf.services.dependencies import build_book_service, build_taxonomy_service

app = typer.Typer(help="CLI-first bookshelf utility.")

SeedTaxonomyPath = Annotated[
    Path,
    typer.Option(
        exists=True,
        dir_okay=False,
        file_okay=True,
        help="Path to the taxonomy seed YAML file.",
    ),
]
StatusFilterOption = Annotated[
    ReadingStatus | None,
    typer.Option(help="Optional reading status filter."),
]
NameOption = Annotated[str | None, typer.Option(help="Book name.")]
CategoryOption = Annotated[str | None, typer.Option(help="Category slug.")]
SubCategoryOption = Annotated[str | None, typer.Option(help="Sub-category slug.")]
PublishedOnOption = Annotated[
    str | None,
    typer.Option(help="Publishing date in YYYY-MM-DD format."),
]
EditionOption = Annotated[str | None, typer.Option(help="Edition label.")]
FormatOption = Annotated[BookFormat | None, typer.Option(help="Book format.")]
PageLengthOption = Annotated[int | None, typer.Option(help="Total page length.")]
ReadingStatusOption = Annotated[
    ReadingStatus | None,
    typer.Option(help="Reading status."),
]
ThumbnailPathOption = Annotated[
    str | None,
    typer.Option(help="Local file path for the thumbnail."),
]
ThumbnailUrlOption = Annotated[
    str | None,
    typer.Option(help="Remote URL to import as thumbnail."),
]
NoteFileOption = Annotated[
    Path | None,
    typer.Option(help="Optional text file to load into the note field."),
]
BookIdArgument = Annotated[UUID, typer.Argument(help="Book identifier.")]
QueryCategoryOption = Annotated[str | None, typer.Option(help="Filter by category slug.")]
QuerySubCategoryOption = Annotated[
    str | None,
    typer.Option(help="Filter by sub-category slug."),
]
QueryFormatOption = Annotated[BookFormat | None, typer.Option(help="Filter by format.")]
QueryNameContainsOption = Annotated[
    str | None,
    typer.Option(help="Filter by name substring."),
]
QueryPublishedBeforeOption = Annotated[
    str | None,
    typer.Option(help="Filter books published on or before YYYY-MM-DD."),
]
QueryPublishedAfterOption = Annotated[
    str | None,
    typer.Option(help="Filter books published on or after YYYY-MM-DD."),
]
SortOption = Annotated[BookSortOption, typer.Option(help="Sort order.")]
PageOption = Annotated[int, typer.Option(help="Page number.", min=1)]
PageSizeOption = Annotated[int, typer.Option(help="Page size.", min=1, max=100)]
PurchaseUrlsOption = Annotated[
    list[str] | None,
    typer.Option("--purchase-url", help="Repeat to replace purchase URLs."),
]
ClearSubCategoryOption = Annotated[bool, typer.Option(help="Clear the sub-category.")]
ClearPurchaseUrlsOption = Annotated[bool, typer.Option(help="Clear all purchase URLs.")]
ClearThumbnailOption = Annotated[bool, typer.Option(help="Remove the current thumbnail.")]
ClearPublishedOnOption = Annotated[bool, typer.Option(help="Clear the publishing date.")]
ClearEditionOption = Annotated[bool, typer.Option(help="Clear the edition field.")]
ClearFormatOption = Annotated[bool, typer.Option(help="Clear the format field.")]
ClearPageLengthOption = Annotated[bool, typer.Option(help="Clear the page length field.")]
ClearNoteOption = Annotated[bool, typer.Option(help="Clear the note field.")]
YesOption = Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation.")]


@app.command()
def seed_taxonomy(path: SeedTaxonomyPath = Path("src/bookshelf/seeds/taxonomy.yaml")) -> None:
    with SessionLocal() as session:
        service = build_taxonomy_service(session)
        count = service.seed_from_file(path)
    typer.echo(f"Seeded {count} categories from {path}")


@app.command()
def categories() -> None:
    with SessionLocal() as session:
        service = build_taxonomy_service(session)
        items = service.list_categories()

    if not items:
        typer.echo("No categories available. Run `bookshelf seed-taxonomy` first.")
        raise typer.Exit(code=1)

    for category in items:
        typer.echo(f"{category.slug}: {category.name}")
        for sub_category in category.subcategories:
            typer.echo(f"  - {sub_category.slug}: {sub_category.name}")


@app.command()
def list(status: StatusFilterOption = None) -> None:
    _run_query_command(BookQueryInput(status=status))


@app.command()
def unread() -> None:
    _run_query_command(BookQueryInput(status=ReadingStatus.UNREAD))


@app.command()
def query(
    status: StatusFilterOption = None,
    category: QueryCategoryOption = None,
    sub_category: QuerySubCategoryOption = None,
    format: QueryFormatOption = None,
    name_contains: QueryNameContainsOption = None,
    published_before: QueryPublishedBeforeOption = None,
    published_after: QueryPublishedAfterOption = None,
    sort: SortOption = BookSortOption.CREATED_AT_DESC,
    page: PageOption = 1,
    page_size: PageSizeOption = 20,
) -> None:
    try:
        query_input = BookQueryInput(
            status=status,
            category_slug=category,
            sub_category_slug=sub_category,
            format=format,
            name_contains=name_contains,
            published_before=_parse_date_option(published_before),
            published_after=_parse_date_option(published_after),
            sort=sort,
            page=page,
            page_size=page_size,
        )
    except ValidationError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1) from exc

    _run_query_command(query_input)


@app.command()
def add(
    name: NameOption = None,
    category: CategoryOption = None,
    sub_category: SubCategoryOption = None,
    published_on: PublishedOnOption = None,
    edition: EditionOption = None,
    format: FormatOption = None,
    page_length: PageLengthOption = None,
    reading_status: ReadingStatusOption = None,
    thumbnail_path: ThumbnailPathOption = None,
    thumbnail_url: ThumbnailUrlOption = None,
    note_file: NoteFileOption = None,
) -> None:
    with SessionLocal() as session:
        taxonomy_service = build_taxonomy_service(session)
        categories_payload = taxonomy_service.list_categories()
        if not categories_payload:
            typer.echo("No categories available. Run `bookshelf seed-taxonomy` first.")
            raise typer.Exit(code=1)

        create_input = _prompt_for_book(
            categories_payload=categories_payload,
            name=name,
            category=category,
            sub_category=sub_category,
            published_on=published_on,
            edition=edition,
            format=format,
            page_length=page_length,
            reading_status=reading_status,
            thumbnail_path=thumbnail_path,
            thumbnail_url=thumbnail_url,
            note_file=note_file,
        )
        service = build_book_service(session)
        try:
            book = service.create_book(create_input)
        except ValidationError as exc:
            typer.echo(f"Error: {exc}")
            raise typer.Exit(code=1) from exc
        except ValueError as exc:
            typer.echo(f"Error: {exc}")
            raise typer.Exit(code=1) from exc

    typer.echo(f"Created book {book.id}: {book.name}")


@app.command()
def update(
    book_id: BookIdArgument,
    name: NameOption = None,
    category: CategoryOption = None,
    sub_category: SubCategoryOption = None,
    published_on: PublishedOnOption = None,
    edition: EditionOption = None,
    format: FormatOption = None,
    page_length: PageLengthOption = None,
    reading_status: ReadingStatusOption = None,
    thumbnail_path: ThumbnailPathOption = None,
    thumbnail_url: ThumbnailUrlOption = None,
    note_file: NoteFileOption = None,
    purchase_urls: PurchaseUrlsOption = None,
    clear_sub_category: ClearSubCategoryOption = False,
    clear_purchase_urls: ClearPurchaseUrlsOption = False,
    clear_thumbnail: ClearThumbnailOption = False,
    clear_published_on: ClearPublishedOnOption = False,
    clear_edition: ClearEditionOption = False,
    clear_format: ClearFormatOption = False,
    clear_page_length: ClearPageLengthOption = False,
    clear_note: ClearNoteOption = False,
) -> None:
    with SessionLocal() as session:
        book_service = build_book_service(session)
        taxonomy_service = build_taxonomy_service(session)

        try:
            current_book = book_service.get_book(book_id)
        except LookupError as exc:
            typer.echo(f"Error: {exc}")
            raise typer.Exit(code=1) from exc

        if _has_update_flags(
            name=name,
            category=category,
            sub_category=sub_category,
            published_on=published_on,
            edition=edition,
            format=format,
            page_length=page_length,
            reading_status=reading_status,
            thumbnail_path=thumbnail_path,
            thumbnail_url=thumbnail_url,
            note_file=note_file,
            purchase_urls=purchase_urls,
            clear_sub_category=clear_sub_category,
            clear_purchase_urls=clear_purchase_urls,
            clear_thumbnail=clear_thumbnail,
            clear_published_on=clear_published_on,
            clear_edition=clear_edition,
            clear_format=clear_format,
            clear_page_length=clear_page_length,
            clear_note=clear_note,
        ):
            try:
                update_input = BookUpdateInput(
                    name=name,
                    category_slug=category,
                    sub_category_slug=sub_category,
                    clear_sub_category=clear_sub_category,
                    purchase_urls=purchase_urls,
                    clear_purchase_urls=clear_purchase_urls,
                    thumbnail_path=thumbnail_path,
                    thumbnail_url=thumbnail_url,
                    clear_thumbnail=clear_thumbnail,
                    published_on=_parse_date_option(published_on),
                    clear_published_on=clear_published_on,
                    edition=edition,
                    clear_edition=clear_edition,
                    format=format,
                    clear_format=clear_format,
                    page_length=page_length,
                    clear_page_length=clear_page_length,
                    reading_status=reading_status,
                    note=_read_note_file(note_file),
                    clear_note=clear_note,
                )
            except ValidationError as exc:
                typer.echo(f"Error: {exc}")
                raise typer.Exit(code=1) from exc
        else:
            categories_payload = taxonomy_service.list_categories()
            try:
                update_input = _prompt_for_book_update(
                    current_book=current_book,
                    categories_payload=categories_payload,
                )
            except ValidationError as exc:
                typer.echo(f"Error: {exc}")
                raise typer.Exit(code=1) from exc

        try:
            updated_book = book_service.update_book(book_id, update_input)
        except ValidationError as exc:
            typer.echo(f"Error: {exc}")
            raise typer.Exit(code=1) from exc
        except (LookupError, ValueError) as exc:
            typer.echo(f"Error: {exc}")
            raise typer.Exit(code=1) from exc

    typer.echo(f"Updated book {updated_book.id}: {updated_book.name}")


@app.command()
def delete(book_id: BookIdArgument, yes: YesOption = False) -> None:
    if not yes:
        confirmed = typer.confirm(f"Delete book {book_id}?", default=False)
        if not confirmed:
            typer.echo("Deletion cancelled.")
            raise typer.Exit(code=1)

    with SessionLocal() as session:
        service = build_book_service(session)
        try:
            service.delete_book(book_id)
        except (LookupError, ValueError) as exc:
            typer.echo(f"Error: {exc}")
            raise typer.Exit(code=1) from exc

    typer.echo(f"Deleted book {book_id}")


def _prompt_for_book(
    *,
    categories_payload: list,
    name: str | None,
    category: str | None,
    sub_category: str | None,
    published_on: str | None,
    edition: str | None,
    format: BookFormat | None,
    page_length: int | None,
    reading_status: ReadingStatus | None,
    thumbnail_path: str | None,
    thumbnail_url: str | None,
    note_file: Path | None,
) -> BookCreateInput:
    category_map = {item.slug: item for item in categories_payload}

    book_name = name or typer.prompt("Book name")

    if category is None:
        typer.echo("Available categories:")
        for item in categories_payload:
            typer.echo(f"- {item.slug}: {item.name}")
        category = typer.prompt("Category slug")

    if category not in category_map:
        raise typer.BadParameter(f"Unknown category slug: {category}")

    category_entry = category_map[category]
    sub_category_value = sub_category
    if sub_category_value is None and category_entry.subcategories:
        typer.echo("Available sub-categories:")
        for item in category_entry.subcategories:
            typer.echo(f"- {item.slug}: {item.name}")
        entered = typer.prompt("Sub-category slug (optional)", default="", show_default=False)
        sub_category_value = entered or None

    if sub_category_value is not None:
        valid_sub_categories = {item.slug for item in category_entry.subcategories}
        if sub_category_value not in valid_sub_categories:
            raise typer.BadParameter(
                f"Unknown sub-category slug for category {category}: {sub_category_value}"
            )

    purchase_urls = _collect_purchase_urls()

    thumbnail_path_value = thumbnail_path
    thumbnail_url_value = thumbnail_url
    if thumbnail_path_value is None and thumbnail_url_value is None:
        source_mode = typer.prompt(
            "Thumbnail source [none/path/url]",
            default="none",
        ).strip().lower()
        if source_mode == "path":
            thumbnail_path_value = typer.prompt("Thumbnail file path")
        elif source_mode == "url":
            thumbnail_url_value = typer.prompt("Thumbnail URL")

    published_date = _parse_date(
        published_on
        if published_on is not None
        else typer.prompt("Publishing date YYYY-MM-DD (optional)", default="", show_default=False)
    )

    edition_value = edition
    if edition_value is None:
        edition_value = typer.prompt("Edition (optional)", default="", show_default=False) or None

    format_value = format
    if format_value is None:
        typer.echo(
            "Formats: " + ", ".join(item.value for item in BookFormat)
        )
        entered = typer.prompt("Format (optional)", default="", show_default=False)
        format_value = BookFormat(entered) if entered else None

    page_length_value = page_length
    if page_length_value is None:
        page_length_value = _parse_int(
            typer.prompt("Page length (optional)", default="", show_default=False)
        )

    reading_status_value = reading_status
    if reading_status_value is None:
        typer.echo("Reading statuses: unread, reading, read")
        entered = typer.prompt("Reading status", default=ReadingStatus.UNREAD.value)
        reading_status_value = ReadingStatus(entered)

    note = _resolve_note(note_file)

    return BookCreateInput(
        name=book_name,
        category_slug=category,
        sub_category_slug=sub_category_value,
        purchase_urls=purchase_urls,
        thumbnail_path=thumbnail_path_value,
        thumbnail_url=thumbnail_url_value,
        published_on=published_date,
        edition=edition_value,
        format=format_value,
        page_length=page_length_value,
        reading_status=reading_status_value,
        note=note,
    )


def _prompt_for_book_update(
    *,
    current_book: BookSchema,
    categories_payload: list,
) -> BookUpdateInput:
    category_map = {item.slug: item for item in categories_payload}

    book_name = _prompt_keep_or_replace(
        label="Book name",
        current_value=current_book.name,
    )

    typer.echo("Available categories:")
    for item in categories_payload:
        typer.echo(f"- {item.slug}: {item.name}")
    category_value = _prompt_keep_or_replace(
        label="Category slug",
        current_value=current_book.category.slug,
    )
    if category_value not in category_map:
        raise typer.BadParameter(f"Unknown category slug: {category_value}")

    category_entry = category_map[category_value]
    current_sub_category_slug = (
        current_book.sub_category.slug
        if current_book.sub_category is not None and current_book.category.slug == category_value
        else None
    )

    clear_sub_category = False
    sub_category_value = None
    if category_entry.subcategories:
        typer.echo("Available sub-categories:")
        for item in category_entry.subcategories:
            typer.echo(f"- {item.slug}: {item.name}")
        entered_sub_category = typer.prompt(
            "Sub-category slug (Enter to keep, '-' to clear)",
            default="",
            show_default=False,
        ).strip()
        if entered_sub_category == "-":
            clear_sub_category = True
        elif entered_sub_category:
            valid_sub_categories = {item.slug for item in category_entry.subcategories}
            if entered_sub_category not in valid_sub_categories:
                raise typer.BadParameter(
                    "Unknown sub-category slug for category "
                    f"{category_value}: {entered_sub_category}"
                )
            sub_category_value = entered_sub_category
        else:
            sub_category_value = current_sub_category_slug
    else:
        clear_sub_category = True

    replace_purchase_urls = typer.confirm("Replace purchase URLs?", default=False)
    purchase_urls = _collect_purchase_urls() if replace_purchase_urls else None

    thumbnail_action = typer.prompt(
        "Thumbnail action [keep/clear/path/url]",
        default="keep",
    ).strip().lower()
    thumbnail_path = None
    thumbnail_url = None
    clear_thumbnail = False
    if thumbnail_action == "clear":
        clear_thumbnail = True
    elif thumbnail_action == "path":
        thumbnail_path = typer.prompt("Thumbnail file path")
    elif thumbnail_action == "url":
        thumbnail_url = typer.prompt("Thumbnail URL")

    published_on_value, clear_published_on = _prompt_optional_date_update(
        label="Publishing date YYYY-MM-DD",
    )
    edition_value, clear_edition = _prompt_optional_text_update("Edition")
    format_value, clear_format = _prompt_optional_enum_update(
        label="Format",
        values=[item.value for item in BookFormat],
        parser=BookFormat,
    )
    page_length_value, clear_page_length = _prompt_optional_int_update("Page length")

    reading_status_entered = typer.prompt(
        "Reading status (Enter to keep)",
        default="",
        show_default=False,
    ).strip()
    reading_status_value = (
        ReadingStatus(reading_status_entered) if reading_status_entered else None
    )

    note_value, clear_note = _prompt_note_update(current_book.note)

    return BookUpdateInput(
        name=book_name if book_name != current_book.name else None,
        category_slug=category_value if category_value != current_book.category.slug else None,
        sub_category_slug=sub_category_value,
        clear_sub_category=clear_sub_category,
        purchase_urls=purchase_urls,
        clear_purchase_urls=replace_purchase_urls and purchase_urls == [],
        thumbnail_path=thumbnail_path,
        thumbnail_url=thumbnail_url,
        clear_thumbnail=clear_thumbnail,
        published_on=published_on_value,
        clear_published_on=clear_published_on,
        edition=edition_value,
        clear_edition=clear_edition,
        format=format_value,
        clear_format=clear_format,
        page_length=page_length_value,
        clear_page_length=clear_page_length,
        reading_status=reading_status_value,
        note=note_value,
        clear_note=clear_note,
    )


def _collect_purchase_urls() -> list[str]:
    typer.echo("Add purchase URLs. Leave blank when finished.")
    values: list[str] = []
    while True:
        value = typer.prompt("Purchase URL", default="", show_default=False).strip()
        if not value:
            return values
        values.append(value)


def _run_query_command(query_input: BookQueryInput) -> None:
    with SessionLocal() as session:
        service = build_book_service(session)
        try:
            result = service.query_books(query_input)
        except ValueError as exc:
            typer.echo(f"Error: {exc}")
            raise typer.Exit(code=1) from exc

    _render_query_result(result)


def _render_query_result(result: BookQueryResult) -> None:
    if not result.items:
        typer.echo("No books found.")
        return

    for book in result.items:
        typer.echo(_format_book_summary(book))

    typer.echo(
        f"Page {result.page}/{result.total_pages} | "
        f"page size {result.page_size} | total items {result.total_items}"
    )


def _format_book_summary(book: BookSchema) -> str:
    category_label = book.category.name
    if book.sub_category is not None:
        category_label = f"{category_label} / {book.sub_category.name}"
    return f"{book.id} | {book.name} | {category_label} | {book.reading_status}"


def _parse_date(value: str) -> date | None:
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return date.fromisoformat(stripped)
    except ValueError as exc:
        raise typer.BadParameter("Date must be in YYYY-MM-DD format") from exc


def _parse_date_option(value: str | None) -> date | None:
    if value is None:
        return None
    return _parse_date(value)


def _parse_int(value: str) -> int | None:
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return int(stripped)
    except ValueError as exc:
        raise typer.BadParameter("Expected an integer value") from exc


def _prompt_keep_or_replace(*, label: str, current_value: str) -> str:
    entered = typer.prompt(
        f"{label} (Enter to keep current: {current_value})",
        default="",
        show_default=False,
    ).strip()
    return entered or current_value


def _prompt_optional_text_update(label: str) -> tuple[str | None, bool]:
    entered = typer.prompt(
        f"{label} (Enter to keep, '-' to clear)",
        default="",
        show_default=False,
    ).strip()
    if not entered:
        return None, False
    if entered == "-":
        return None, True
    return entered, False


def _prompt_optional_date_update(label: str) -> tuple[date | None, bool]:
    entered = typer.prompt(
        f"{label} (Enter to keep, '-' to clear)",
        default="",
        show_default=False,
    ).strip()
    if not entered:
        return None, False
    if entered == "-":
        return None, True
    return _parse_date(entered), False


def _prompt_optional_int_update(label: str) -> tuple[int | None, bool]:
    entered = typer.prompt(
        f"{label} (Enter to keep, '-' to clear)",
        default="",
        show_default=False,
    ).strip()
    if not entered:
        return None, False
    if entered == "-":
        return None, True
    parsed = _parse_int(entered)
    return parsed, False


def _prompt_optional_enum_update(
    *,
    label: str,
    values: list[str],
    parser,
) -> tuple[object | None, bool]:
    typer.echo(f"{label} values: {', '.join(values)}")
    entered = typer.prompt(
        f"{label} (Enter to keep, '-' to clear)",
        default="",
        show_default=False,
    ).strip()
    if not entered:
        return None, False
    if entered == "-":
        return None, True
    return parser(entered), False


def _prompt_note_update(current_note: str | None) -> tuple[str | None, bool]:
    action = typer.prompt(
        "Note action [keep/edit/clear]",
        default="keep",
    ).strip().lower()
    if action == "keep":
        return None, False
    if action == "clear":
        return None, True

    content = typer.edit(current_note or "")
    if content is None:
        return None, False
    normalized = content.strip()
    if not normalized:
        return None, True
    return normalized, False


def _read_note_file(note_file: Path | None) -> str | None:
    if note_file is None:
        return None
    return note_file.read_text(encoding="utf-8").strip() or None


def _has_update_flags(
    *,
    name: str | None,
    category: str | None,
    sub_category: str | None,
    published_on: str | None,
    edition: str | None,
    format: BookFormat | None,
    page_length: int | None,
    reading_status: ReadingStatus | None,
    thumbnail_path: str | None,
    thumbnail_url: str | None,
    note_file: Path | None,
    purchase_urls: list[str] | None,
    clear_sub_category: bool,
    clear_purchase_urls: bool,
    clear_thumbnail: bool,
    clear_published_on: bool,
    clear_edition: bool,
    clear_format: bool,
    clear_page_length: bool,
    clear_note: bool,
) -> bool:
    return any(
        value is not None
        for value in [
            name,
            category,
            sub_category,
            published_on,
            edition,
            format,
            page_length,
            reading_status,
            thumbnail_path,
            thumbnail_url,
            note_file,
            purchase_urls,
        ]
    ) or any(
        [
            clear_sub_category,
            clear_purchase_urls,
            clear_thumbnail,
            clear_published_on,
            clear_edition,
            clear_format,
            clear_page_length,
            clear_note,
        ]
    )


def _resolve_note(note_file: Path | None) -> str | None:
    if note_file is not None:
        return note_file.read_text(encoding="utf-8").strip() or None

    content = typer.edit("# Write notes about the book below.\n")
    if content is None:
        return None
    lines = [line for line in content.splitlines() if not line.strip().startswith("#")]
    normalized = "\n".join(lines).strip()
    return normalized or None


if __name__ == "__main__":
    app()
