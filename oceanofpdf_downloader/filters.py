import importlib

from loguru import logger

from oceanofpdf_downloader.filter_config import GENRE_BLACKLIST, TITLE_BLACKLIST
from oceanofpdf_downloader.models import Book


def _load_blacklists() -> tuple[list[str], list[str]]:
    """Merge base and local blacklists."""
    title = list(TITLE_BLACKLIST)
    genre = list(GENRE_BLACKLIST)

    try:
        local = importlib.import_module("oceanofpdf_downloader.filter_config_local")
        logger.info("Loaded local filter overrides from filter_config_local.py")
        title.extend(getattr(local, "TITLE_BLACKLIST", []))
        genre.extend(getattr(local, "GENRE_BLACKLIST", []))
    except ModuleNotFoundError:
        pass

    if title:
        logger.info("Title blacklist: {}", title)
    if genre:
        logger.info("Genre blacklist: {}", genre)

    return title, genre


_title_blacklist, _genre_blacklist = _load_blacklists()


def is_blacklisted(book: Book) -> bool:
    """Check if a book matches any blacklist keyword (case-insensitive)."""
    title_lower = book.title.lower()
    genre_lower = book.genre.lower()

    for word in _title_blacklist:
        if word.lower() in title_lower:
            return True

    for word in _genre_blacklist:
        if word.lower() in genre_lower:
            return True

    return False


def filter_books(books: list[Book]) -> list[Book]:
    """Filter out blacklisted books."""
    return [b for b in books if not is_blacklisted(b)]
