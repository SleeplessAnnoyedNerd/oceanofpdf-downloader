from loguru import logger
from rich.console import Console
from rich.prompt import Prompt

from oceanofpdf_downloader.display import display_book_records
from oceanofpdf_downloader.models import BookRecord, BookState
from oceanofpdf_downloader.repository import BookRepository


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


def select_books(
    records: list[BookRecord],
    repo: BookRepository,
    console: Console | None = None,
) -> list[BookRecord]:
    """Prompt user to select NEW books for download. Returns SCHEDULED records."""
    if console is None:
        console = Console()

    if not records:
        console.print("[yellow]No new books to select.[/yellow]")
        return []

    display_book_records(records, console)

    answer = Prompt.ask(
        "Enter book numbers to download (e.g. 1,3,5 or 1-5 or all)",
        default="none",
        console=console,
    )

    indices = parse_selection(answer, len(records))

    if not indices:
        console.print("[dim]No books selected.[/dim]")
        return []

    scheduled: list[BookRecord] = []
    for i in sorted(indices):
        record = records[i - 1]
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

    console.print(f"[green]{len(scheduled)} book(s) scheduled for download.[/green]")
    return scheduled
