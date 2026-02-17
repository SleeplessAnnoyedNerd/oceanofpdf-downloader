from oceanofpdf_downloader.filter_config import GENRE_BLACKLIST, TITLE_BLACKLIST
from oceanofpdf_downloader.models import Book


def is_blacklisted(book: Book) -> bool:
    """Check if a book matches any blacklist keyword (case-insensitive)."""
    title_lower = book.title.lower()
    genre_lower = book.genre.lower()

    for word in TITLE_BLACKLIST:
        if word.lower() in title_lower:
            return True

    for word in GENRE_BLACKLIST:
        if word.lower() in genre_lower:
            return True

    return False


def filter_books(books: list[Book]) -> list[Book]:
    """Filter out blacklisted books."""
    return [b for b in books if not is_blacklisted(b)]
