from oceanofpdf_downloader.scraper import parse_books_from_html


# Real HTML structure: Language/Genre are in <div class="postmetainfo"> with <br> separators.
# Both Language and Genre are optional — absent fields fall back to "Unknown".
SINGLE_BOOK_HTML = """
<html><body>
<article class="post type-post status-publish format-standard has-post-thumbnail entry" aria-label="[PDF] [EPUB] State of Betrayal (Blurred Lines #1) Download">
  <header class="entry-header">
    <a class="entry-image-link" href="https://oceanofpdf.com/authors/a-denise/pdf-epub-state-of-betrayal-blurred-lines-1-download/" aria-hidden="true" tabindex="-1">
      <img width="150" height="225" src="https://media.oceanofpdf.com/2026/02/img.jpg" class="alignleft post-image entry-image" alt="" decoding="async">
    </a>
    <h2 class="entry-title">
      <a class="entry-title-link" rel="bookmark" href="https://oceanofpdf.com/authors/a-denise/pdf-epub-state-of-betrayal-blurred-lines-1-download/">State of Betrayal (Blurred Lines #1)</a>
    </h2>
  </header>
  <div class="postmetainfo"><strong>Author: </strong>A. Denise<br><strong>Language: </strong>English<br><strong>Genre: </strong>Historical Fiction, Historical Romance, Christmas</div>
  <div class="entry-content"><p>Some description.</p></div>
</article>
</body></html>
"""


def test_parse_single_book():
    books = parse_books_from_html(SINGLE_BOOK_HTML)
    assert len(books) == 1
    book = books[0]
    assert book.title == "State of Betrayal (Blurred Lines #1)"
    assert book.detail_url == "https://oceanofpdf.com/authors/a-denise/pdf-epub-state-of-betrayal-blurred-lines-1-download/"
    assert book.language == "English"
    assert book.genre == "Historical Fiction, Historical Romance, Christmas"


# Three books: both fields present / genre absent / both absent.
MULTI_BOOK_HTML = """
<html><body>
<article class="post type-post status-publish format-standard has-post-thumbnail entry">
  <header class="entry-header">
    <h2 class="entry-title">
      <a class="entry-title-link" rel="bookmark" href="https://oceanofpdf.com/book-a/">Book A by Author A</a>
    </h2>
  </header>
  <div class="postmetainfo"><strong>Author: </strong>Author A<br><strong>Language: </strong>English<br><strong>Genre: </strong>Fiction</div>
  <div class="entry-content"><p>Description A.</p></div>
</article>
<article class="post type-post status-publish format-standard has-post-thumbnail entry">
  <header class="entry-header">
    <h2 class="entry-title">
      <a class="entry-title-link" rel="bookmark" href="https://oceanofpdf.com/book-b/">Book B by Author B</a>
    </h2>
  </header>
  <div class="postmetainfo"><strong>Author: </strong>Author B<br><strong>Language: </strong>German<br></div>
  <div class="entry-content"><p>Description B.</p></div>
</article>
<article class="post type-post status-publish format-standard has-post-thumbnail entry">
  <header class="entry-header">
    <h2 class="entry-title">
      <a class="entry-title-link" rel="bookmark" href="https://oceanofpdf.com/book-c/">Book C by Author C</a>
    </h2>
  </header>
  <div class="postmetainfo"><strong>Author: </strong>Author C<br></div>
  <div class="entry-content"><p>Description C.</p></div>
</article>
</body></html>
"""


def test_parse_multiple_books():
    books = parse_books_from_html(MULTI_BOOK_HTML)
    assert len(books) == 3
    assert books[0].title == "Book A by Author A"
    assert books[0].language == "English"
    assert books[0].genre == "Fiction"
    assert books[1].title == "Book B by Author B"
    assert books[1].language == "German"
    assert books[1].genre == "Unknown"
    assert books[2].title == "Book C by Author C"
    assert books[2].language == "Unknown"
    assert books[2].genre == "Unknown"


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
