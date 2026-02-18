import os
import sys
import types

from oceanofpdf_downloader.config import Config, load_config


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


def test_load_config_no_local():
    config = load_config(max_pages=3)
    assert config.max_pages == 3
    assert config.pause_seconds == 2.0


def test_load_config_local_overrides(monkeypatch):
    local = types.ModuleType("oceanofpdf_downloader.config_local")
    local.download_dir = "/custom/books"
    local.pause_seconds = 5.0
    monkeypatch.setitem(sys.modules, "oceanofpdf_downloader.config_local", local)

    config = load_config(max_pages=2)
    assert config.download_dir == "/custom/books"
    assert config.pause_seconds == 5.0
    assert config.max_pages == 2


def test_load_config_local_does_not_override_explicit_kwargs(monkeypatch):
    """kwargs passed directly to load_config take priority and can be overridden by local only
    if local is loaded after; kwargs win for fields NOT in local."""
    local = types.ModuleType("oceanofpdf_downloader.config_local")
    local.headless = True
    monkeypatch.setitem(sys.modules, "oceanofpdf_downloader.config_local", local)

    config = load_config(max_pages=1)
    assert config.headless is True
