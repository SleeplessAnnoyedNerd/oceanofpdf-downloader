# Step 3: Persistence — Design Doc

**Goal:** Store scraped books in SQLite so state (new, skipped, scheduled, done, retry) persists across sessions. Duplicates are skipped on re-scrape.

**Approach:** Raw `sqlite3` (no ORM). Single `BookRepository` class wraps all DB operations.

---

## Schema

```sql
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    detail_url TEXT NOT NULL UNIQUE,
    language TEXT NOT NULL DEFAULT 'Unknown',
    genre TEXT NOT NULL DEFAULT 'Unknown',
    state TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

- `detail_url` is the unique key for deduplication (INSERT OR IGNORE)
- `state` is one of: `new`, `skipped`, `scheduled`, `done`, `retry`
- ISO 8601 timestamps via SQLite `datetime('now')`

## DB Location

Fixed path: `~/.config/oceanofpdf-downloader/books.db`. Parent directory created automatically if missing.

## Models

`BookState` string enum enforces valid state values:

```python
class BookState(str, Enum):
    NEW = "new"
    SKIPPED = "skipped"
    SCHEDULED = "scheduled"
    DONE = "done"
    RETRY = "retry"
```

`BookRecord` dataclass represents a persisted row:

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

Existing `Book` dataclass stays as the scraping DTO. `Book` → scraped data in, `BookRecord` → persisted data out.

## Repository

`BookRepository` class with methods:

- `__init__(db_path=None)` — defaults to XDG path, creates dir/table
- `insert_book(book: Book) -> BookRecord | None` — INSERT OR IGNORE, returns None if duplicate
- `import_books(books: list[Book]) -> int` — bulk insert, returns count of newly inserted
- `get_by_url(detail_url: str) -> BookRecord | None` — lookup by URL
- `get_books_by_state(state: BookState) -> list[BookRecord]` — filter by state
- `update_state(book_id: int, state: BookState) -> None` — update state and updated_at

Testing uses `:memory:` DB.

## Integration

Flow changes from: scrape → filter → display
To: scrape → filter → **import to DB** → display new books

`display.py` gets a `display_book_records()` function that renders `list[BookRecord]` in a rich table with a State column.

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `oceanofpdf_downloader/models.py` | Modify | Add `BookState` enum and `BookRecord` dataclass |
| `oceanofpdf_downloader/repository.py` | Create | `BookRepository` class |
| `oceanofpdf_downloader/display.py` | Modify | Add `display_book_records()` |
| `oceanofpdf_downloader/__main__.py` | Modify | Wire up repository after scraping |
| `tests/test_models.py` | Modify | Tests for `BookState` and `BookRecord` |
| `tests/test_repository.py` | Create | Tests for all repository methods |
| `tests/test_display.py` | Modify | Test for `display_book_records()` |

No new dependencies — `sqlite3` is in the standard library.
