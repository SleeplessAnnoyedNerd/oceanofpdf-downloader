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
    parser.add_argument(
        "--train", action="store_true",
        help="Train the ML model from existing DONE/SKIPPED/BLACKLISTED books and exit",
    )
    parser.add_argument(
        "--check-training", action="store_true",
        help="Run the trained model against the database and print match statistics",
    )
    args = parser.parse_args()

    if args.train:
        from oceanofpdf_downloader.ml_selector import MLSelector
        config = load_config(max_pages=1)
        repo = BookRepository()
        ml = MLSelector(config)
        try:
            ml.train(repo)
        except ValueError as e:
            logger.error("Training failed: {}", e)
        return

    if args.check_training:
        from rich.table import Table
        from oceanofpdf_downloader.ml_selector import MLSelector
        config = load_config(max_pages=1)
        repo = BookRepository()
        ml = MLSelector(config)
        if not ml.load():
            logger.error("No trained model found — run with --train first")
            return
        console = Console()
        console.print(f"\n[bold]ML Model Check[/bold]")
        console.print(f"  Model     : {config.ml_model_path}")
        console.print(f"  Threshold : {config.ml_confidence_threshold}\n")

        table = Table(show_header=True, header_style="bold")
        table.add_column("State", style="cyan")
        table.add_column("Total", justify="right")
        table.add_column("Would schedule", justify="right")
        table.add_column("Would skip", justify="right")
        table.add_column("Avg score", justify="right")
        table.add_column("Min", justify="right")
        table.add_column("Max", justify="right")

        states_to_check = [
            BookState.DONE,
            BookState.SKIPPED,
            BookState.BLACKLISTED,
            BookState.NEW,
        ]
        training_tp = training_fn = training_fp = training_tn = 0

        for state in states_to_check:
            books = repo.get_books_by_state(state)
            if not books:
                continue
            scores = [ml.score(Book(b.title, b.detail_url, b.language, b.genre)) for b in books]
            scheduled = sum(1 for s in scores if s >= config.ml_confidence_threshold)
            skipped = len(scores) - scheduled
            avg = sum(scores) / len(scores)
            pct_sched = scheduled / len(scores) * 100
            pct_skip = skipped / len(scores) * 100
            table.add_row(
                state.value,
                str(len(books)),
                f"{scheduled} ({pct_sched:.0f}%)",
                f"{skipped} ({pct_skip:.0f}%)",
                f"{avg:.2f}",
                f"{min(scores):.2f}",
                f"{max(scores):.2f}",
            )
            if state == BookState.DONE:
                training_tp += scheduled
                training_fn += skipped
            elif state in (BookState.SKIPPED, BookState.BLACKLISTED):
                training_fp += scheduled
                training_tn += skipped

        console.print(table)

        # Training-data summary
        n_pos = training_tp + training_fn
        n_neg = training_fp + training_tn
        if n_pos:
            recall = training_tp / n_pos * 100
            console.print(f"[bold]Training data summary[/bold] ({n_pos} positive, {n_neg} negative):")
            console.print(f"  Recall on DONE (correctly scheduled)         : {recall:.1f}%")
        if n_neg:
            fpr = training_fp / n_neg * 100
            console.print(f"  False positive rate on SKIPPED/BLACKLISTED   : {fpr:.1f}%")
        console.print()
        return

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

        # ML auto-selection
        if config.ml_autoselect:
            from oceanofpdf_downloader.ml_selector import MLSelector
            ml_selector = MLSelector(config)
            if ml_selector.load():
                ml_selected = [r for r in new_books if ml_selector.predict(
                    Book(title=r.title, detail_url=r.detail_url,
                         language=r.language, genre=r.genre))]
                for record in ml_selected:
                    repo.update_state(record.id, BookState.SCHEDULED)
                if ml_selected:
                    logger.info("{} book(s) auto-scheduled by ML", len(ml_selected))
                    for r in ml_selected:
                        console.print(f"  [dim]ML[/dim] - {r.title} ({r.genre})")
                    new_books = repo.get_books_by_state(BookState.NEW)
            else:
                logger.warning("ml_autoselect enabled but no trained model — run with --train first")

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
