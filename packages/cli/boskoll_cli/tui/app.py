"""The boskoll Textual application and its three-panel layout.

The TUI is split into three core panels arranged side by side:

- ``history`` (left): the conversation history.
- ``editor`` (centre): the code editor, sized twice as wide as either side
  panel so it remains the visual focus.
- ``context`` (right): the agent and project context.

This module provides the foundation for panel resizing via mouse drag and
keyboard shortcuts, with a minimum panel size enforced.
"""

from __future__ import annotations

from enum import Enum

from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.events import MouseDown, MouseMove, MouseUp
from textual.widgets import Footer, Header, Static

from boskoll_cli.settings import Theme, load_theme

HISTORY_ID = "history"
EDITOR_ID = "editor"
CONTEXT_ID = "context"

HISTORY_TITLE = "History"
EDITOR_TITLE = "Editor"
CONTEXT_TITLE = "Context"

MIN_PANEL_WEIGHT = 1
BORDER_THRESHOLD = 3


class ResizeBorder(Enum):
    LEFT = 0
    RIGHT = 1

_WEIGHT_HISTORY = 1
_WEIGHT_EDITOR = 2
_WEIGHT_CONTEXT = 1

_SAMPLE_PYTHON = '''def hello_world():
    """Print a friendly greeting."""
    print("Hello, World!")
    return 42


if __name__ == "__main__":
    hello_world()
'''

_SAMPLE_JS = '''function helloWorld() {
    console.log("Hello, World!");
    return 42;
}


if (typeof module !== "undefined") {
    helloWorld();
}
'''


class Panel(VerticalScroll):
    """A scrollable panel that fills one slot of the three-panel layout."""
    can_focus = True


class BoskollApp(App[None]):
    """Top-level Textual application for boskoll."""

    TITLE = "boskoll"
    SUB_TITLE = "AI code assistant"

    BINDINGS = [
        ("ctrl+left", "decrease_weight", "Decrease panel width"),
        ("ctrl+right", "increase_weight", "Increase panel width"),
        ("ctrl+t", "toggle_theme", "Toggle theme"),
    ]

    CSS = """
    Horizontal {
        height: 1fr;
    }
    #history {
        width: 1fr;
    }
    #editor {
        width: 2fr;
    }
    #context {
        width: 1fr;
    }
    Panel {
        border: round $primary;
        padding: 0 1;
    }
    """

    _weights: dict[str, int]
    _dragging: bool = False
    _drag_border: ResizeBorder | None = None
    _last_drag_x: int = 0
    _boskoll_theme: Theme
    _editor_code: str = _SAMPLE_PYTHON
    _editor_language: str = "python"
    _mounted: bool = False

    _PANEL_NEIGHBORS: dict[str, tuple[str, str]] = {
        HISTORY_ID: (EDITOR_ID, EDITOR_ID),
        EDITOR_ID: (CONTEXT_ID, HISTORY_ID),
        CONTEXT_ID: (EDITOR_ID, EDITOR_ID),
    }

    def __init__(self, theme: Theme | str | None = None) -> None:
        super().__init__()
        self._boskoll_theme = Theme(theme) if theme is not None else load_theme()
        self.dark = self._boskoll_theme is Theme.DARK
        self._weights = {
            HISTORY_ID: _WEIGHT_HISTORY,
            EDITOR_ID: _WEIGHT_EDITOR,
            CONTEXT_ID: _WEIGHT_CONTEXT,
        }

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield Panel(Static(HISTORY_TITLE), id=HISTORY_ID)
            yield Panel(self._make_editor_content(), id=EDITOR_ID)
            yield Panel(Static(CONTEXT_TITLE), id=CONTEXT_ID)
        yield Footer()

    def _make_editor_content(self) -> Static:
        """Create the editor content with syntax highlighting."""
        return Static(
            self._syntax(self._editor_code, self._editor_language)
        )

    def set_editor_code(self, code: str, language: str = "python") -> None:
        """Replace the editor panel's content with ``code`` highlighted as ``language``.

        Parameters
        ----------
        code:
            The new source to render.
        language:
            A Pygments lexer name (``"python"``, ``"javascript"``, ``"typescript"``, ...).
            Defaults to ``"python"``.
        """
        self._editor_code = code
        self._editor_language = language
        editor = self.query_one(f"#{EDITOR_ID}")
        static = editor.query_one(Static)
        static.update(self._syntax(code, language))

    def _syntax(self, code: str, language: str) -> Syntax:
        return Syntax(
            code,
            language,
            theme="monokai" if self._boskoll_theme is Theme.DARK else "default",
            line_numbers=True,
            word_wrap=True,
        )

    @property
    def boskoll_theme(self) -> Theme:
        """Return the active TUI theme."""
        return self._boskoll_theme

    def set_theme(self, theme: Theme | str) -> None:
        """Apply a theme to the running TUI."""
        self._boskoll_theme = Theme(theme)
        self.dark = self._boskoll_theme is Theme.DARK
        if self._mounted:
            self.query_one(f"#{EDITOR_ID}").query_one(Static).update(
                self._syntax(self._editor_code, self._editor_language)
            )

    def action_toggle_theme(self) -> None:
        self.set_theme(Theme.LIGHT if self._boskoll_theme is Theme.DARK else Theme.DARK)

    def on_mount(self) -> None:
        self._mounted = True
        self.apply_weights()

    def apply_weights(self) -> None:
        total = sum(self._weights.values())
        history = self.query_one(f"#{HISTORY_ID}")
        editor = self.query_one(f"#{EDITOR_ID}")
        context = self.query_one(f"#{CONTEXT_ID}")

        history.styles.width = f"{self._weights[HISTORY_ID] / total * 100}%"
        editor.styles.width = f"{self._weights[EDITOR_ID] / total * 100}%"
        context.styles.width = f"{self._weights[CONTEXT_ID] / total * 100}%"

    def _get_resize_border(self, x: int, y: int) -> ResizeBorder | None:
        history = self.query_one(f"#{HISTORY_ID}")
        editor = self.query_one(f"#{EDITOR_ID}")
        horizontal = self.query_one(Horizontal)

        if not (horizontal.region.y <= y < horizontal.region.bottom):
            return None

        if abs(x - history.region.right) <= BORDER_THRESHOLD:
            return ResizeBorder.LEFT
        if abs(x - editor.region.right) <= BORDER_THRESHOLD:
            return ResizeBorder.RIGHT

        return None

    def on_mouse_down(self, event: MouseDown) -> None:
        if event.button != 0:
            return

        border = self._get_resize_border(event.x, event.y)
        if border is not None:
            self._dragging = True
            self._drag_border = border
            self._last_drag_x = event.x
            event.prevent_default()

    def on_mouse_move(self, event: MouseMove) -> None:
        if self._dragging and self._drag_border is not None:
            delta_x = event.x - self._last_drag_x
            self._last_drag_x = event.x
            self._apply_drag_delta(delta_x)
            event.prevent_default()

    def on_mouse_up(self, event: MouseUp) -> None:
        if self._dragging:
            self._dragging = False
            self._drag_border = None
            self._last_drag_x = 0

    def _apply_drag_delta(self, delta_x: int) -> None:
        if self._drag_border == ResizeBorder.LEFT:
            self._resize_pair(HISTORY_ID, EDITOR_ID, delta_x)
        elif self._drag_border == ResizeBorder.RIGHT:
            self._resize_pair(EDITOR_ID, CONTEXT_ID, delta_x)

    def _resize_pair(self, first_id: str, second_id: str, delta_x: int) -> None:
        first = self.query_one(f"#{first_id}")
        second = self.query_one(f"#{second_id}")

        total_active_width = first.region.width + second.region.width
        total_active_weight = self._weights[first_id] + self._weights[second_id]

        if total_active_width <= 0:
            return

        new_first_width = first.region.width + delta_x
        new_first_weight = round(
            new_first_width / total_active_width * total_active_weight
        )
        self._set_weight_pair(first_id, second_id, new_first_weight, total_active_weight)

    def _set_weight_pair(
        self,
        first_id: str,
        second_id: str,
        new_first_weight: int,
        total_weight: int,
    ) -> None:
        new_first_weight = max(
            MIN_PANEL_WEIGHT,
            min(new_first_weight, total_weight - MIN_PANEL_WEIGHT),
        )
        new_second_weight = total_weight - new_first_weight
        self._weights[first_id] = new_first_weight
        self._weights[second_id] = new_second_weight
        self.apply_weights()

    def _get_focused_panel_id(self) -> str | None:
        focused = self.focused
        if focused is None:
            return None
        if focused.id in (HISTORY_ID, EDITOR_ID, CONTEXT_ID):
            return focused.id
        for ancestor in focused.ancestors:
            if ancestor.id in (HISTORY_ID, EDITOR_ID, CONTEXT_ID):
                return ancestor.id
        return None

    def action_decrease_weight(self) -> None:
        panel_id = self._get_focused_panel_id()
        if panel_id is None:
            return

        _, decrease_target = self._PANEL_NEIGHBORS[panel_id]
        total = self._weights[panel_id] + self._weights[decrease_target]
        self._set_weight_pair(panel_id, decrease_target, self._weights[panel_id] - 1, total)

    def action_increase_weight(self) -> None:
        panel_id = self._get_focused_panel_id()
        if panel_id is None:
            return

        increase_source, _ = self._PANEL_NEIGHBORS[panel_id]
        total = self._weights[panel_id] + self._weights[increase_source]
        self._set_weight_pair(increase_source, panel_id, self._weights[increase_source] - 1, total)


def history_weight() -> int:
    """Return the width weight allocated to the history panel."""
    return _WEIGHT_HISTORY


def editor_weight() -> int:
    """Return the width weight allocated to the editor panel."""
    return _WEIGHT_EDITOR


def context_weight() -> int:
    """Return the width weight allocated to the context panel."""
    return _WEIGHT_CONTEXT
