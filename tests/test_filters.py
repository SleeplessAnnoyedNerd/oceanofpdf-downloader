from unittest.mock import patch

from oceanofpdf_downloader.filters import filter_books, is_autoselected, is_blacklisted
from oceanofpdf_downloader.models import Book


def _book(title="Book A", genre="Fiction"):
    return Book(title=title, detail_url="http://example.com", language="English", genre=genre)


class TestIsBlacklisted:
    @patch("oceanofpdf_downloader.filters._title_blacklist", ["romance"])
    def test_matches_title(self):
        assert is_blacklisted(_book(title="Dark Romance Novel")) is True

    @patch("oceanofpdf_downloader.filters._genre_blacklist", ["thriller"])
    def test_matches_genre(self):
        assert is_blacklisted(_book(genre="Mystery, Thriller")) is True

    @patch("oceanofpdf_downloader.filters._title_blacklist", ["ROMANCE"])
    def test_case_insensitive_title(self):
        assert is_blacklisted(_book(title="a romance story")) is True

    @patch("oceanofpdf_downloader.filters._genre_blacklist", ["Thriller"])
    def test_case_insensitive_genre(self):
        assert is_blacklisted(_book(genre="thriller, mystery")) is True

    @patch("oceanofpdf_downloader.filters._title_blacklist", ["romance"])
    @patch("oceanofpdf_downloader.filters._genre_blacklist", ["thriller"])
    def test_no_match(self):
        assert is_blacklisted(_book(title="Math Textbook", genre="Science")) is False

    def test_empty_blacklists(self):
        assert is_blacklisted(_book()) is False


class TestFilterBooks:
    @patch("oceanofpdf_downloader.filters._title_blacklist", ["romance"])
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


class TestIsAutoselected:
    @patch("oceanofpdf_downloader.filters._title_autoselect", ["algebra"])
    def test_matches_title(self):
        assert is_autoselected(_book(title="College Algebra")) is True

    @patch("oceanofpdf_downloader.filters._genre_autoselect", ["textbooks"])
    def test_matches_genre(self):
        assert is_autoselected(_book(genre="Mathematics, Textbooks")) is True

    @patch("oceanofpdf_downloader.filters._genre_autoselect", ["TEXTBOOKS"])
    def test_case_insensitive(self):
        assert is_autoselected(_book(genre="textbooks, math")) is True

    @patch("oceanofpdf_downloader.filters._title_autoselect", ["algebra"])
    @patch("oceanofpdf_downloader.filters._genre_autoselect", ["textbooks"])
    def test_no_match(self):
        assert is_autoselected(_book(title="Romance Novel", genre="Fiction")) is False

    def test_empty_autoselect(self):
        assert is_autoselected(_book()) is False
