import re
import time

from loguru import logger

from oceanofpdf_downloader.browser import BrowserSession
from oceanofpdf_downloader.config import Config
from oceanofpdf_downloader.models import Book
from oceanofpdf_downloader.repository import BookRepository


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


class BookScraper:
    """Scrapes book listings from oceanofpdf.com using a shared BrowserSession."""

    def __init__(self, config: Config, session: BrowserSession) -> None:
        self.config = config
        self.session = session

    def _get_page_url(self, page_num: int) -> str:
        if page_num <= 1:
            return self.config.base_url
        return f"{self.config.base_url}page/{page_num}/"

    def scrape_listing_page(self, page_num: int) -> list[Book]:
        """Navigate to a listing page and extract all books."""
        url = self._get_page_url(page_num)
        logger.info("Scraping page {} — {}", page_num, url)

        page = self.session.new_page()
        try:
            self.session.navigate(page, url)
            html = page.content()
            books = parse_books_from_html(html)
            logger.info("Found {} books on page {}", len(books), page_num)
            return books
        finally:
            page.close()

    def scrape_all_pages(self, repo: BookRepository | None = None) -> list[Book]:
        """Scrape all listing pages up to max_pages.

        If a repository is provided, stops early when duplicates (books already
        in the database) are found on at least 2 different pages.
        """
        all_books: list[Book] = []
        pages_with_duplicates = 0
        for page_num in range(1, self.config.max_pages + 1):
            books = self.scrape_listing_page(page_num)
            all_books.extend(books)

            if repo and any(repo.get_by_url(b.detail_url) for b in books):
                pages_with_duplicates += 1
                if pages_with_duplicates >= 2:
                    logger.info("Duplicates found on {} pages, stopping early", pages_with_duplicates)
                    break

            if page_num < self.config.max_pages:
                logger.info("Pausing {} seconds before next page...", self.config.pause_seconds)
                time.sleep(self.config.pause_seconds)
        logger.info("Total books found: {}", len(all_books))
        return all_books
