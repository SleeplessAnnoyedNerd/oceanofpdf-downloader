import importlib

from loguru import logger

from oceanofpdf_downloader.filter_config import (
    GENRE_AUTOSELECT,
    GENRE_BLACKLIST,
    TITLE_AUTOSELECT,
    TITLE_BLACKLIST,
)
from oceanofpdf_downloader.models import Book


def _load_config() -> dict[str, list[str]]:
    """Merge base and local filter config."""
    config = {
        "title_blacklist": list(TITLE_BLACKLIST),
        "genre_blacklist": list(GENRE_BLACKLIST),
        "title_autoselect": list(TITLE_AUTOSELECT),
        "genre_autoselect": list(GENRE_AUTOSELECT),
    }

    try:
        local = importlib.import_module("oceanofpdf_downloader.filter_config_local")
        logger.info("Loaded local filter overrides from filter_config_local.py")
        config["title_blacklist"].extend(getattr(local, "TITLE_BLACKLIST", []))
        config["genre_blacklist"].extend(getattr(local, "GENRE_BLACKLIST", []))
        config["title_autoselect"].extend(getattr(local, "TITLE_AUTOSELECT", []))
        config["genre_autoselect"].extend(getattr(local, "GENRE_AUTOSELECT", []))
    except ModuleNotFoundError:
        pass

    if config["title_blacklist"]:
        logger.info("Title blacklist: {}", config["title_blacklist"])
    if config["genre_blacklist"]:
        logger.info("Genre blacklist: {}", config["genre_blacklist"])
    if config["title_autoselect"]:
        logger.info("Title autoselect: {}", config["title_autoselect"])
    if config["genre_autoselect"]:
        logger.info("Genre autoselect: {}", config["genre_autoselect"])

    return config


_config = _load_config()
_title_blacklist = _config["title_blacklist"]
_genre_blacklist = _config["genre_blacklist"]
_title_autoselect = _config["title_autoselect"]
_genre_autoselect = _config["genre_autoselect"]


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


def is_autoselected(book: Book) -> bool:
    """Check if a book matches any autoselect keyword (case-insensitive)."""
    title_lower = book.title.lower()
    genre_lower = book.genre.lower()

    for word in _title_autoselect:
        if word.lower() in title_lower:
            return True

    for word in _genre_autoselect:
        if word.lower() in genre_lower:
            return True

    return False


def filter_books(books: list[Book]) -> list[Book]:
    """Filter out blacklisted books."""
    return [b for b in books if not is_blacklisted(b)]
