import time

import pytest

from oceanofpdf_downloader.models import Book, BookState
from oceanofpdf_downloader.repository import BookRepository


def make_repo() -> BookRepository:
    return BookRepository(":memory:")


def insert(repo: BookRepository, title: str, language: str = "English", genre: str = "Fiction") -> int:
    book = Book(title=title, detail_url=f"https://example.com/{title}", language=language, genre=genre)
    record = repo.insert_book(book)
    assert record is not None
    return record.id


# --- get_all_books ---

def test_get_all_books_empty():
    repo = make_repo()
    assert repo.get_all_books() == []


def test_get_all_books_returns_inserted():
    repo = make_repo()
    insert(repo, "Book A")
    insert(repo, "Book B")
    books = repo.get_all_books()
    assert len(books) == 2


def test_get_all_books_excludes_blacklisted():
    repo = make_repo()
    bid = insert(repo, "Blacklisted Book")
    insert(repo, "Normal Book")
    repo.update_state(bid, BookState.BLACKLISTED)
    books = repo.get_all_books()
    assert len(books) == 1
    assert books[0].title == "Normal Book"


def test_get_all_books_sorted_desc():
    repo = make_repo()
    a_id = insert(repo, "Book A")
    b_id = insert(repo, "Book B")
    # Force Book A to have a later updated_at by updating its state
    time.sleep(0.01)
    repo.update_state(a_id, BookState.SCHEDULED)
    books = repo.get_all_books()
    assert books[0].id == a_id
    assert books[1].id == b_id


def test_get_all_books_all_states_except_blacklisted():
    repo = make_repo()
    ids = {}
    for state in BookState:
        bid = insert(repo, f"Book {state.value}")
        if state != BookState.NEW:
            repo.update_state(bid, state)
        ids[state] = bid
    books = repo.get_all_books()
    returned_ids = {b.id for b in books}
    assert ids[BookState.BLACKLISTED] not in returned_ids
    for state in BookState:
        if state != BookState.BLACKLISTED:
            assert ids[state] in returned_ids


# --- search_books ---

def test_search_books_matches_title():
    repo = make_repo()
    insert(repo, "Python Programming")
    insert(repo, "Java Basics")
    results = repo.search_books("Python")
    assert len(results) == 1
    assert results[0].title == "Python Programming"


def test_search_books_matches_language():
    repo = make_repo()
    insert(repo, "Book A", language="German")
    insert(repo, "Book B", language="English")
    results = repo.search_books("German")
    assert len(results) == 1
    assert results[0].title == "Book A"


def test_search_books_matches_genre():
    repo = make_repo()
    insert(repo, "Book A", genre="Science Fiction")
    insert(repo, "Book B", genre="Romance")
    results = repo.search_books("Science")
    assert len(results) == 1
    assert results[0].title == "Book A"


def test_search_books_no_match():
    repo = make_repo()
    insert(repo, "Python Programming")
    results = repo.search_books("Haskell")
    assert results == []


def test_search_books_excludes_blacklisted():
    repo = make_repo()
    bid = insert(repo, "Python Blacklisted")
    insert(repo, "Python Normal")
    repo.update_state(bid, BookState.BLACKLISTED)
    results = repo.search_books("Python")
    assert len(results) == 1
    assert results[0].title == "Python Normal"


def test_search_books_case_insensitive():
    repo = make_repo()
    insert(repo, "Python Programming")
    results = repo.search_books("python")
    assert len(results) == 1


def test_search_books_partial_match():
    repo = make_repo()
    insert(repo, "Advanced Python Programming")
    results = repo.search_books("Pytho")
    assert len(results) == 1
