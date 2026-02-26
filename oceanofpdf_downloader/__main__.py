import argparse

from loguru import logger
from rich.console import Console

from oceanofpdf_downloader.browser import BrowserSession
from oceanofpdf_downloader.config import load_config
from oceanofpdf_downloader.display import display_book_records
from oceanofpdf_downloader.downloader import BookDownloader
from oceanofpdf_downloader.filters import filter_books, is_autoselected, is_blacklisted
from oceanofpdf_downloader.live_display import LiveDisplay
from oceanofpdf_downloader.models import Book, BookState
from oceanofpdf_downloader.repository import BookRepository
from oceanofpdf_downloader.scraper import BookScraper
from oceanofpdf_downloader.selection import select_books


def main() -> None:
    parser = argparse.ArgumentParser(description="OceanOfPDF Downloader")
    parser.add_argument(
        "--editor", action="store_true",
        help="Launch the database editor instead of the downloader",
    )
    args = parser.parse_args()

    if args.editor:
        from oceanofpdf_downloader.editor import run_editor
        run_editor()
        return

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
        answer = console.input("Proceed with these books? [Y/n/q]: ").strip().lower()
        if answer in ("q", "quit"):
            logger.info("Quitting without changes.")
            return
        elif answer in ("", "y", "yes"):
            # Mark retry books as scheduled again
            for book in retry:
                repo.update_state(book.id, BookState.SCHEDULED)
            logger.info("Resuming with {} pending books", len(pending))
        else:
            for book in pending:
                repo.update_state(book.id, BookState.SKIPPED)
            logger.info("Skipped {} pending books", len(pending))
            pending = []

    console.print("\nSelect source:")
    console.print("  [1] Recently Added  (https://oceanofpdf.com/recently-added/)")
    console.print("  [2] New Releases    (https://oceanofpdf.com/new-releases/)")
    source_answer = input("Choice [1]: ").strip() or "1"

    if source_answer == "2":
        base_url = "https://oceanofpdf.com/new-releases/"
        paginated = False
        start_page = 0
        max_pages = 1
    else:
        base_url = "https://oceanofpdf.com/recently-added/"
        paginated = True

        try:
            start_page = int(input("Start from page? [0]: ").strip() or "0")
        except ValueError:
            logger.error("Invalid number, using 0")
            start_page = 0

        if start_page < 0:
            logger.error("Start page must be >= 0, using 0")
            start_page = 0

        try:
            max_pages = int(input("How many pages to scrape? [15]: ").strip() or "15")
        except ValueError:
            logger.error("Invalid number, using 15")
            max_pages = 15

        if max_pages == 0:
            if not pending:
                logger.info("Exiting.")
                return
            logger.info("max_pages=0, skipping scrape — will only download pending books.")

        if max_pages < 0:
            logger.error("Number must be >= 0, using 1")
            max_pages = 1

    headless_answer = input("Run browser headless? [y/N]: ").strip().lower()
    headless = headless_answer in ("y", "yes")

    config = load_config(
        max_pages=max_pages,
        start_page=start_page,
        headless=headless,
        base_url=base_url,
        paginated=paginated,
    )
    logger.info("Config: {}", config)

    live = LiveDisplay(config, console)
    logger.remove()
    logger.add(live.sink, colorize=False)

    with BrowserSession(config) as session:
        scraper = BookScraper(config, session)

        live.enable()
        books = scraper.scrape_all_pages(repo, live_display=live)
        live.disable()

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
                genre_str = f" ({record.genre})" if record.genre != "Unknown" else ""
                console.print(f"  - {record.title}{genre_str}")
            new_books = repo.get_books_by_state(BookState.NEW)

        # Auto-schedule matching books
        autoselected = []
        for record in new_books:
            book = Book(title=record.title, detail_url=record.detail_url,
                        language=record.language, genre=record.genre)
            if is_autoselected(book):
                repo.update_state(record.id, BookState.SCHEDULED)
                autoselected.append(record)
        if autoselected:
            logger.info("{} book(s) auto-scheduled by filter", len(autoselected))
            for record in autoselected:
                genre_str = f" ({record.genre})" if record.genre != "Unknown" else ""
                console.print(f"  - {record.title}{genre_str}")
            new_books = repo.get_books_by_state(BookState.NEW)

        newly_scheduled = select_books(new_books, repo, console)
        newly_scheduled.extend(autoselected)

        all_scheduled = pending + newly_scheduled
        logger.info("{} book(s) scheduled for download.", len(all_scheduled))

        if all_scheduled:
            downloader = BookDownloader(config, repo, session)
            live.enable()
            done = downloader.download_all(all_scheduled, console, live_display=live)
            live.disable()
            console.print(f"\n[bold]Download complete: {done}/{len(all_scheduled)} succeeded[/bold]")
        else:
            console.print("\n[yellow]No books scheduled for download.[/yellow]")


if __name__ == "__main__":
    main()
