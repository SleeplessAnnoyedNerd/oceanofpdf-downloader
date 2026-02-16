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
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_table()

    def _connect(self) -> sqlite3.Connection:
        return self._conn

    def _create_table(self) -> None:
        self._conn.execute(CREATE_TABLE_SQL)
        self._conn.commit()

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
        cursor = self._conn.execute(INSERT_BOOK_SQL, (book.title, book.detail_url, book.language, book.genre))
        self._conn.commit()
        if cursor.rowcount == 0:
            return None
        record_row = self._conn.execute("SELECT * FROM books WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return self._row_to_record(record_row)

    def import_books(self, books: list[Book]) -> int:
        count = 0
        for book in books:
            if self.insert_book(book) is not None:
                count += 1
        return count

    def get_by_url(self, detail_url: str) -> BookRecord | None:
        row = self._conn.execute("SELECT * FROM books WHERE detail_url = ?", (detail_url,)).fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def get_books_by_state(self, state: BookState) -> list[BookRecord]:
        rows = self._conn.execute("SELECT * FROM books WHERE state = ?", (state.value,)).fetchall()
        return [self._row_to_record(row) for row in rows]

    def update_state(self, book_id: int, state: BookState) -> None:
        self._conn.execute(
            "UPDATE books SET state = ?, updated_at = datetime('now') WHERE id = ?",
            (state.value, book_id),
        )
        self._conn.commit()
