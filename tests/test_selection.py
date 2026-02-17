from unittest.mock import patch

from rich.console import Console

from oceanofpdf_downloader.models import Book, BookState
from oceanofpdf_downloader.repository import BookRepository
from oceanofpdf_downloader.selection import parse_selection, select_books


# --- parse_selection tests ---


def test_parse_selection_empty():
    assert parse_selection("", 10) == set()


def test_parse_selection_none():
    assert parse_selection("none", 10) == set()


def test_parse_selection_all():
    assert parse_selection("all", 5) == {1, 2, 3, 4, 5}


def test_parse_selection_single():
    assert parse_selection("3", 5) == {3}


def test_parse_selection_comma_separated():
    assert parse_selection("1,3,5", 5) == {1, 3, 5}


def test_parse_selection_range():
    assert parse_selection("2-4", 5) == {2, 3, 4}


def test_parse_selection_mixed():
    assert parse_selection("1,3-5,7", 10) == {1, 3, 4, 5, 7}


def test_parse_selection_out_of_range_ignored():
    assert parse_selection("0,3,6", 5) == {3}


def test_parse_selection_range_partially_out():
    assert parse_selection("4-8", 5) == {4, 5}


def test_parse_selection_invalid_ignored():
    assert parse_selection("abc,2,xyz", 5) == {2}


def test_parse_selection_invalid_range_ignored():
    assert parse_selection("a-b,3", 5) == {3}


def test_parse_selection_whitespace():
    assert parse_selection("  1 , 3 , 5  ", 5) == {1, 3, 5}


def test_parse_selection_all_case_insensitive():
    assert parse_selection("ALL", 3) == {1, 2, 3}
    assert parse_selection("All", 3) == {1, 2, 3}


# --- select_books tests ---


def _make_repo_with_books(count: int) -> tuple[BookRepository, list]:
    repo = BookRepository(db_path=":memory:")
    records = []
    for i in range(1, count + 1):
        book = Book(title=f"Book {i}", detail_url=f"https://example.com/{i}", language="English", genre="Fiction")
        record = repo.insert_book(book)
        records.append(record)
    return repo, records


def test_select_books_none_selected():
    repo, records = _make_repo_with_books(3)
    console = Console(file=open("/dev/null", "w"))

    with patch("oceanofpdf_downloader.selection.Prompt.ask", return_value="none"):
        result = select_books(records, repo, console)

    assert result == []
    # All should be marked SKIPPED
    for r in records:
        assert repo.get_by_url(r.detail_url).state == BookState.SKIPPED


def test_select_books_some_selected():
    repo, records = _make_repo_with_books(3)
    console = Console(file=open("/dev/null", "w"))

    with patch("oceanofpdf_downloader.selection.Prompt.ask", return_value="1,3"):
        result = select_books(records, repo, console)

    assert len(result) == 2
    assert result[0].title == "Book 1"
    assert result[1].title == "Book 3"
    assert all(r.state == BookState.SCHEDULED for r in result)
    # Verify DB state
    assert repo.get_by_url("https://example.com/1").state == BookState.SCHEDULED
    assert repo.get_by_url("https://example.com/2").state == BookState.SKIPPED
    assert repo.get_by_url("https://example.com/3").state == BookState.SCHEDULED


def test_select_books_all_selected():
    repo, records = _make_repo_with_books(2)
    console = Console(file=open("/dev/null", "w"))

    with patch("oceanofpdf_downloader.selection.Prompt.ask", return_value="all"):
        result = select_books(records, repo, console)

    assert len(result) == 2
    assert all(r.state == BookState.SCHEDULED for r in result)


def test_select_books_empty_list():
    repo = BookRepository(db_path=":memory:")
    console = Console(file=open("/dev/null", "w"))

    result = select_books([], repo, console)

    assert result == []
