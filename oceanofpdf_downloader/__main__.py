import sys

from loguru import logger

from oceanofpdf_downloader.config import Config
from oceanofpdf_downloader.display import display_books
from oceanofpdf_downloader.filters import filter_books
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
    display_books(books)

    logger.info("Done. Found {} books total.", len(books))


if __name__ == "__main__":
    main()
