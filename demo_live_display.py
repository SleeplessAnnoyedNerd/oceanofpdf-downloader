"""Quick demo of LiveDisplay: fake scraping then fake downloading.

Also tests long-line wrapping: one log entry per page is intentionally
wider than a typical terminal (120+ visible chars) to verify that the
cursor-up erase accounts for wrapped rows correctly.
"""
import time
from loguru import logger
from rich.console import Console

from oceanofpdf_downloader.config import Config
from oceanofpdf_downloader.live_display import LiveDisplay

config = Config(max_pages=5)
console = Console()
live = LiveDisplay(config, console)

logger.remove()
logger.add(live.sink, colorize=False)

BOOKS = ["The Art of War", "Dune", "Clean Code", "Thinking, Fast and Slow", "Sapiens"]

# A URL long enough to wrap on most terminals (120 visible chars)
LONG_URL = "https://oceanofpdf.com/authors/some-very-long-author-name/some-very-long-book-title-that-goes-on-and-on-pdf-epub/"

# --- Scraping phase ---
live.enable()
for i in range(1, config.max_pages + 1):
    live.set_progress(f"[bold cyan]Scraping page {i} / {config.max_pages}[/bold cyan]")
    logger.info("Navigating to page {}", i)
    time.sleep(0.4)
    logger.info("Found {} books on page {}", len(BOOKS), i)
    time.sleep(0.3)
    # Long line — should wrap and still erase cleanly
    logger.debug("Detail URL: {}", LONG_URL)
    time.sleep(0.5)

logger.info("Scraping complete. Total books: {}", config.max_pages * len(BOOKS))
time.sleep(0.5)
live.disable()

# --- Intermediate phase (no live display) ---
console.print("\n[bold]Processing results...[/bold]")
time.sleep(0.8)
console.print("  3 book(s) blacklisted by filter")
console.print("  2 book(s) auto-scheduled\n")
time.sleep(0.5)

# --- Downloading phase ---
live.enable()
for i, title in enumerate(BOOKS, 1):
    live.set_progress(f"[bold cyan]Downloading {i} / {len(BOOKS)}:[/bold cyan] {title}")
    logger.info("Opening detail page for '{}'", title)
    time.sleep(0.3)
    logger.info("Found 2 download form(s)")
    time.sleep(0.4)
    logger.info("Downloaded: ~/Downloads/{}.pdf", title.replace(" ", "_"))
    time.sleep(0.3)
    logger.info("Downloaded: ~/Downloads/{}.epub", title.replace(" ", "_"))
    time.sleep(0.4)
    logger.info("Done: {}", title)
    time.sleep(0.3)

live.disable()
console.print(f"\n[bold]Download complete: {len(BOOKS)}/{len(BOOKS)} succeeded[/bold]")
