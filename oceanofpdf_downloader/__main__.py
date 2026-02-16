import sys

from loguru import logger

from oceanofpdf_downloader.config import Config
from oceanofpdf_downloader.display import display_book_records
from oceanofpdf_downloader.filters import filter_books
from oceanofpdf_downloader.models import BookState
from oceanofpdf_downloader.repository import BookRepository
from oceanofpdf_downloader.scraper import BookScraper


def main() -> None:
    logger.info("OceanOfPDF Downloader starting")

    try:
        max_pages = int(input("How many pages to scrape? [1]: ").strip() or "1")
    except ValueError:
        logger.error("Invalid number, using 1")
        max_pages = 1

    if max_pages < 1:
        logger.error("Number must be >= 1, using 1")
        max_pages = 1

    config = Config(max_pages=max_pages)
    logger.info("Config: max_pages={}, pause={}s, download_dir={}", config.max_pages, config.pause_seconds, config.download_dir)

    with BookScraper(config) as scraper:
        books = scraper.scrape_all_pages()

    books = filter_books(books)

    repo = BookRepository()
    new_count = repo.import_books(books)
    logger.info("Imported {} new books ({} duplicates skipped)", new_count, len(books) - new_count)

    new_books = repo.get_books_by_state(BookState.NEW)
    display_book_records(new_books)

    logger.info("Done. {} new books in database.", len(new_books))


if __name__ == "__main__":
    main()
