from oceanofpdf_downloader.models import Book, BookRecord, BookState


def test_book_creation():
    book = Book(
        title="College Algebra and Trigonometry by Margaret L. Lial",
        detail_url="https://oceanofpdf.com/authors/margaret-l-lial/pdf-college-algebra-and-trigonometry-by-margaret-l-lial-download/",
        language="English",
        genre="Mathematics",
    )
    assert book.title == "College Algebra and Trigonometry by Margaret L. Lial"
    assert book.detail_url.startswith("https://")
    assert book.language == "English"
    assert book.genre == "Mathematics"


def test_book_equality():
    book1 = Book(title="A", detail_url="http://x", language="English", genre="Fiction")
    book2 = Book(title="A", detail_url="http://x", language="English", genre="Fiction")
    assert book1 == book2


def test_book_state_values():
    assert BookState.NEW == "new"
    assert BookState.SKIPPED == "skipped"
    assert BookState.SCHEDULED == "scheduled"
    assert BookState.DONE == "done"
    assert BookState.RETRY == "retry"


def test_book_state_from_string():
    assert BookState("new") == BookState.NEW
    assert BookState("done") == BookState.DONE


def test_book_record_creation():
    record = BookRecord(
        id=1,
        title="Test Book",
        detail_url="https://example.com/book",
        language="English",
        genre="Fiction",
        state=BookState.NEW,
        created_at="2026-02-16 12:00:00",
        updated_at="2026-02-16 12:00:00",
    )
    assert record.id == 1
    assert record.state == BookState.NEW
    assert record.created_at == "2026-02-16 12:00:00"
