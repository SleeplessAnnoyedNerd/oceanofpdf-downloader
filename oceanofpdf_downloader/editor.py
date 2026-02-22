from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Input, Label, ListItem, ListView

from oceanofpdf_downloader.models import BookRecord, BookState
from oceanofpdf_downloader.repository import BookRepository


COLUMNS = [
    ("id", "ID"),
    ("state", "State"),
    ("title", "Title"),
    ("genre", "Genre"),
]

EDITABLE_STATES = [s for s in BookState if s != BookState.BLACKLISTED]


class StateModal(ModalScreen):
    """Pop-up for selecting a new book state."""

    BINDINGS = [("escape", "dismiss_none", "Cancel")]

    DEFAULT_CSS = """
    StateModal {
        align: center middle;
    }
    StateModal > ListView {
        width: 40;
        height: auto;
        max-height: 20;
        border: tall $primary;
        background: $surface;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        with ListView():
            for state in EDITABLE_STATES:
                yield ListItem(Label(state.value), id=f"state-{state.value}")

    def action_dismiss_none(self) -> None:
        self.dismiss(None)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        state_value = event.item.id.removeprefix("state-")
        self.dismiss(BookState(state_value))


class SearchModal(ModalScreen):
    """Pop-up for entering a search query."""

    BINDINGS = [("escape", "dismiss_none", "Cancel")]

    DEFAULT_CSS = """
    SearchModal {
        align: center middle;
    }
    SearchModal > Label {
        width: 60;
        padding: 0 1;
    }
    SearchModal > Input {
        width: 60;
        border: tall $primary;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("Search title, language, genre (empty to reset):")
        yield Input(placeholder="…")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def action_dismiss_none(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)


class BookEditorApp(App):
    """TUI editor for the books database."""

    BINDINGS = [
        Binding("c", "change_state", "Change State"),
        Binding("f", "find", "Find"),
        Binding("q", "quit", "Quit"),
    ]

    DEFAULT_CSS = """
    #status-bar {
        height: 1;
        background: $panel;
        padding: 0 1;
        color: $text-muted;
    }
    """

    def __init__(self, repo: BookRepository) -> None:
        super().__init__()
        self.repo = repo
        self._current_query: str | None = None
        self._books: list[BookRecord] = []

    def compose(self) -> ComposeResult:
        yield DataTable(id="books-table", zebra_stripes=True)
        yield Label("", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        for key, label in COLUMNS:
            table.add_column(label, key=key)
        self._refresh_books()

    def _refresh_books(self) -> None:
        if self._current_query:
            self._books = self.repo.search_books(self._current_query)
        else:
            self._books = self.repo.get_all_books()

        table = self.query_one(DataTable)
        table.clear()
        for b in self._books:
            table.add_row(
                str(b.id),
                b.state.value,
                b.title[:40],
                b.genre,
            )

        status = self.query_one("#status-bar", Label)
        filter_info = f'  (filter: "{self._current_query}")' if self._current_query else ""
        status.update(f"{len(self._books)} entries{filter_info}")

    def _current_book(self) -> BookRecord | None:
        table = self.query_one(DataTable)
        row_idx = table.cursor_coordinate.row
        if row_idx < 0 or row_idx >= len(self._books):
            return None
        return self._books[row_idx]

    async def action_change_state(self) -> None:
        book = self._current_book()
        if book is None:
            return
        new_state = await self.push_screen_wait(StateModal())
        if new_state is not None:
            self.repo.update_state(book.id, new_state)
            self._refresh_books()

    async def action_find(self) -> None:
        query = await self.push_screen_wait(SearchModal())
        if query is None:  # Escape pressed
            return
        self._current_query = query.strip() or None
        self._refresh_books()


def run_editor(db_path: str | None = None) -> None:
    repo = BookRepository(db_path)
    app = BookEditorApp(repo)
    app.run()
