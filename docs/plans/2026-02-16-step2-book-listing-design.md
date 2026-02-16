# Step 2 Design: Book Listing Prototype

## Goal

Implement a prototype that scrapes oceanofpdf.com/recently-added/ and lists all books with title, detail page URL, language, and genre — up to a user-specified number of pages.

## Project Structure

```
oceanofpdf_downloader/
    __init__.py
    __main__.py          # Entry point: python -m oceanofpdf_downloader
    config.py            # Configuration (max pages, pause, download dir)
    models.py            # Book dataclass
    scraper.py           # BookScraper class wrapping Playwright
    display.py           # Rich table output
    filters.py           # Filter stub (passes everything through)
    utils.py             # rename_file() stub and helpers
tests/
    __init__.py
    test_models.py
    test_scraper.py      # Tests with mocked HTML
    test_filters.py
    test_utils.py
requirements.txt
```

## Components

### models.py

`Book` dataclass with fields: `title: str`, `detail_url: str`, `language: str`, `genre: str`.

### config.py

`Config` dataclass:
- `max_pages: int` — how many listing pages to scrape
- `pause_seconds: float` — delay between requests (default 2.0)
- `download_dir: str` — where to save files (default `~/Downloads`)
- `base_url: str` — `https://oceanofpdf.com/recently-added/`

### scraper.py

`BookScraper` class:
- Takes a `Config` instance
- Manages Playwright browser lifecycle (headed Chromium)
- `scrape_listing_page(page_num: int) -> list[Book]` — navigates to page, parses entries
- `scrape_all_pages() -> list[Book]` — iterates 1..max_pages with pause, logs progress
- Context manager (`__enter__`/`__exit__`) for browser cleanup

### display.py

`display_books(books: list[Book])` — renders a rich Table with columns: #, Title, Language, Genre, URL.

### filters.py

`filter_books(books: list[Book]) -> list[Book]` — stub, returns input unchanged.

### utils.py

`rename_file(filename: str) -> str` — stub, returns input unchanged.

### __main__.py

Entry point flow:
1. Ask user for max pages via input prompt
2. Create Config
3. Scrape all pages with BookScraper
4. Apply filter_books() stub
5. Display results with display_books()

## Parsing Strategy

Each book on the listing page lives in a `<header class="entry-header">`. Extract:
- **Title & URL**: from `a.entry-title-link` (href attribute and inner text)
- **Language & Genre**: from `<strong>Language: </strong>` and `<strong>Genre: </strong>` tags located near each entry's parent container

## Technology

- **Playwright** (Python, headed Chromium) for browser automation
- **rich** for table display
- **loguru** for logging
- **pytest** for testing

## Testing

Tests use mocked HTML fixtures — no real network calls:
- `test_scraper.py` — test parsing logic with sample HTML from the spec
- `test_filters.py` — verify stub passes books through
- `test_utils.py` — verify rename stub returns original name

## Design Decisions

- Visible browser (not headless) so user can see what's happening
- 2-second default pause between page requests
- Sequential scraping only
- Server-provided filenames with rename_file() stub for future logic
