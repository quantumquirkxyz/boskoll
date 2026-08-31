"""Textual TUI package for boskoll."""

from boskoll_cli.tui.app import (
    CONTEXT_ID,
    CONTEXT_TITLE,
    EDITOR_ID,
    EDITOR_TITLE,
    HISTORY_ID,
    HISTORY_TITLE,
    BoskollApp,
    context_weight,
    editor_weight,
    history_weight,
)

__all__ = [
    "BoskollApp",
    "CONTEXT_ID",
    "CONTEXT_TITLE",
    "EDITOR_ID",
    "EDITOR_TITLE",
    "HISTORY_ID",
    "HISTORY_TITLE",
    "context_weight",
    "editor_weight",
    "history_weight",
]
