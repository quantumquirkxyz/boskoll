"""The boskoll Textual application and its three-panel layout.

The TUI is split into three core panels arranged side by side:

- ``history`` (left): the conversation history.
- ``editor`` (centre): the code editor, sized twice as wide as either side
  panel so it remains the visual focus.
- ``context`` (right): the agent and project context.

This module is the foundation that later TUI tickets (resizing, syntax
highlighting, theme, navigation) build on; it only composes the layout.
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Footer, Header, Static

HISTORY_ID = "history"
EDITOR_ID = "editor"
CONTEXT_ID = "context"

HISTORY_TITLE = "History"
EDITOR_TITLE = "Editor"
CONTEXT_TITLE = "Context"

_WEIGHT_HISTORY = 1
_WEIGHT_EDITOR = 2
_WEIGHT_CONTEXT = 1


class Panel(VerticalScroll):
    """A scrollable panel that fills one slot of the three-panel layout."""


class BoskollApp(App[None]):
    """Top-level Textual application for boskoll."""

    TITLE = "boskoll"
    SUB_TITLE = "AI code assistant"

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

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield Panel(Static(HISTORY_TITLE), id=HISTORY_ID)
            yield Panel(Static(EDITOR_TITLE), id=EDITOR_ID)
            yield Panel(Static(CONTEXT_TITLE), id=CONTEXT_ID)
        yield Footer()


def history_weight() -> int:
    """Return the width weight allocated to the history panel."""
    return _WEIGHT_HISTORY


def editor_weight() -> int:
    """Return the width weight allocated to the editor panel."""
    return _WEIGHT_EDITOR


def context_weight() -> int:
    """Return the width weight allocated to the context panel."""
    return _WEIGHT_CONTEXT
