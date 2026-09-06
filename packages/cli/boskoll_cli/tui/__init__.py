"""Textual TUI package for boskoll."""

from boskoll_cli.settings import Theme
from boskoll_cli.tui.app import (
    BORDER_THRESHOLD,
    CONTEXT_ID,
    CONTEXT_TITLE,
    EDITOR_ID,
    EDITOR_TITLE,
    HISTORY_ID,
    HISTORY_TITLE,
    MIN_PANEL_WEIGHT,
    BoskollApp,
    EditorContent,
    context_weight,
    editor_weight,
    history_weight,
)

__all__ = [
    "BORDER_THRESHOLD",
    "BoskollApp",
    "CONTEXT_ID",
    "CONTEXT_TITLE",
    "EDITOR_ID",
    "EDITOR_TITLE",
    "HISTORY_ID",
    "HISTORY_TITLE",
    "MIN_PANEL_WEIGHT",
    "EditorContent",
    "context_weight",
    "editor_weight",
    "history_weight",
    "Theme",
]
