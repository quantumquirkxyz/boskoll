"""Tests for the boskoll Textual application and its three-panel layout.

These exercise the acceptance criteria of the TUI foundation ticket: a
Textual app class exists, the three panels (history | editor | context) are
rendered, and they are laid out with the correct proportions.
"""

from __future__ import annotations

import pytest
from textual.app import App
from textual.widgets import Footer, Header, Static

from boskoll_cli.tui import (
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

PANEL_IDS = (HISTORY_ID, EDITOR_ID, CONTEXT_ID)


@pytest.mark.parametrize(
    ("weight_fn", "expected"),
    [
        (history_weight, 1),
        (editor_weight, 2),
        (context_weight, 1),
    ],
)
def test_panel_weight_helpers(weight_fn: object, expected: int) -> None:
    panel_weight = weight_fn
    assert callable(panel_weight)
    assert panel_weight() == expected


def test_boskoll_app_is_textual_app() -> None:
    assert issubclass(BoskollApp, App)


def test_layout_titles_defined() -> None:
    assert HISTORY_TITLE == "History"
    assert EDITOR_TITLE == "Editor"
    assert CONTEXT_TITLE == "Context"


async def test_three_panels_rendered() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)):
        for panel_id in PANEL_IDS:
            panel = app.query_one(f"#{panel_id}")
            assert panel.id == panel_id


async def test_each_panel_has_a_title_label() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)):
        assert str(app.query_one(f"#{HISTORY_ID}").query_one(Static).render()) == HISTORY_TITLE
        assert str(app.query_one(f"#{EDITOR_ID}").query_one(Static).render()) == EDITOR_TITLE
        assert str(app.query_one(f"#{CONTEXT_ID}").query_one(Static).render()) == CONTEXT_TITLE


async def test_panels_have_correct_proportions() -> None:
    app = BoskollApp()
    size = (80, 24)
    async with app.run_test(size=size):
        history = app.query_one(f"#{HISTORY_ID}").region
        editor = app.query_one(f"#{EDITOR_ID}").region
        context = app.query_one(f"#{CONTEXT_ID}").region

    assert history.width * 2 == editor.width
    assert context.width * 2 == editor.width
    assert history.width == context.width
    assert history.height == editor.height == context.height


async def test_panels_are_arranged_left_to_right() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)):
        history = app.query_one(f"#{HISTORY_ID}").region
        editor = app.query_one(f"#{EDITOR_ID}").region
        context = app.query_one(f"#{CONTEXT_ID}").region

    assert history.x == 0
    assert history.right == editor.x
    assert editor.right == context.x
    assert context.x + context.width == 80


async def test_app_composes_header_and_footer() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)):
        assert app.query_one(Header) is not None
        assert app.query_one(Footer) is not None
