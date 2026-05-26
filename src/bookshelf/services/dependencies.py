from sqlalchemy.orm import Session

from bookshelf.config.settings import get_settings
from bookshelf.services.books import BookService
from bookshelf.services.taxonomy import TaxonomyService
from bookshelf.storage.thumbnails import ThumbnailStorage


def build_thumbnail_storage() -> ThumbnailStorage:
    return ThumbnailStorage(get_settings())


def build_book_service(session: Session) -> BookService:
    return BookService(session=session, thumbnail_storage=build_thumbnail_storage())


def build_taxonomy_service(session: Session) -> TaxonomyService:
    return TaxonomyService(session=session)
