from oceanofpdf_downloader.models import Book


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
