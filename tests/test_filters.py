from oceanofpdf_downloader.filters import filter_books
from oceanofpdf_downloader.models import Book


def test_filter_books_passes_all():
    books = [
        Book(title="Book A", detail_url="http://a", language="English", genre="Fiction"),
        Book(title="Book B", detail_url="http://b", language="German", genre="Science"),
    ]
    result = filter_books(books)
    assert result == books
    assert len(result) == 2


def test_filter_books_empty_list():
    assert filter_books([]) == []
