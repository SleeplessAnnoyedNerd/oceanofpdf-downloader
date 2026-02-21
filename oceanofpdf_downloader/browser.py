import os
import platform
import subprocess
import time

from loguru import logger
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

from oceanofpdf_downloader.config import Config

CLOUDFLARE_TIMEOUT = 300  # 5 minutes
CLOUDFLARE_POLL_INTERVAL = 2  # seconds


class BrowserSession:
    """Shared browser session with persistent profile, stealth, and Cloudflare handling."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._playwright = None
        self._context = None
        self._stealth = Stealth()
        self._xvfb = None

    def __enter__(self):
        if platform.system() == "Linux" and "DISPLAY" not in os.environ:
            self._start_xvfb()

        self._playwright = sync_playwright().start()

        launch_args = [
            "--disable-blink-features=AutomationControlled",
        ]

        # Try real Chrome first, fall back to bundled Chromium
        try:
            self._context = self._playwright.chromium.launch_persistent_context(
                self.config.profile_dir,
                channel="chrome",
                headless=self.config.headless,
                args=launch_args,
                accept_downloads=True,
            )
            logger.info("Launched persistent Chrome browser")
        except Exception:
            logger.info("Chrome not available, falling back to Chromium")
            self._context = self._playwright.chromium.launch_persistent_context(
                self.config.profile_dir,
                headless=self.config.headless,
                args=launch_args,
                accept_downloads=True,
            )
            logger.info("Launched persistent Chromium browser")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._context:
            self._context.close()
        if self._playwright:
            self._playwright.stop()
        if self._xvfb:
            self._xvfb.terminate()
            self._xvfb.wait()
            logger.info("Stopped Xvfb")
        logger.info("Browser closed")
        return False

    def _start_xvfb(self) -> None:
        display = ":99"
        self._xvfb = subprocess.Popen(
            ["Xvfb", display, "-screen", "0", "1280x1024x24"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.5)  # give Xvfb time to initialise
        os.environ["DISPLAY"] = display
        logger.info("Started Xvfb virtual display on {}", display)

    def new_page(self):
        """Create a new page with stealth patches applied and download behavior set."""
        page = self._context.new_page()
        self._stealth.apply_stealth_sync(page)

        # Enable file downloads via CDP — required for headless Chromium
        cdp = self._context.new_cdp_session(page)
        cdp.send("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": self.config.download_dir,
        })

        return page

    def navigate(self, page, url: str) -> None:
        """Navigate to a URL, handling Cloudflare challenges if encountered."""
        page.goto(url, wait_until="domcontentloaded")
        if self._is_cloudflare_challenge(page):
            self._wait_for_cloudflare(page)

    def _is_cloudflare_challenge(self, page) -> bool:
        """Check if the current page is a Cloudflare challenge."""
        try:
            title = page.title()
            if "Just a moment" in title:
                return True
        except Exception:
            pass

        try:
            if page.locator("#challenge-running").count() > 0:
                return True
        except Exception:
            pass

        return False

    def _wait_for_cloudflare(self, page) -> None:
        """Wait for the user to solve the Cloudflare challenge."""
        logger.warning(
            "Cloudflare challenge detected — please solve it in the browser window. "
            "Waiting up to {} seconds...", CLOUDFLARE_TIMEOUT
        )
        deadline = time.time() + CLOUDFLARE_TIMEOUT
        while time.time() < deadline:
            time.sleep(CLOUDFLARE_POLL_INTERVAL)
            if not self._is_cloudflare_challenge(page):
                logger.info("Cloudflare challenge solved")
                return
        raise TimeoutError(
            f"Cloudflare challenge was not solved within {CLOUDFLARE_TIMEOUT} seconds"
        )
