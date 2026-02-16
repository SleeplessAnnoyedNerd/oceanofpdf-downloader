# Step 2: Book Listing Prototype — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Scrape oceanofpdf.com/recently-added/ and display all books (title, URL, language, genre) in a rich table, up to a user-specified number of pages.

**Architecture:** Class-based with separate modules. `BookScraper` wraps Playwright (headed Chromium), parses listing pages, returns `Book` dataclass instances. `display_books()` renders results via rich. Entry point asks for max pages, scrapes, filters (stub), displays.

**Tech Stack:** Python 3, Playwright, rich, loguru, pytest

---

### Task 1: Project scaffolding and dependencies

**Files:**
- Create: `requirements.txt`
- Create: `oceanofpdf_downloader/__init__.py`
- Create: `tests/__init__.py`

**Step 1: Create requirements.txt**

```
playwright
rich
loguru
pytest
```

**Step 2: Create package and test directories**

```bash
mkdir -p oceanofpdf_downloader tests
touch oceanofpdf_downloader/__init__.py tests/__init__.py
```

**Step 3: Set up venv and install dependencies**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

**Step 4: Verify installation**

```bash
source venv/bin/activate
python -c "import playwright; import rich; import loguru; print('OK')"
```
Expected: `OK`

**Step 5: Commit**

```bash
git add requirements.txt oceanofpdf_downloader/__init__.py tests/__init__.py
git commit -m "feat: project scaffolding with dependencies"
```

---

### Task 2: Book model

**Files:**
- Create: `oceanofpdf_downloader/models.py`
- Create: `tests/test_models.py`

**Step 1: Write the failing test**

```python
# tests/test_models.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError` or `ImportError`

**Step 3: Write minimal implementation**

```python
# oceanofpdf_downloader/models.py
from dataclasses import dataclass


@dataclass
class Book:
    title: str
    detail_url: str
    language: str
    genre: str
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add oceanofpdf_downloader/models.py tests/test_models.py
git commit -m "feat: add Book dataclass model"
```

---

### Task 3: Config

**Files:**
- Create: `oceanofpdf_downloader/config.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing test**

```python
# tests/test_config.py
import os
from oceanofpdf_downloader.config import Config


def test_config_defaults():
    config = Config(max_pages=3)
    assert config.max_pages == 3
    assert config.pause_seconds == 2.0
    assert config.download_dir == os.path.expanduser("~/Downloads")
    assert config.base_url == "https://oceanofpdf.com/recently-added/"
    assert config.headless is False


def test_config_custom():
    config = Config(
        max_pages=5,
        pause_seconds=1.0,
        download_dir="/tmp/books",
        headless=True,
    )
    assert config.max_pages == 5
    assert config.pause_seconds == 1.0
    assert config.download_dir == "/tmp/books"
    assert config.headless is True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

```python
# oceanofpdf_downloader/config.py
import os
from dataclasses import dataclass, field


@dataclass
class Config:
    max_pages: int
    pause_seconds: float = 2.0
    download_dir: str = field(default_factory=lambda: os.path.expanduser("~/Downloads"))
    base_url: str = "https://oceanofpdf.com/recently-added/"
    headless: bool = False
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add oceanofpdf_downloader/config.py tests/test_config.py
git commit -m "feat: add Config dataclass with defaults"
```

---

### Task 4: Filter stub

**Files:**
- Create: `oceanofpdf_downloader/filters.py`
- Create: `tests/test_filters.py`

**Step 1: Write the failing test**

```python
# tests/test_filters.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_filters.py -v`
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

```python
# oceanofpdf_downloader/filters.py
from oceanofpdf_downloader.models import Book


def filter_books(books: list[Book]) -> list[Book]:
    """Filter books based on criteria. Currently a stub that passes all books through."""
    return books
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_filters.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add oceanofpdf_downloader/filters.py tests/test_filters.py
git commit -m "feat: add filter_books stub"
```

---

### Task 5: Utils / rename stub

**Files:**
- Create: `oceanofpdf_downloader/utils.py`
- Create: `tests/test_utils.py`

**Step 1: Write the failing test**

```python
# tests/test_utils.py
from oceanofpdf_downloader.utils import rename_file


def test_rename_file_returns_same():
    assert rename_file("Sweet_Temptation_-_Cora_Kent.pdf") == "Sweet_Temptation_-_Cora_Kent.pdf"


def test_rename_file_empty():
    assert rename_file("") == ""
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_utils.py -v`
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

```python
# oceanofpdf_downloader/utils.py


def rename_file(filename: str) -> str:
    """Rename a downloaded file. Currently a stub that returns the original name."""
    return filename
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_utils.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add oceanofpdf_downloader/utils.py tests/test_utils.py
git commit -m "feat: add rename_file stub"
```

---

### Task 6: Scraper — HTML parsing logic

This is the core task. We separate parsing from browser navigation so parsing can be tested with mocked HTML.

**Files:**
- Create: `oceanofpdf_downloader/scraper.py`
- Create: `tests/test_scraper.py`

**Step 1: Write the failing test for parsing a single book entry**

The test uses a realistic HTML fixture based on the spec example. Note: language and genre appear in the article content after the header, inside `<strong>` tags.

```python
# tests/test_scraper.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_scraper.py::test_parse_single_book -v`
Expected: FAIL with `ImportError`

**Step 3: Write the failing test for multiple books**

```python
# append to tests/test_scraper.py

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
```

**Step 4: Write minimal implementation of parse_books_from_html**

```python
# oceanofpdf_downloader/scraper.py
import re
import time

from loguru import logger
from playwright.sync_api import sync_playwright

from oceanofpdf_downloader.config import Config
from oceanofpdf_downloader.models import Book


def parse_books_from_html(html: str) -> list[Book]:
    """Parse book entries from a listing page's HTML.

    Extracts books from <article> elements containing <header class="entry-header">.
    Title and URL come from a.entry-title-link.
    Language and genre come from <strong>Language: </strong> and <strong>Genre: </strong>
    tags in the article's content.
    """
    from html.parser import HTMLParser

    # Use a simple regex-based approach on the HTML string.
    # Split by article boundaries to isolate each book entry.
    books: list[Book] = []

    # Find all article blocks (or fall back to header blocks)
    article_pattern = re.compile(
        r'<article[^>]*>(.+?)</article>', re.DOTALL
    )
    articles = article_pattern.findall(html)

    # If no <article> tags, try to find headers directly
    if not articles:
        header_pattern = re.compile(
            r'<header class="entry-header">(.+?)</header>', re.DOTALL
        )
        articles = header_pattern.findall(html)
        if not articles:
            return []

    for article_html in articles:
        # Extract title and URL from entry-title-link
        title_match = re.search(
            r'<a\s+class="entry-title-link"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
            article_html,
        )
        if not title_match:
            continue

        detail_url = title_match.group(1)
        title = title_match.group(2).strip()

        # Extract language
        lang_match = re.search(
            r'<strong>\s*Language:\s*</strong>\s*([^<]+)', article_html
        )
        language = lang_match.group(1).strip() if lang_match else "Unknown"

        # Extract genre
        genre_match = re.search(
            r'<strong>\s*Genre:\s*</strong>\s*([^<]+)', article_html
        )
        genre = genre_match.group(1).strip() if genre_match else "Unknown"

        books.append(Book(
            title=title,
            detail_url=detail_url,
            language=language,
            genre=genre,
        ))

    return books
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_scraper.py -v`
Expected: PASS (3 tests)

**Step 6: Commit**

```bash
git add oceanofpdf_downloader/scraper.py tests/test_scraper.py
git commit -m "feat: add parse_books_from_html with tests"
```

---

### Task 7: Scraper — BookScraper class (browser integration)

**Files:**
- Modify: `oceanofpdf_downloader/scraper.py`

**Step 1: Add BookScraper class to scraper.py**

Append to `oceanofpdf_downloader/scraper.py`:

```python
class BookScraper:
    """Scrapes book listings from oceanofpdf.com using Playwright."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._playwright = None
        self._browser = None

    def __enter__(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.config.headless)
        logger.info("Browser launched (headless={})", self.config.headless)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        logger.info("Browser closed")
        return False

    def _get_page_url(self, page_num: int) -> str:
        if page_num <= 1:
            return self.config.base_url
        return f"{self.config.base_url}page/{page_num}/"

    def scrape_listing_page(self, page_num: int) -> list[Book]:
        """Navigate to a listing page and extract all books."""
        url = self._get_page_url(page_num)
        logger.info("Scraping page {} — {}", page_num, url)

        page = self._browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded")
            html = page.content()
            books = parse_books_from_html(html)
            logger.info("Found {} books on page {}", len(books), page_num)
            return books
        finally:
            page.close()

    def scrape_all_pages(self) -> list[Book]:
        """Scrape all listing pages up to max_pages."""
        all_books: list[Book] = []
        for page_num in range(1, self.config.max_pages + 1):
            books = self.scrape_listing_page(page_num)
            all_books.extend(books)
            if page_num < self.config.max_pages:
                logger.info("Pausing {} seconds before next page...", self.config.pause_seconds)
                time.sleep(self.config.pause_seconds)
        logger.info("Total books found: {}", len(all_books))
        return all_books
```

**Step 2: Write a test for URL construction**

Append to `tests/test_scraper.py`:

```python
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
```

**Step 3: Run tests to verify they pass**

Run: `pytest tests/test_scraper.py -v`
Expected: PASS (5 tests)

**Step 4: Commit**

```bash
git add oceanofpdf_downloader/scraper.py tests/test_scraper.py
git commit -m "feat: add BookScraper class with browser management"
```

---

### Task 8: Display module

**Files:**
- Create: `oceanofpdf_downloader/display.py`
- Create: `tests/test_display.py`

**Step 1: Write the failing test**

```python
# tests/test_display.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_display.py -v`
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

```python
# oceanofpdf_downloader/display.py
from rich.console import Console
from rich.table import Table

from oceanofpdf_downloader.models import Book


def display_books(books: list[Book], console: Console | None = None) -> None:
    """Display books in a formatted rich table."""
    if console is None:
        console = Console()

    if not books:
        console.print("[yellow]No books found.[/yellow]")
        return

    table = Table(title=f"Books Found ({len(books)})")
    table.add_column("#", style="dim", width=5)
    table.add_column("Title", style="bold")
    table.add_column("Language")
    table.add_column("Genre")
    table.add_column("URL", style="dim")

    for i, book in enumerate(books, 1):
        table.add_row(str(i), book.title, book.language, book.genre, book.detail_url)

    console.print(table)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_display.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add oceanofpdf_downloader/display.py tests/test_display.py
git commit -m "feat: add display_books with rich table output"
```

---

### Task 9: Main entry point

**Files:**
- Create: `oceanofpdf_downloader/__main__.py`

**Step 1: Write the entry point**

```python
# oceanofpdf_downloader/__main__.py
import sys

from loguru import logger

from oceanofpdf_downloader.config import Config
from oceanofpdf_downloader.display import display_books
from oceanofpdf_downloader.filters import filter_books
from oceanofpdf_downloader.scraper import BookScraper


def main() -> None:
    logger.info("OceanOfPDF Downloader starting")

    try:
        max_pages = int(input("How many pages to scrape? [1]: ").strip() or "1")
    except ValueError:
        logger.error("Invalid number, using 1")
        max_pages = 1

    if max_pages < 1:
        logger.error("Number must be >= 1, using 1")
        max_pages = 1

    config = Config(max_pages=max_pages)
    logger.info("Config: max_pages={}, pause={}s, download_dir={}", config.max_pages, config.pause_seconds, config.download_dir)

    with BookScraper(config) as scraper:
        books = scraper.scrape_all_pages()

    books = filter_books(books)
    display_books(books)

    logger.info("Done. Found {} books total.", len(books))


if __name__ == "__main__":
    main()
```

**Step 2: Verify it runs (manual smoke test)**

Run: `python -m oceanofpdf_downloader`
Expected: Prompts for pages, launches browser, scrapes, shows table.

**Step 3: Commit**

```bash
git add oceanofpdf_downloader/__main__.py
git commit -m "feat: add __main__.py entry point"
```

---

### Task 10: Run all tests and final commit

**Step 1: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS (11 tests total)

**Step 2: Manual smoke test with the live site**

Run: `python -m oceanofpdf_downloader` (enter `1` for pages)
Expected: Browser opens, navigates to oceanofpdf.com/recently-added/, shows a table of books.

**Step 3: Fix any issues found during smoke test**

If parsing doesn't match the real site HTML, adjust regex patterns in `parse_books_from_html` and update test fixtures.

**Step 4: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: adjust parsing for live site HTML"
```
