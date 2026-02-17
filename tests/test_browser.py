from unittest.mock import MagicMock, patch

from oceanofpdf_downloader.browser import BrowserSession
from oceanofpdf_downloader.config import Config


def _make_session():
    config = Config(max_pages=1)
    session = BrowserSession(config)
    return session


class TestIsCloudflareChallenge:
    def test_detects_just_a_moment_title(self):
        session = _make_session()
        page = MagicMock()
        page.title.return_value = "Just a moment..."
        page.locator.return_value.count.return_value = 0
        assert session._is_cloudflare_challenge(page) is True

    def test_detects_challenge_running_selector(self):
        session = _make_session()
        page = MagicMock()
        page.title.return_value = "Some Other Title"
        page.locator.return_value.count.return_value = 1
        assert session._is_cloudflare_challenge(page) is True

    def test_returns_false_for_normal_page(self):
        session = _make_session()
        page = MagicMock()
        page.title.return_value = "Ocean of PDF - Download Free Books"
        page.locator.return_value.count.return_value = 0
        assert session._is_cloudflare_challenge(page) is False


class TestWaitForCloudflare:
    def test_passes_through_when_no_challenge(self):
        session = _make_session()
        page = MagicMock()
        page.title.return_value = "Normal Page"
        page.locator.return_value.count.return_value = 0

        # _is_cloudflare_challenge returns False on first poll, so it should return immediately
        session._wait_for_cloudflare(page)

    def test_waits_until_challenge_clears(self):
        session = _make_session()
        page = MagicMock()

        # First two calls: challenge present; third call: cleared
        page.title.side_effect = ["Just a moment...", "Just a moment...", "Normal Page"]
        page.locator.return_value.count.return_value = 0

        with patch("oceanofpdf_downloader.browser.time.sleep"):
            session._wait_for_cloudflare(page)


class TestNavigate:
    def test_navigate_no_challenge(self):
        session = _make_session()
        page = MagicMock()
        page.title.return_value = "Normal Page"
        page.locator.return_value.count.return_value = 0

        session.navigate(page, "https://example.com")

        page.goto.assert_called_once_with("https://example.com", wait_until="domcontentloaded")

    def test_navigate_with_challenge(self):
        session = _make_session()
        page = MagicMock()

        # Challenge on first check (from navigate), then clears on poll
        page.title.side_effect = ["Just a moment...", "Normal Page"]
        page.locator.return_value.count.return_value = 0

        with patch("oceanofpdf_downloader.browser.time.sleep"):
            session.navigate(page, "https://example.com")

        page.goto.assert_called_once()
