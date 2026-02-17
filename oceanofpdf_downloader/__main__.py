from loguru import logger
from rich.console import Console

from oceanofpdf_downloader.browser import BrowserSession
from oceanofpdf_downloader.config import Config
from oceanofpdf_downloader.display import display_book_records
from oceanofpdf_downloader.downloader import BookDownloader
from oceanofpdf_downloader.filters import filter_books, is_blacklisted
from oceanofpdf_downloader.models import Book, BookState
from oceanofpdf_downloader.repository import BookRepository
from oceanofpdf_downloader.scraper import BookScraper
from oceanofpdf_downloader.selection import select_books


def main() -> None:
    logger.info("OceanOfPDF Downloader starting")

    console = Console()
    repo = BookRepository()

    # Check for previously scheduled and failed books
    scheduled = repo.get_books_by_state(BookState.SCHEDULED)
    retry = repo.get_books_by_state(BookState.RETRY)
    pending = scheduled + retry
    if pending:
        console.print(f"\n[bold cyan]{len(pending)} book(s) pending from a previous run "
                       f"({len(scheduled)} scheduled, {len(retry)} failed):[/bold cyan]")
        display_book_records(pending, console)
        answer = console.input("Proceed with these books? [Y/n]: ").strip().lower()
        if answer in ("", "y", "yes"):
            # Mark retry books as scheduled again
            for book in retry:
                repo.update_state(book.id, BookState.SCHEDULED)
            logger.info("Resuming with {} pending books", len(pending))
        else:
            pending = []

    try:
        max_pages = int(input("How many pages to scrape? [1]: ").strip() or "1")
    except ValueError:
        logger.error("Invalid number, using 1")
        max_pages = 1

    if max_pages < 1:
        logger.error("Number must be >= 1, using 1")
        max_pages = 1

    headless_answer = input("Run browser headless? [y/N]: ").strip().lower()
    headless = headless_answer in ("y", "yes")

    config = Config(max_pages=max_pages, headless=headless)
    logger.info("Config: max_pages={}, pause={}s, download_dir={}", config.max_pages, config.pause_seconds, config.download_dir)

    with BrowserSession(config) as session:
        scraper = BookScraper(config, session)
        books = scraper.scrape_all_pages(repo)

        books = filter_books(books)

        new_count = repo.import_books(books)
        logger.info("Imported {} new books ({} duplicates skipped)", new_count, len(books) - new_count)

        new_books = repo.get_books_by_state(BookState.NEW)

        # Mark blacklisted books
        blacklisted = []
        for record in new_books:
            book = Book(title=record.title, detail_url=record.detail_url,
                        language=record.language, genre=record.genre)
            if is_blacklisted(book):
                repo.update_state(record.id, BookState.BLACKLISTED)
                blacklisted.append(record)
        if blacklisted:
            logger.info("{} book(s) blacklisted by filter", len(blacklisted))
            for record in blacklisted:
                console.print(f"  - {record.title} ({record.genre})")
            new_books = repo.get_books_by_state(BookState.NEW)

        newly_scheduled = select_books(new_books, repo, console)

        all_scheduled = pending + newly_scheduled
        logger.info("{} book(s) scheduled for download.", len(all_scheduled))

        if all_scheduled:
            downloader = BookDownloader(config, repo, session)
            downloader.download_all(all_scheduled, console)
        else:
            console.print("\n[yellow]No books scheduled for download.[/yellow]")


if __name__ == "__main__":
    main()
