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
    scraper = BookScraper(config, session=None)
    assert scraper._get_page_url(0) == "https://oceanofpdf.com/recently-added/"


def test_get_page_url_subsequent():
    config = Config(max_pages=3)
    scraper = BookScraper(config, session=None)
    assert scraper._get_page_url(2) == "https://oceanofpdf.com/recently-added/page/2/"
    assert scraper._get_page_url(3) == "https://oceanofpdf.com/recently-added/page/3/"


def test_get_page_url_non_paginated():
    config = Config(max_pages=1, base_url="https://oceanofpdf.com/new-releases/", paginated=False)
    scraper = BookScraper(config, session=None)
    assert scraper._get_page_url(0) == "https://oceanofpdf.com/new-releases/"
    assert scraper._get_page_url(5) == "https://oceanofpdf.com/new-releases/"


from oceanofpdf_downloader.scraper import parse_new_releases_from_html


NEW_RELEASES_HTML = """
<html><body>
<article class="post page entry" aria-label="New Releases">
  <div class="entry-content">
    <div class="row all-event-list mt20 book-list">
      <div class="col-lg-2 col-sm-3 col-6">
        <div class="widget-event">
          <a class="title-image" href="https://oceanofpdf.com/authors/jane-doe/pdf-epub-book-one-download/" title="Book One by Jane Doe">
            <img src="cover1.jpg" alt="" />
          </a>
          <div class="widget-event__info">
            <div class="title">
              <a href="https://oceanofpdf.com/authors/jane-doe/pdf-epub-book-one-download/" title="Book One by Jane Doe">Book One by Jane Doe</a>
            </div>
          </div>
        </div>
      </div>
      <div class="col-lg-2 col-sm-3 col-6">
        <div class="widget-event">
          <a class="title-image" href="https://oceanofpdf.com/authors/john-smith/pdf-epub-book-two-download/" title="Book Two by John Smith">
            <img src="cover2.jpg" alt="" />
          </a>
          <div class="widget-event__info">
            <div class="title">
              <a href="https://oceanofpdf.com/authors/john-smith/pdf-epub-book-two-download/" title="Book Two by John Smith">Book Two by John Smith</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</article>
</body></html>
"""


def test_parse_new_releases_count():
    books = parse_new_releases_from_html(NEW_RELEASES_HTML)
    assert len(books) == 2


def test_parse_new_releases_titles_and_urls():
    books = parse_new_releases_from_html(NEW_RELEASES_HTML)
    assert books[0].title == "Book One by Jane Doe"
    assert books[0].detail_url == "https://oceanofpdf.com/authors/jane-doe/pdf-epub-book-one-download/"
    assert books[1].title == "Book Two by John Smith"
    assert books[1].detail_url == "https://oceanofpdf.com/authors/john-smith/pdf-epub-book-two-download/"


def test_parse_new_releases_unknown_metadata():
    books = parse_new_releases_from_html(NEW_RELEASES_HTML)
    for book in books:
        assert book.language == "Unknown"
        assert book.genre == "Unknown"


def test_parse_new_releases_empty():
    books = parse_new_releases_from_html("<html><body><p>No books</p></body></html>")
    assert books == []
