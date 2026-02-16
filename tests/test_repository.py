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


def test_import_books():
    repo = BookRepository(db_path=":memory:")
    books = [
        Book(title="Book A", detail_url="https://example.com/a", language="English", genre="Fiction"),
        Book(title="Book B", detail_url="https://example.com/b", language="German", genre="Science"),
        Book(title="Book A", detail_url="https://example.com/a", language="English", genre="Fiction"),  # duplicate
    ]
    count = repo.import_books(books)
    assert count == 2


def test_get_by_url():
    repo = BookRepository(db_path=":memory:")
    book = Book(title="Test Book", detail_url="https://example.com/book", language="English", genre="Fiction")
    repo.insert_book(book)
    record = repo.get_by_url("https://example.com/book")
    assert record is not None
    assert record.title == "Test Book"


def test_get_by_url_not_found():
    repo = BookRepository(db_path=":memory:")
    record = repo.get_by_url("https://example.com/nonexistent")
    assert record is None


def test_get_books_by_state():
    repo = BookRepository(db_path=":memory:")
    repo.insert_book(Book(title="A", detail_url="https://a", language="En", genre="F"))
    repo.insert_book(Book(title="B", detail_url="https://b", language="En", genre="F"))
    new_books = repo.get_books_by_state(BookState.NEW)
    assert len(new_books) == 2
    scheduled = repo.get_books_by_state(BookState.SCHEDULED)
    assert len(scheduled) == 0


def test_update_state():
    repo = BookRepository(db_path=":memory:")
    book = Book(title="Test", detail_url="https://test", language="En", genre="F")
    record = repo.insert_book(book)
    repo.update_state(record.id, BookState.SCHEDULED)
    updated = repo.get_by_url("https://test")
    assert updated.state == BookState.SCHEDULED
    assert updated.updated_at >= record.updated_at
