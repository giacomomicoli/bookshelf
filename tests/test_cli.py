import re

from typer.testing import CliRunner

from bookshelf.cli import main as cli_main
from tests.support import TAXONOMY_PATH


def test_cli_seed_and_add_book(session_factory, monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(cli_main, "SessionLocal", session_factory)
    monkeypatch.setattr(cli_main.typer, "edit", lambda _: "Dense notes about the book.")

    def extract_book_id(output: str) -> str:
        match = re.search(r"Created book ([0-9a-f-]{36}):", output)
        assert match is not None, output
        return match.group(1)

    seed_result = runner.invoke(cli_main.app, ["seed-taxonomy", "--path", str(TAXONOMY_PATH)])
    add_result = runner.invoke(
        cli_main.app,
        [
            "add",
            "--name",
            "My CLI Book",
            "--category",
            "essays",
            "--sub-category",
            "personal-essays",
        ],
        input="\nnone\n\n\n\n\n\n",
    )
    unread_result = runner.invoke(cli_main.app, ["unread"])
    query_result = runner.invoke(
        cli_main.app,
        ["query", "--status", "unread", "--page", "1", "--page-size", "10"],
    )
    book_id = extract_book_id(add_result.stdout)
    update_result = runner.invoke(
        cli_main.app,
        [
            "update",
            book_id,
            "--reading-status",
            "read",
            "--clear-note",
        ],
    )
    delete_result = runner.invoke(
        cli_main.app,
        ["delete", book_id, "--yes"],
    )
    missing_result = runner.invoke(cli_main.app, ["list"])

    assert seed_result.exit_code == 0
    assert "Seeded 14 categories" in seed_result.stdout
    assert add_result.exit_code == 0, add_result.stdout
    assert "Created book" in add_result.stdout
    assert unread_result.exit_code == 0
    assert "My CLI Book" in unread_result.stdout
    assert query_result.exit_code == 0
    assert "Page 1/1" in query_result.stdout
    assert update_result.exit_code == 0
    assert "Updated book" in update_result.stdout
    assert delete_result.exit_code == 0
    assert "Deleted book" in delete_result.stdout
    assert missing_result.exit_code == 0
    assert "No books found." in missing_result.stdout
