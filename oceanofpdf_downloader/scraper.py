import re
import time

from loguru import logger
from playwright.sync_api import sync_playwright

from oceanofpdf_downloader.config import Config
from oceanofpdf_downloader.models import Book


def parse_books_from_html(html: str) -> list[Book]:
    """Parse book entries from a listing page's HTML.

    Extracts books from <article> elements containing <header class="entry-header">.
    Title and URL come from a.entry-title-link.
    Language and genre come from <strong>Language: </strong> and <strong>Genre: </strong>
    tags in the article's content.
    """
    books: list[Book] = []

    # Find all article blocks (or fall back to header blocks)
    article_pattern = re.compile(
        r'<article[^>]*>(.+?)</article>', re.DOTALL
    )
    articles = article_pattern.findall(html)

    # If no <article> tags, try to find headers directly
    if not articles:
        header_pattern = re.compile(
            r'<header class="entry-header">(.+?)</header>', re.DOTALL
        )
        articles = header_pattern.findall(html)
        if not articles:
            return []

    for article_html in articles:
        # Extract title and URL from entry-title-link
        title_match = re.search(
            r'<a\s+class="entry-title-link"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
            article_html,
        )
        if not title_match:
            continue

        detail_url = title_match.group(1)
        title = title_match.group(2).strip()

        # Extract language
        lang_match = re.search(
            r'<strong>\s*Language:\s*</strong>\s*([^<]+)', article_html
        )
        language = lang_match.group(1).strip() if lang_match else "Unknown"

        # Extract genre
        genre_match = re.search(
            r'<strong>\s*Genre:\s*</strong>\s*([^<]+)', article_html
        )
        genre = genre_match.group(1).strip() if genre_match else "Unknown"

        books.append(Book(
            title=title,
            detail_url=detail_url,
            language=language,
            genre=genre,
        ))

    return books
