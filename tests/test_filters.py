from unittest.mock import patch

from oceanofpdf_downloader.filters import filter_books, is_blacklisted
from oceanofpdf_downloader.models import Book


def _book(title="Book A", genre="Fiction"):
    return Book(title=title, detail_url="http://example.com", language="English", genre=genre)


class TestIsBlacklisted:
    @patch("oceanofpdf_downloader.filters.TITLE_BLACKLIST", ["romance"])
    def test_matches_title(self):
        assert is_blacklisted(_book(title="Dark Romance Novel")) is True

    @patch("oceanofpdf_downloader.filters.GENRE_BLACKLIST", ["thriller"])
    def test_matches_genre(self):
        assert is_blacklisted(_book(genre="Mystery, Thriller")) is True

    @patch("oceanofpdf_downloader.filters.TITLE_BLACKLIST", ["ROMANCE"])
    def test_case_insensitive_title(self):
        assert is_blacklisted(_book(title="a romance story")) is True

    @patch("oceanofpdf_downloader.filters.GENRE_BLACKLIST", ["Thriller"])
    def test_case_insensitive_genre(self):
        assert is_blacklisted(_book(genre="thriller, mystery")) is True

    @patch("oceanofpdf_downloader.filters.TITLE_BLACKLIST", ["romance"])
    @patch("oceanofpdf_downloader.filters.GENRE_BLACKLIST", ["thriller"])
    def test_no_match(self):
        assert is_blacklisted(_book(title="Math Textbook", genre="Science")) is False

    def test_empty_blacklists(self):
        assert is_blacklisted(_book()) is False


class TestFilterBooks:
    @patch("oceanofpdf_downloader.filters.TITLE_BLACKLIST", ["romance"])
    def test_filters_out_blacklisted(self):
        books = [
            _book(title="Romance Novel"),
            _book(title="Math Textbook"),
        ]
        result = filter_books(books)
        assert len(result) == 1
        assert result[0].title == "Math Textbook"

    def test_empty_blacklists_passes_all(self):
        books = [_book(title="Book A"), _book(title="Book B")]
        result = filter_books(books)
        assert result == books

    def test_empty_list(self):
        assert filter_books([]) == []
