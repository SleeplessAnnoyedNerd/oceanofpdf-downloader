# Step 3: Persistence — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Store scraped books in SQLite with state tracking (new/skipped/scheduled/done/retry), skipping duplicates on re-scrape.

**Architecture:** `BookRepository` wraps Python's built-in `sqlite3` module. Single `books` table with `detail_url` as unique key. `BookState` enum and `BookRecord` dataclass added to models. DB lives at `~/.config/oceanofpdf-downloader/books.db`.

**Tech Stack:** Python 3, sqlite3 (stdlib), existing rich/loguru/pytest

---

### Task 1: Add BookState enum and BookRecord dataclass

**Files:**
- Modify: `oceanofpdf_downloader/models.py`
- Modify: `tests/test_models.py`

**Step 1: Write the failing tests**

Append to `tests/test_models.py`:

```python
from oceanofpdf_downloader.models import BookState, BookRecord


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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `ImportError` (BookState, BookRecord not yet defined)

**Step 3: Write minimal implementation**

Add to `oceanofpdf_downloader/models.py` (before the `Book` class):

```python
from enum import Enum


class BookState(str, Enum):
    NEW = "new"
    SKIPPED = "skipped"
    SCHEDULED = "scheduled"
    DONE = "done"
    RETRY = "retry"
```

Add after the `Book` class:

```python
@dataclass
class BookRecord:
    id: int
    title: str
    detail_url: str
    language: str
    genre: str
    state: BookState
    created_at: str
    updated_at: str
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_models.py -v`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add oceanofpdf_downloader/models.py tests/test_models.py
git commit -m "feat: add BookState enum and BookRecord dataclass"
```

---

### Task 2: BookRepository — create table and insert

**Files:**
- Create: `oceanofpdf_downloader/repository.py`
- Create: `tests/test_repository.py`

**Step 1: Write the failing tests**

```python
# tests/test_repository.py
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_repository.py -v`
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

```python
# oceanofpdf_downloader/repository.py
import os
import sqlite3

from oceanofpdf_downloader.models import Book, BookRecord, BookState

DB_DIR = os.path.expanduser("~/.config/oceanofpdf-downloader")
DB_PATH = os.path.join(DB_DIR, "books.db")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    detail_url TEXT NOT NULL UNIQUE,
    language TEXT NOT NULL DEFAULT 'Unknown',
    genre TEXT NOT NULL DEFAULT 'Unknown',
    state TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

INSERT_BOOK_SQL = """
INSERT OR IGNORE INTO books (title, detail_url, language, genre)
VALUES (?, ?, ?, ?)
"""


class BookRepository:
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or DB_PATH
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._create_table()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_table(self) -> None:
        conn = self._connect()
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()
        conn.close()

    def _row_to_record(self, row: sqlite3.Row) -> BookRecord:
        return BookRecord(
            id=row["id"],
            title=row["title"],
            detail_url=row["detail_url"],
            language=row["language"],
            genre=row["genre"],
            state=BookState(row["state"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def insert_book(self, book: Book) -> BookRecord | None:
        conn = self._connect()
        cursor = conn.execute(INSERT_BOOK_SQL, (book.title, book.detail_url, book.language, book.genre))
        conn.commit()
        if cursor.rowcount == 0:
            conn.close()
            return None
        record_row = conn.execute("SELECT * FROM books WHERE id = ?", (cursor.lastrowid,)).fetchone()
        conn.close()
        return self._row_to_record(record_row)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_repository.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add oceanofpdf_downloader/repository.py tests/test_repository.py
git commit -m "feat: add BookRepository with create table and insert"
```

---

### Task 3: BookRepository — import_books, get_by_url, get_books_by_state, update_state

**Files:**
- Modify: `oceanofpdf_downloader/repository.py`
- Modify: `tests/test_repository.py`

**Step 1: Write the failing tests**

Append to `tests/test_repository.py`:

```python
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
```

**Step 2: Run tests to verify new tests fail**

Run: `pytest tests/test_repository.py -v`
Expected: 3 PASS, 5 FAIL (new methods don't exist yet)

**Step 3: Write minimal implementation**

Add to `BookRepository` class in `oceanofpdf_downloader/repository.py`:

```python
    def import_books(self, books: list[Book]) -> int:
        count = 0
        for book in books:
            if self.insert_book(book) is not None:
                count += 1
        return count

    def get_by_url(self, detail_url: str) -> BookRecord | None:
        conn = self._connect()
        row = conn.execute("SELECT * FROM books WHERE detail_url = ?", (detail_url,)).fetchone()
        conn.close()
        if row is None:
            return None
        return self._row_to_record(row)

    def get_books_by_state(self, state: BookState) -> list[BookRecord]:
        conn = self._connect()
        rows = conn.execute("SELECT * FROM books WHERE state = ?", (state.value,)).fetchall()
        conn.close()
        return [self._row_to_record(row) for row in rows]

    def update_state(self, book_id: int, state: BookState) -> None:
        conn = self._connect()
        conn.execute(
            "UPDATE books SET state = ?, updated_at = datetime('now') WHERE id = ?",
            (state.value, book_id),
        )
        conn.commit()
        conn.close()
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_repository.py -v`
Expected: PASS (8 tests)

**Step 5: Commit**

```bash
git add oceanofpdf_downloader/repository.py tests/test_repository.py
git commit -m "feat: add import_books, get_by_url, get_books_by_state, update_state"
```

---

### Task 4: Display book records

**Files:**
- Modify: `oceanofpdf_downloader/display.py`
- Modify: `tests/test_display.py`

**Step 1: Write the failing test**

Append to `tests/test_display.py`:

```python
from oceanofpdf_downloader.display import display_book_records
from oceanofpdf_downloader.models import BookRecord, BookState


def test_display_book_records_output():
    records = [
        BookRecord(id=1, title="Book A", detail_url="http://a.com", language="English", genre="Fiction", state=BookState.NEW, created_at="2026-02-16 12:00:00", updated_at="2026-02-16 12:00:00"),
        BookRecord(id=2, title="Book B", detail_url="http://b.com", language="German", genre="Science", state=BookState.SCHEDULED, created_at="2026-02-16 12:00:00", updated_at="2026-02-16 12:00:00"),
    ]
    console = Console(file=StringIO(), width=120)
    display_book_records(records, console=console)
    output = console.file.getvalue()
    assert "Book A" in output
    assert "Book B" in output
    assert "new" in output
    assert "scheduled" in output


def test_display_book_records_empty():
    console = Console(file=StringIO(), width=120)
    display_book_records([], console=console)
    output = console.file.getvalue()
    assert "No books found" in output
```

**Step 2: Run tests to verify new tests fail**

Run: `pytest tests/test_display.py -v`
Expected: 2 PASS (existing), 2 FAIL (new)

**Step 3: Write minimal implementation**

Add to `oceanofpdf_downloader/display.py`:

```python
from oceanofpdf_downloader.models import Book, BookRecord


def display_book_records(records: list[BookRecord], console: Console | None = None) -> None:
    """Display book records in a formatted rich table with state column."""
    if console is None:
        console = Console()

    if not records:
        console.print("[yellow]No books found.[/yellow]")
        return

    table = Table(title=f"Books Found ({len(records)})")
    table.add_column("#", style="dim", width=5)
    table.add_column("Title", style="bold")
    table.add_column("Language")
    table.add_column("Genre")
    table.add_column("State")
    table.add_column("URL", style="dim")

    for i, record in enumerate(records, 1):
        table.add_row(str(i), record.title, record.language, record.genre, record.state.value, record.detail_url)

    console.print(table)
```

Note: Update the import line at top of `display.py` from `from oceanofpdf_downloader.models import Book` to `from oceanofpdf_downloader.models import Book, BookRecord`.

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_display.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add oceanofpdf_downloader/display.py tests/test_display.py
git commit -m "feat: add display_book_records with state column"
```

---

### Task 5: Wire up repository in __main__.py

**Files:**
- Modify: `oceanofpdf_downloader/__main__.py`

**Step 1: Update the entry point**

Replace the contents of `oceanofpdf_downloader/__main__.py` with:

```python
import sys

from loguru import logger

from oceanofpdf_downloader.config import Config
from oceanofpdf_downloader.display import display_book_records
from oceanofpdf_downloader.filters import filter_books
from oceanofpdf_downloader.repository import BookRepository
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

    repo = BookRepository()
    new_count = repo.import_books(books)
    logger.info("Imported {} new books ({} duplicates skipped)", new_count, len(books) - new_count)

    from oceanofpdf_downloader.models import BookState
    new_books = repo.get_books_by_state(BookState.NEW)
    display_book_records(new_books)

    logger.info("Done. {} new books in database.", len(new_books))


if __name__ == "__main__":
    main()
```

**Step 2: Run all tests to verify nothing broke**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add oceanofpdf_downloader/__main__.py
git commit -m "feat: wire up BookRepository in entry point"
```

---

### Task 6: Run all tests and final verification

**Step 1: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS (18+ tests total)

**Step 2: Manual smoke test**

Run: `python -m oceanofpdf_downloader` (enter `1` for pages)
Expected: Browser opens, scrapes, imports to DB, shows table with State column. Second run with same pages should show 0 new books imported.

**Step 3: Verify DB file exists**

Run: `ls -la ~/.config/oceanofpdf-downloader/books.db`
Expected: File exists with non-zero size.

**Step 4: Verify duplicate skipping**

Run `python -m oceanofpdf_downloader` again (enter `1`).
Expected: Log shows "Imported 0 new books (N duplicates skipped)".

**Step 5: Fix any issues and commit if needed**

```bash
git add -A
git commit -m "fix: adjust persistence for live site"
```
