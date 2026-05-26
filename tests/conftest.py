from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from bookshelf.db.base import Base
from bookshelf.services.taxonomy import TaxonomyService
from tests.support import TAXONOMY_PATH


@pytest.fixture
def session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    try:
        yield factory
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def session(session_factory: sessionmaker[Session]) -> Session:
    with session_factory() as session:
        yield session


@pytest.fixture
def seeded_session(session: Session) -> Session:
    TaxonomyService(session).seed_from_file(TAXONOMY_PATH)
    return session
