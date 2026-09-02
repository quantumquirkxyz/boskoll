"""Textual TUI package for boskoll."""

from boskoll_cli.tui.app import (
    BORDER_THRESHOLD,
    CONTEXT_ID,
    CONTEXT_TITLE,
    EDITOR_ID,
    EDITOR_TITLE,
    HISTORY_ID,
    HISTORY_TITLE,
    MAX_PANEL_WEIGHT,
    MIN_PANEL_WEIGHT,
    BoskollApp,
    context_weight,
    editor_weight,
    history_weight,
)

__all__ = [
    "BoskollApp",
    "BORDER_THRESHOLD",
    "CONTEXT_ID",
    "CONTEXT_TITLE",
    "EDITOR_ID",
    "EDITOR_TITLE",
    "HISTORY_ID",
    "HISTORY_TITLE",
    "MAX_PANEL_WEIGHT",
    "MIN_PANEL_WEIGHT",
    "context_weight",
    "editor_weight",
    "history_weight",
]
