from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from oceanofpdf_downloader.display import display_book_records
from oceanofpdf_downloader.models import BookRecord, BookState
from oceanofpdf_downloader.repository import BookRepository

PAGE_SIZE = 15


def parse_selection(input_str: str, max_index: int) -> set[int]:
    """Parse user input into a set of 1-based indices.

    Accepts: comma-separated numbers (1,3,5), ranges (2-5), 'all',
    empty string, or 'none'. Returns valid indices only.
    """
    text = input_str.strip().lower()

    if not text or text == "none":
        return set()

    if text == "all":
        return set(range(1, max_index + 1))

    result: set[int] = set()
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            bounds = part.split("-", 1)
            try:
                start = int(bounds[0].strip())
                end = int(bounds[1].strip())
            except ValueError:
                logger.warning("Ignoring invalid range: '{}'", part)
                continue
            for n in range(start, end + 1):
                if 1 <= n <= max_index:
                    result.add(n)
        else:
            try:
                n = int(part)
            except ValueError:
                logger.warning("Ignoring invalid number: '{}'", part)
                continue
            if 1 <= n <= max_index:
                result.add(n)

    return result


def _select_page(
    page_records: list[BookRecord],
    page_num: int,
    total_pages: int,
    repo: BookRepository,
    console: Console,
) -> list[BookRecord] | None:
    """Display one page of books and prompt for selection.

    Returns scheduled records, or None if the user quit with 'q'.
    """
    display_book_records(page_records, console)

    page_label = f" (page {page_num}/{total_pages})" if total_pages > 1 else ""
    answer = Prompt.ask(
        f"Select books to download{page_label} (e.g. 1,3,5 or 1-{len(page_records)} or all, q to stop)",
        default="none",
        console=console,
    )

    quit_requested = answer.strip().lower() == "q"
    indices = set() if quit_requested else parse_selection(answer, len(page_records))

    scheduled: list[BookRecord] = []
    for i, record in enumerate(page_records, 1):
        if i in indices:
            repo.update_state(record.id, BookState.SCHEDULED)
            scheduled.append(BookRecord(
                id=record.id,
                title=record.title,
                detail_url=record.detail_url,
                language=record.language,
                genre=record.genre,
                state=BookState.SCHEDULED,
                created_at=record.created_at,
                updated_at=record.updated_at,
            ))
        elif record.state == BookState.NEW:
            repo.update_state(record.id, BookState.SKIPPED)

    return None if quit_requested else scheduled


def _review_ml_page(
    page_records: list[BookRecord],
    page_num: int,
    total_pages: int,
    total_records: int,
    repo: BookRepository,
    console: Console,
) -> list[BookRecord]:
    """Display one page of ML-selected books and prompt for books to skip or blacklist.

    Returns the records from this page that were removed from SCHEDULED (skipped or blacklisted).
    """
    page_label = f" \u2014 page {page_num}/{total_pages}" if total_pages > 1 else ""

    console.print(Panel(
        f"{total_records} book(s) auto-scheduled by ML{page_label}\n"
        "Enter numbers to [bold]SKIP[/bold] (one-time) or [bold]BLACKLIST[/bold] (permanent).",
        title="\u26a0  ML REVIEW",
        border_style="red",
        title_align="left",
    ))

    display_book_records(page_records, console)

    removed: list[BookRecord] = []

    # --- Skip prompt ---
    console.print()
    skip_answer = Prompt.ask(
        "[red]Books to **SKIP** (e.g. 1,3 or 2-4), or Enter to keep all[/red]",
        default="",
        console=console,
    )
    to_skip = parse_selection(skip_answer, len(page_records))
    if to_skip:
        confirmed = Confirm.ask(
            f"Skip {len(to_skip)} book(s)? (not downloaded this time, not permanent)",
            default=False,
            console=console,
        )
        if confirmed:
            for i, record in enumerate(page_records, 1):
                if i in to_skip:
                    repo.update_state(record.id, BookState.SKIPPED)
                    logger.info("Skipped after ML review: {}", record.title)
                    removed.append(record)

    # --- Blacklist prompt ---
    already_removed = {r.id for r in removed}
    blacklist_answer = Prompt.ask(
        "Books to BLACKLIST permanently (e.g. 1,3 or 2-4), or Enter to keep all",
        default="",
        console=console,
    )
    to_blacklist = {
        i for i in parse_selection(blacklist_answer, len(page_records))
        if page_records[i - 1].id not in already_removed
    }
    if to_blacklist:
        confirmed = Confirm.ask(
            f"Are you sure you want to BLACKLIST {len(to_blacklist)} book(s)?",
            default=False,
            console=console,
        )
        if confirmed:
            for i, record in enumerate(page_records, 1):
                if i in to_blacklist:
                    repo.update_state(record.id, BookState.BLACKLISTED)
                    logger.info("Blacklisted after ML review: {}", record.title)
                    removed.append(record)

    return removed


def review_ml_selected(
    records: list[BookRecord],
    repo: BookRepository,
    console: Console,
) -> list[BookRecord]:
    """Show ML-selected books paged and let the user blacklist unwanted ones by number.

    Returns the records that remain SCHEDULED.
    """
    total_pages = (len(records) + PAGE_SIZE - 1) // PAGE_SIZE
    removed_ids: set[int] = set()

    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * PAGE_SIZE
        page_records = records[start:start + PAGE_SIZE]
        for r in _review_ml_page(page_records, page_num, total_pages, len(records), repo, console):
            removed_ids.add(r.id)

    return [r for r in records if r.id not in removed_ids]


def select_books(
    records: list[BookRecord],
    repo: BookRepository,
    console: Console | None = None,
) -> list[BookRecord]:
    """Prompt user to select NEW books for download, paged. Returns SCHEDULED records."""
    if console is None:
        console = Console()

    if not records:
        console.print("[yellow]No new books to select.[/yellow]")
        return []

    total_pages = (len(records) + PAGE_SIZE - 1) // PAGE_SIZE
    all_scheduled: list[BookRecord] = []

    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        page_records = records[start:end]

        scheduled = _select_page(page_records, page_num, total_pages, repo, console)
        if scheduled is None:
            break
        all_scheduled.extend(scheduled)

    if all_scheduled:
        console.print(f"[green]{len(all_scheduled)} book(s) scheduled for download.[/green]")
    else:
        console.print("[dim]No books selected.[/dim]")
    return all_scheduled
