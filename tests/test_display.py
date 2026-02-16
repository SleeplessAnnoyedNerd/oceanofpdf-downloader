from io import StringIO

from rich.console import Console

from oceanofpdf_downloader.display import display_books
from oceanofpdf_downloader.models import Book


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
