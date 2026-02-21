from loguru import logger
from rich.console import Console
from rich.prompt import Prompt

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
    indices = parse_selection(answer, len(page_records))

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
