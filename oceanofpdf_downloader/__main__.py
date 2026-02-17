from loguru import logger
from rich.console import Console

from oceanofpdf_downloader.config import Config
from oceanofpdf_downloader.display import display_book_records
from oceanofpdf_downloader.downloader import BookDownloader
from oceanofpdf_downloader.filters import filter_books
from oceanofpdf_downloader.models import BookState
from oceanofpdf_downloader.repository import BookRepository
from oceanofpdf_downloader.scraper import BookScraper
from oceanofpdf_downloader.selection import select_books


def main() -> None:
    logger.info("OceanOfPDF Downloader starting")

    console = Console()
    repo = BookRepository()

    # Check for previously scheduled books
    scheduled = repo.get_books_by_state(BookState.SCHEDULED)
    if scheduled:
        console.print(f"\n[bold cyan]{len(scheduled)} book(s) scheduled from a previous run:[/bold cyan]")
        display_book_records(scheduled, console)
        answer = console.input("Proceed with these scheduled books? [Y/n]: ").strip().lower()
        if answer in ("", "y", "yes"):
            logger.info("Resuming with {} previously scheduled books", len(scheduled))
        else:
            scheduled = []

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

    new_count = repo.import_books(books)
    logger.info("Imported {} new books ({} duplicates skipped)", new_count, len(books) - new_count)

    new_books = repo.get_books_by_state(BookState.NEW)
    newly_scheduled = select_books(new_books, repo, console)

    all_scheduled = scheduled + newly_scheduled
    logger.info("{} book(s) scheduled for download.", len(all_scheduled))

    if all_scheduled:
        with BookDownloader(config, repo) as downloader:
            downloader.download_all(all_scheduled, console)
    else:
        console.print("\n[yellow]No books scheduled for download.[/yellow]")


if __name__ == "__main__":
    main()
