from rich.console import Console
from rich.table import Table

from oceanofpdf_downloader.models import Book, BookRecord


def display_books(books: list[Book], console: Console | None = None) -> None:
    """Display books in a formatted rich table."""
    if console is None:
        console = Console()

    if not books:
        console.print("[yellow]No books found.[/yellow]")
        return

    table = Table(title=f"Books Found ({len(books)})")
    table.add_column("#", style="dim", width=5)
    table.add_column("Title", style="bold")
    table.add_column("Language")
    table.add_column("Genre")
    table.add_column("URL", style="dim")

    for i, book in enumerate(books, 1):
        table.add_row(str(i), book.title, book.language, book.genre, book.detail_url)

    console.print(table)


def display_book_records(records: list[BookRecord], console: Console | None = None) -> None:
    """Display book records in a formatted rich table with state column."""
    if console is None:
        console = Console()

    if not records:
        console.print("[yellow]No books found.[/yellow]")
        return

    table = Table(title=f"Books Found ({len(records)})")
    table.add_column("#", style="dim", width=5)
    table.add_column("Title", style="bold")
    table.add_column("Language")
    table.add_column("Genre")
    table.add_column("State")
    table.add_column("URL", style="dim")

    for i, record in enumerate(records, 1):
        table.add_row(str(i), record.title, record.language, record.genre, record.state.value, record.detail_url)

    console.print(table)
