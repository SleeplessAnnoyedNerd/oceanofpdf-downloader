import os
from oceanofpdf_downloader.config import Config


def test_config_defaults():
    config = Config(max_pages=3)
    assert config.max_pages == 3
    assert config.pause_seconds == 2.0
    assert config.download_dir == os.path.expanduser("~/Downloads")
    assert config.base_url == "https://oceanofpdf.com/recently-added/"
    assert config.headless is False


def test_config_custom():
    config = Config(
        max_pages=5,
        pause_seconds=1.0,
        download_dir="/tmp/books",
        headless=True,
    )
    assert config.max_pages == 5
    assert config.pause_seconds == 1.0
    assert config.download_dir == "/tmp/books"
    assert config.headless is True
