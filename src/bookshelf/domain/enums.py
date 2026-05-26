from enum import StrEnum


class ReadingStatus(StrEnum):
    UNREAD = "unread"
    READING = "reading"
    READ = "read"


class BookFormat(StrEnum):
    HARDCOVER = "hardcover"
    PAPERBACK = "paperback"
    MASS_MARKET_PAPERBACK = "mass_market_paperback"
    EBOOK = "ebook"
    AUDIOBOOK = "audiobook"
    OTHER = "other"


class BookSortOption(StrEnum):
    CREATED_AT_DESC = "created_at_desc"
    CREATED_AT_ASC = "created_at_asc"
    PUBLISHED_ON_DESC = "published_on_desc"
    PUBLISHED_ON_ASC = "published_on_asc"
    NAME_ASC = "name_asc"
    NAME_DESC = "name_desc"
