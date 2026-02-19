import sys
from collections import deque

from rich.console import Console
from rich.markup import escape

from oceanofpdf_downloader.config import Config

_LEVEL_COLORS: dict[str, str] = {
    "TRACE": "dim",
    "DEBUG": "cyan",
    "INFO": "green",
    "SUCCESS": "bold green",
    "WARNING": "yellow",
    "ERROR": "bold red",
    "CRITICAL": "bold red",
}


class LiveDisplay:
    """Loguru sink with ring buffer: renders a progress line + recent log lines in-place."""

    def __init__(self, config: Config, console: Console) -> None:
        self._buffer: deque[str] = deque(maxlen=config.log_lines)
        self._console = console
        self._progress = ""
        self._last_line_count = 0
        self._enabled = False

    def enable(self) -> None:
        self._enabled = True
        self._render()

    def disable(self) -> None:
        self._erase()
        self._enabled = False

    def sink(self, message) -> None:
        """Loguru sink: append formatted record to ring buffer and re-render if active."""
        record = message.record
        level = record["level"].name
        color = _LEVEL_COLORS.get(level, "white")
        time_str = record["time"].strftime("%H:%M:%S")
        text = escape(str(record["message"]))
        line = f"[dim]{time_str}[/dim] [{color}]{level:<8}[/{color}] {text}"
        self._buffer.append(line)
        if self._enabled:
            self._render()

    def set_progress(self, text: str) -> None:
        self._progress = text
        if self._enabled:
            self._render()

    def _erase(self) -> None:
        if self._last_line_count > 0:
            sys.stdout.write(f"\033[{self._last_line_count}F\033[J")
            sys.stdout.flush()
            self._last_line_count = 0

    def _render(self) -> None:
        self._erase()
        lines: list[str] = []
        if self._progress:
            lines.append(self._progress)
            lines.append("")  # blank separator
        lines.extend(self._buffer)
        if not lines:
            return
        self._last_line_count = len(lines)
        for line in lines:
            self._console.print(line, highlight=False)
