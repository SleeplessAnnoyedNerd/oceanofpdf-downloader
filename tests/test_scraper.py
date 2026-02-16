from oceanofpdf_downloader.scraper import parse_books_from_html


SINGLE_BOOK_HTML = """
<html><body>
<article class="post">
  <header class="entry-header">
    <a class="entry-image-link" href="https://oceanofpdf.com/authors/margaret-l-lial/pdf-college-algebra-and-trigonometry-by-margaret-l-lial-download/" aria-hidden="true" tabindex="-1">
      <img width="100" height="120" src="https://media.oceanofpdf.com/2026/02/img.jpg" class="alignleft post-image entry-image" alt="" />
    </a>
    <h2 class="entry-title">
      <a class="entry-title-link" rel="bookmark" href="https://oceanofpdf.com/authors/margaret-l-lial/pdf-college-algebra-and-trigonometry-by-margaret-l-lial-download/">College Algebra and Trigonometry by Margaret L. Lial</a>
    </h2>
  </header>
  <div class="entry-content">
    <p><strong>Language: </strong>English</p>
    <p><strong>Genre: </strong>Mathematics, Textbook</p>
  </div>
</article>
</body></html>
"""


def test_parse_single_book():
    books = parse_books_from_html(SINGLE_BOOK_HTML)
    assert len(books) == 1
    book = books[0]
    assert book.title == "College Algebra and Trigonometry by Margaret L. Lial"
    assert book.detail_url == "https://oceanofpdf.com/authors/margaret-l-lial/pdf-college-algebra-and-trigonometry-by-margaret-l-lial-download/"
    assert book.language == "English"
    assert book.genre == "Mathematics, Textbook"


MULTI_BOOK_HTML = """
<html><body>
<article class="post">
  <header class="entry-header">
    <h2 class="entry-title">
      <a class="entry-title-link" rel="bookmark" href="https://oceanofpdf.com/book-a/">Book A by Author A</a>
    </h2>
  </header>
  <div class="entry-content">
    <p><strong>Language: </strong>English</p>
    <p><strong>Genre: </strong>Fiction</p>
  </div>
</article>
<article class="post">
  <header class="entry-header">
    <h2 class="entry-title">
      <a class="entry-title-link" rel="bookmark" href="https://oceanofpdf.com/book-b/">Book B by Author B</a>
    </h2>
  </header>
  <div class="entry-content">
    <p><strong>Language: </strong>German</p>
    <p><strong>Genre: </strong>Science</p>
  </div>
</article>
</body></html>
"""


def test_parse_multiple_books():
    books = parse_books_from_html(MULTI_BOOK_HTML)
    assert len(books) == 2
    assert books[0].title == "Book A by Author A"
    assert books[0].language == "English"
    assert books[1].title == "Book B by Author B"
    assert books[1].language == "German"


EMPTY_HTML = "<html><body><p>No books here</p></body></html>"


def test_parse_empty_page():
    books = parse_books_from_html(EMPTY_HTML)
    assert books == []


from oceanofpdf_downloader.scraper import BookScraper
from oceanofpdf_downloader.config import Config


def test_get_page_url_first():
    config = Config(max_pages=1)
    scraper = BookScraper(config)
    assert scraper._get_page_url(1) == "https://oceanofpdf.com/recently-added/"


def test_get_page_url_subsequent():
    config = Config(max_pages=3)
    scraper = BookScraper(config)
    assert scraper._get_page_url(2) == "https://oceanofpdf.com/recently-added/page/2/"
    assert scraper._get_page_url(3) == "https://oceanofpdf.com/recently-added/page/3/"
