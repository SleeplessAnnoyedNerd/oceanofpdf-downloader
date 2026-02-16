from oceanofpdf_downloader.models import Book, BookState
from oceanofpdf_downloader.repository import BookRepository


def test_create_table():
    repo = BookRepository(db_path=":memory:")
    # Table should exist after init
    conn = repo._connect()
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='books'")
    assert cursor.fetchone() is not None
    conn.close()


def test_insert_book():
    repo = BookRepository(db_path=":memory:")
    book = Book(title="Test Book", detail_url="https://example.com/book", language="English", genre="Fiction")
    record = repo.insert_book(book)
    assert record is not None
    assert record.id == 1
    assert record.title == "Test Book"
    assert record.detail_url == "https://example.com/book"
    assert record.state == BookState.NEW
    assert record.created_at is not None


def test_insert_duplicate_skipped():
    repo = BookRepository(db_path=":memory:")
    book = Book(title="Test Book", detail_url="https://example.com/book", language="English", genre="Fiction")
    record1 = repo.insert_book(book)
    record2 = repo.insert_book(book)
    assert record1 is not None
    assert record2 is None
