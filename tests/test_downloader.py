from unittest.mock import MagicMock, patch
import os

import pytest

from oceanofpdf_downloader.downloader import DownloadForm, parse_download_forms, BookDownloader
from oceanofpdf_downloader.config import Config
from oceanofpdf_downloader.models import BookRecord, BookState
from oceanofpdf_downloader.repository import BookRepository


SINGLE_FORM_HTML = """
<html><body>
<form method="post" action="https://oceanofpdf.com/Fetching_Resource.php">
  <input type="hidden" name="id" value="srv3">
  <input type="hidden" name="filename" value="MyBook.pdf">
  <input type="submit" value="Download PDF">
</form>
</body></html>
"""

TWO_FORMS_HTML = """
<html><body>
<form method="post" action="https://oceanofpdf.com/Fetching_Resource.php">
  <input type="hidden" name="id" value="srv1">
  <input type="hidden" name="filename" value="MyBook.pdf">
  <input type="submit" value="Download PDF">
</form>
<form method="post" action="https://oceanofpdf.com/Fetching_Resource.php">
  <input type="hidden" name="id" value="srv2">
  <input type="hidden" name="filename" value="MyBook.epub">
  <input type="submit" value="Download EPUB">
</form>
</body></html>
"""

NO_FORMS_HTML = """
<html><body>
<p>No download forms here.</p>
</body></html>
"""

UNRELATED_FORM_HTML = """
<html><body>
<form method="post" action="https://example.com/other">
  <input type="hidden" name="id" value="srv1">
  <input type="hidden" name="filename" value="other.pdf">
  <input type="submit" value="Submit">
</form>
</body></html>
"""


class TestParseDownloadForms:
    def test_single_form(self):
        forms = parse_download_forms(SINGLE_FORM_HTML)
        assert len(forms) == 1
        assert forms[0].server_id == "srv3"
        assert forms[0].filename == "MyBook.pdf"

    def test_two_forms(self):
        forms = parse_download_forms(TWO_FORMS_HTML)
        assert len(forms) == 2
        assert forms[0].server_id == "srv1"
        assert forms[0].filename == "MyBook.pdf"
        assert forms[1].server_id == "srv2"
        assert forms[1].filename == "MyBook.epub"

    def test_no_forms(self):
        forms = parse_download_forms(NO_FORMS_HTML)
        assert forms == []

    def test_unrelated_form_ignored(self):
        forms = parse_download_forms(UNRELATED_FORM_HTML)
        assert forms == []

    def test_form_missing_filename(self):
        html = """
        <form action="https://oceanofpdf.com/Fetching_Resource.php">
          <input type="hidden" name="id" value="srv1">
          <input type="submit" value="Download">
        </form>
        """
        forms = parse_download_forms(html)
        assert forms == []

    def test_form_missing_id(self):
        html = """
        <form action="https://oceanofpdf.com/Fetching_Resource.php">
          <input type="hidden" name="filename" value="Book.pdf">
          <input type="submit" value="Download">
        </form>
        """
        forms = parse_download_forms(html)
        assert forms == []


class TestBookDownloader:
    def _make_record(self, **kwargs):
        defaults = dict(
            id=1,
            title="Test Book",
            detail_url="https://oceanofpdf.com/test-book/",
            language="English",
            genre="Fiction",
            state=BookState.SCHEDULED,
            created_at="2026-01-01",
            updated_at="2026-01-01",
        )
        defaults.update(kwargs)
        return BookRecord(**defaults)

    def test_download_book_success(self, tmp_path):
        repo = BookRepository(db_path=":memory:")
        config = Config(max_pages=1, download_dir=str(tmp_path), pause_seconds=0)

        downloader = BookDownloader(config, repo)

        # Mock Playwright objects
        mock_download = MagicMock()
        mock_download.save_as = MagicMock()

        mock_page = MagicMock()
        mock_page.content.return_value = SINGLE_FORM_HTML

        # Set up expect_download context manager
        mock_download_ctx = MagicMock()
        mock_download_ctx.__enter__ = MagicMock(return_value=mock_download_ctx)
        mock_download_ctx.__exit__ = MagicMock(return_value=False)
        mock_download_ctx.value = mock_download
        mock_page.expect_download.return_value = mock_download_ctx

        # Mock the locator chain
        mock_form_locator = MagicMock()
        mock_ancestor_form = MagicMock()
        mock_submit = MagicMock()
        mock_form_locator.locator.return_value = mock_ancestor_form
        mock_ancestor_form.locator.return_value = mock_submit
        mock_page.locator.return_value.first = mock_form_locator

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        downloader._context = mock_context

        record = self._make_record()
        result = downloader.download_book(record)

        assert result is True
        mock_page.goto.assert_called_once_with(record.detail_url, wait_until="domcontentloaded")
        mock_download.save_as.assert_called_once_with(
            os.path.join(str(tmp_path), "MyBook.pdf")
        )
        mock_page.close.assert_called_once()

    def test_download_book_no_forms(self, tmp_path):
        repo = BookRepository(db_path=":memory:")
        config = Config(max_pages=1, download_dir=str(tmp_path), pause_seconds=0)

        downloader = BookDownloader(config, repo)

        mock_page = MagicMock()
        mock_page.content.return_value = NO_FORMS_HTML

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        downloader._context = mock_context

        record = self._make_record()
        result = downloader.download_book(record)

        assert result is False
        mock_page.close.assert_called_once()

    def test_download_all_updates_state(self, tmp_path):
        repo = BookRepository(db_path=":memory:")
        config = Config(max_pages=1, download_dir=str(tmp_path), pause_seconds=0)

        from oceanofpdf_downloader.models import Book
        repo.insert_book(Book(title="Book A", detail_url="https://example.com/a", language="English", genre="Fiction"))
        repo.update_state(1, BookState.SCHEDULED)

        downloader = BookDownloader(config, repo)
        console = MagicMock()

        # Patch download_book to return True
        downloader.download_book = MagicMock(return_value=True)
        downloader._context = MagicMock()

        records = repo.get_books_by_state(BookState.SCHEDULED)
        downloader.download_all(records, console)

        updated = repo.get_by_url("https://example.com/a")
        assert updated.state == BookState.DONE

    def test_download_all_marks_retry_on_failure(self, tmp_path):
        repo = BookRepository(db_path=":memory:")
        config = Config(max_pages=1, download_dir=str(tmp_path), pause_seconds=0)

        from oceanofpdf_downloader.models import Book
        repo.insert_book(Book(title="Book B", detail_url="https://example.com/b", language="English", genre="Fiction"))
        repo.update_state(1, BookState.SCHEDULED)

        downloader = BookDownloader(config, repo)
        console = MagicMock()

        downloader.download_book = MagicMock(return_value=False)
        downloader._context = MagicMock()

        records = repo.get_books_by_state(BookState.SCHEDULED)
        downloader.download_all(records, console)

        updated = repo.get_by_url("https://example.com/b")
        assert updated.state == BookState.RETRY
