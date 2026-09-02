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

from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.events import MouseDown, MouseMove, MouseUp
from textual.widgets import Footer, Header, Static

HISTORY_ID = "history"
EDITOR_ID = "editor"
CONTEXT_ID = "context"

HISTORY_TITLE = "History"
EDITOR_TITLE = "Editor"
CONTEXT_TITLE = "Context"

MIN_PANEL_WEIGHT = 1
MAX_PANEL_WEIGHT = 10
BORDER_THRESHOLD = 3

_WEIGHT_HISTORY = 1
_WEIGHT_EDITOR = 2
_WEIGHT_CONTEXT = 1


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
    _drag_border: int | None = None
    _drag_start_x: int = 0
    _drag_start_weights: dict[str, int] | None = None

    def __init__(self) -> None:
        super().__init__()
        self._weights = {
            HISTORY_ID: _WEIGHT_HISTORY,
            EDITOR_ID: _WEIGHT_EDITOR,
            CONTEXT_ID: _WEIGHT_CONTEXT,
        }

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield Panel(Static(HISTORY_TITLE), id=HISTORY_ID)
            yield Panel(Static(EDITOR_TITLE), id=EDITOR_ID)
            yield Panel(Static(CONTEXT_TITLE), id=CONTEXT_ID)
        yield Footer()

    def on_mount(self) -> None:
        self.apply_weights()

    def apply_weights(self) -> None:
        total = sum(self._weights.values())
        history = self.query_one(f"#{HISTORY_ID}")
        editor = self.query_one(f"#{EDITOR_ID}")
        context = self.query_one(f"#{CONTEXT_ID}")

        history.styles.width = f"{self._weights[HISTORY_ID] / total * 100}%"
        editor.styles.width = f"{self._weights[EDITOR_ID] / total * 100}%"
        context.styles.width = f"{self._weights[CONTEXT_ID] / total * 100}%"

    def _get_resize_border(self, x: int, y: int) -> int | None:
        history = self.query_one(f"#{HISTORY_ID}")
        editor = self.query_one(f"#{EDITOR_ID}")
        horizontal = self.query_one(Horizontal)

        if horizontal is None:
            return None

        if not (horizontal.region.y <= y < horizontal.region.bottom):
            return None

        if abs(x - history.region.right) <= BORDER_THRESHOLD:
            return 0
        if abs(x - editor.region.right) <= BORDER_THRESHOLD:
            return 1

        return None

    def on_mouse_down(self, event: MouseDown) -> None:
        if event.button != 0:
            return

        border = self._get_resize_border(event.x, event.y)
        if border is not None:
            self._dragging = True
            self._drag_border = border
            self._drag_start_x = event.x
            self._drag_start_weights = self._weights.copy()
            event.prevent_default()

    def on_mouse_move(self, event: MouseMove) -> None:
        if self._dragging and self._drag_border is not None:
            delta_x = event.x - self._drag_start_x
            self._apply_drag_delta(delta_x)
            event.prevent_default()

    def on_mouse_up(self, event: MouseUp) -> None:
        if self._dragging:
            self._dragging = False
            self._drag_border = None
            self._drag_start_weights = None

    def _apply_drag_delta(self, delta_x: int) -> None:
        history = self.query_one(f"#{HISTORY_ID}")
        editor = self.query_one(f"#{EDITOR_ID}")
        context = self.query_one(f"#{CONTEXT_ID}")

        if self._drag_border == 0:
            initial_history_width = history.region.width
            initial_editor_width = editor.region.width
            total_active_width = initial_history_width + initial_editor_width
            total_active_weight = (
                self._weights[HISTORY_ID] + self._weights[EDITOR_ID]
            )

            if total_active_width <= 0:
                return

            new_history_width = initial_history_width + delta_x
            new_history_weight = round(
                new_history_width / total_active_width * total_active_weight
            )
            new_history_weight = max(
                MIN_PANEL_WEIGHT,
                min(new_history_weight, total_active_weight - MIN_PANEL_WEIGHT),
            )
            new_editor_weight = total_active_weight - new_history_weight

            self._weights[HISTORY_ID] = new_history_weight
            self._weights[EDITOR_ID] = new_editor_weight

        elif self._drag_border == 1:
            initial_editor_width = editor.region.width
            initial_context_width = context.region.width
            total_active_width = initial_editor_width + initial_context_width
            total_active_weight = (
                self._weights[EDITOR_ID] + self._weights[CONTEXT_ID]
            )

            if total_active_width <= 0:
                return

            new_editor_width = initial_editor_width + delta_x
            new_editor_weight = round(
                new_editor_width / total_active_width * total_active_weight
            )
            new_editor_weight = max(
                MIN_PANEL_WEIGHT,
                min(new_editor_weight, total_active_weight - MIN_PANEL_WEIGHT),
            )
            new_context_weight = total_active_weight - new_editor_weight

            self._weights[EDITOR_ID] = new_editor_weight
            self._weights[CONTEXT_ID] = new_context_weight

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

        weights = self._weights.copy()
        idx = (HISTORY_ID, EDITOR_ID, CONTEXT_ID).index(panel_id)

        if idx == 0:
            neighbor = EDITOR_ID
        elif idx == 1:
            neighbor = HISTORY_ID
        else:
            neighbor = EDITOR_ID

        if (
            weights[panel_id] > MIN_PANEL_WEIGHT
            and weights[neighbor] < MAX_PANEL_WEIGHT
        ):
            weights[panel_id] -= 1
            weights[neighbor] += 1
            self._weights = weights
            self.apply_weights()

    def action_increase_weight(self) -> None:
        panel_id = self._get_focused_panel_id()
        if panel_id is None:
            return

        weights = self._weights.copy()
        idx = (HISTORY_ID, EDITOR_ID, CONTEXT_ID).index(panel_id)

        if idx == 0:
            neighbor = EDITOR_ID
        elif idx == 1:
            neighbor = CONTEXT_ID
        else:
            neighbor = EDITOR_ID

        if (
            weights[neighbor] > MIN_PANEL_WEIGHT
            and weights[panel_id] < MAX_PANEL_WEIGHT
        ):
            weights[panel_id] += 1
            weights[neighbor] -= 1
            self._weights = weights
            self.apply_weights()


def history_weight() -> int:
    """Return the width weight allocated to the history panel."""
    return _WEIGHT_HISTORY


def editor_weight() -> int:
    """Return the width weight allocated to the editor panel."""
    return _WEIGHT_EDITOR


def context_weight() -> int:
    """Return the width weight allocated to the context panel."""
    return _WEIGHT_CONTEXT
