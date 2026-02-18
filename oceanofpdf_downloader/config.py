import os
from dataclasses import dataclass, field


@dataclass
class Config:
    max_pages: int
    pause_seconds: float = 2.0
    download_dir: str = field(default_factory=lambda: os.path.expanduser("~/Downloads"))
    base_url: str = "https://oceanofpdf.com/recently-added/"
    headless: bool = False
    download_timeout_ms: int = 45000
    profile_dir: str = field(default_factory=lambda: os.path.expanduser("~/.config/oceanofpdf-downloader/browser-profile/"))
