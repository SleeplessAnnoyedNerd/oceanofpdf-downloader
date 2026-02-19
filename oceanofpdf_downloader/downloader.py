import os
import re
import time
from dataclasses import dataclass

from loguru import logger
from rich.console import Console
from rich.markup import escape

from oceanofpdf_downloader.browser import BrowserSession
from oceanofpdf_downloader.config import Config
from oceanofpdf_downloader.models import BookRecord, BookState
from oceanofpdf_downloader.repository import BookRepository
from oceanofpdf_downloader.utils import rename_file


@dataclass
class DownloadForm:
    server_id: str
    filename: str


def parse_download_forms(html: str) -> list[DownloadForm]:
    """Extract download forms targeting Fetching_Resource.php from detail page HTML."""
    forms: list[DownloadForm] = []

    form_pattern = re.compile(
        r'<form[^>]*action="[^"]*Fetching_Resource\.php"[^>]*>(.+?)</form>',
        re.DOTALL,
    )

    for form_match in form_pattern.finditer(html):
        form_body = form_match.group(1)

        id_match = re.search(
            r'<input[^>]*name="id"[^>]*value="([^"]*)"', form_body
        )
        filename_match = re.search(
            r'<input[^>]*name="filename"[^>]*value="([^"]*)"', form_body
        )

        if id_match and filename_match:
            forms.append(DownloadForm(
                server_id=id_match.group(1),
                filename=filename_match.group(1),
            ))

    return forms


class BookDownloader:
    """Downloads scheduled books using a shared BrowserSession."""

    def __init__(self, config: Config, repo: BookRepository, session: BrowserSession) -> None:
        self.config = config
        self.repo = repo
        self.session = session

    def download_book(self, record: BookRecord) -> bool:
        """Open a book's detail page, find download forms, and download all files.

        Returns True if at least one file was downloaded successfully.
        """
        page = self.session.new_page()
        try:
            logger.info("Opening detail page: {}", record.detail_url)
            self.session.navigate(page, record.detail_url)
            html = page.content()

            forms = parse_download_forms(html)
            if not forms:
                logger.warning("No download forms found for '{}'", record.title)
                return False

            logger.info("Found {} download form(s) for '{}'", len(forms), record.title)
            success_count = 0

            for form in forms:
                try:
                    final_name = rename_file(form.filename)
                    save_path = os.path.join(self.config.download_dir, final_name)

                    # Find the form's submit button and click it while expecting a download
                    # Use filename to locate the correct form (server_id can be shared across forms)
                    form_selector = f'form[action*="Fetching_Resource.php"] input[name="filename"][value="{form.filename}"]'
                    form_element = page.locator(form_selector).first
                    submit_button = form_element.locator("xpath=ancestor::form").locator(
                        'input[type="submit"], input[type="image"], button[type="submit"]'
                    )

                    if self.config.await_download:
                        with page.expect_download(timeout=self.config.download_timeout_ms) as download_info:
                            submit_button.click()
                        download = download_info.value
                        download.save_as(save_path)
                        logger.info("Downloaded: {}", save_path)
                    else:
                        submit_button.click()
                        logger.info("Clicked download for '{}', waiting {}ms (await_download disabled)",
                                    form.filename, self.config.download_wait_ms)
                        time.sleep(self.config.download_wait_ms / 1000)
                        logger.info("File should be in: {}", self.config.download_dir)
                    success_count += 1

                    time.sleep(self.config.pause_seconds)
                except Exception as e:
                    logger.error("Failed to download '{}': {}", form.filename, e)

            return success_count > 0
        except Exception as e:
            logger.error("Error processing '{}': {}", record.title, e)
            return False
        finally:
            page.close()

    def download_all(self, records: list[BookRecord], console: Console, live_display=None) -> int:
        """Download all scheduled books, updating state after each.

        Returns the number of successfully downloaded books.
        """
        if not live_display:
            console.print(f"\n[bold cyan]Downloading {len(records)} book(s)...[/bold cyan]")
            for record in records:
                console.print(f"  - {record.title}")

        for i, record in enumerate(records, 1):
            if live_display:
                live_display.set_progress(
                    f"[bold cyan]Downloading {i} / {len(records)}:[/bold cyan] {escape(record.title)}"
                )
            else:
                console.print(f"\n[bold][{i}/{len(records)}] {record.title}[/bold]")

            success = self.download_book(record)

            if success:
                self.repo.update_state(record.id, BookState.DONE)
                if live_display:
                    logger.info("Done: {}", record.title)
                else:
                    console.print(f"  [green]Done[/green]")
            else:
                self.repo.update_state(record.id, BookState.RETRY)
                if live_display:
                    logger.warning("Failed — marked for retry: {}", record.title)
                else:
                    console.print(f"  [red]Failed — marked for retry[/red]")

        return sum(1 for r in records if self.repo.get_by_url(r.detail_url).state == BookState.DONE)
