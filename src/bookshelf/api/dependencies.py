from collections.abc import Generator

from sqlalchemy.orm import Session

from bookshelf.db.session import get_session


def get_db_session() -> Generator[Session, None, None]:
    yield from get_session()
