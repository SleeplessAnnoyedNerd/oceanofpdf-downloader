import importlib
import os
from dataclasses import dataclass, field

from loguru import logger


@dataclass
class Config:
    max_pages: int
    start_page: int = 0
    pause_seconds: float = 2.0
    download_dir: str = field(default_factory=lambda: os.path.expanduser("~/Downloads"))
    base_url: str = "https://oceanofpdf.com/recently-added/"
    headless: bool = False
    download_timeout_ms: int = 45000
    await_download: bool = True
    download_wait_ms: int = 10000
    log_lines: int = 10
    profile_dir: str = field(default_factory=lambda: os.path.expanduser("~/.config/oceanofpdf-downloader/browser-profile/"))
    paginated: bool = True
    ml_autoselect: bool = False
    ml_confidence_threshold: float = 0.7
    ml_model_path: str = field(default_factory=lambda: os.path.expanduser(
        "~/.config/oceanofpdf-downloader/model.pkl"))
    ml_negative_examples_path: str = field(default_factory=lambda: os.path.expanduser(
        "~/.config/oceanofpdf-downloader/ml_negatives.txt"))


def load_config(**kwargs) -> Config:
    """Create Config with given kwargs, then apply any overrides from config_local.py if present."""
    config = Config(**kwargs)

    try:
        local = importlib.import_module("oceanofpdf_downloader.config_local")
        logger.info("Loaded local config overrides from config_local.py")
        for field_name in Config.__dataclass_fields__:
            if hasattr(local, field_name):
                setattr(config, field_name, getattr(local, field_name))
    except ModuleNotFoundError:
        pass

    return config
