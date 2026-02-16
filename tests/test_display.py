from io import StringIO

from rich.console import Console

from oceanofpdf_downloader.display import display_book_records, display_books
from oceanofpdf_downloader.models import Book, BookRecord, BookState


def test_display_books_output():
    books = [
        Book(title="Book A", detail_url="http://a.com", language="English", genre="Fiction"),
        Book(title="Book B", detail_url="http://b.com", language="German", genre="Science"),
    ]
    console = Console(file=StringIO(), width=120)
    display_books(books, console=console)
    output = console.file.getvalue()
    assert "Book A" in output
    assert "Book B" in output
    assert "English" in output
    assert "German" in output


def test_display_books_empty():
    console = Console(file=StringIO(), width=120)
    display_books([], console=console)
    output = console.file.getvalue()
    assert "No books found" in output


def test_display_book_records_output():
    records = [
        BookRecord(id=1, title="Book A", detail_url="http://a.com", language="English", genre="Fiction", state=BookState.NEW, created_at="2026-02-16 12:00:00", updated_at="2026-02-16 12:00:00"),
        BookRecord(id=2, title="Book B", detail_url="http://b.com", language="German", genre="Science", state=BookState.SCHEDULED, created_at="2026-02-16 12:00:00", updated_at="2026-02-16 12:00:00"),
    ]
    console = Console(file=StringIO(), width=120)
    display_book_records(records, console=console)
    output = console.file.getvalue()
    assert "Book A" in output
    assert "Book B" in output
    assert "new" in output
    assert "scheduled" in output


def test_display_book_records_empty():
    console = Console(file=StringIO(), width=120)
    display_book_records([], console=console)
    output = console.file.getvalue()
    assert "No books found" in output
