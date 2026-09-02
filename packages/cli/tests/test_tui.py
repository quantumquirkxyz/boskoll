"""Tests for the boskoll Textual application and its three-panel layout.

These exercise the acceptance criteria of the TUI foundation ticket and
the panel resizing ticket: mouse drag resizing, keyboard shortcuts, and
minimum panel size enforcement.
"""

from __future__ import annotations

import pytest
from textual.app import App
from textual.containers import Horizontal
from textual.widgets import Footer, Header, Static

from boskoll_cli.tui import (
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


async def test_panels_are_focusable() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)):
        history = app.query_one(f"#{HISTORY_ID}")
        history.focus()
        assert app.focused == history


class _FakeMouseEvent:
    def __init__(self, button: int, x: int, y: int) -> None:
        self.button = button
        self.x = x
        self.y = y

    def prevent_default(self) -> None:
        pass


async def test_mouse_drag_resizes_panels() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()

        history = app.query_one(f"#{HISTORY_ID}")
        editor = app.query_one(f"#{EDITOR_ID}")
        horizontal = app.query_one(Horizontal)

        border_x = history.region.right
        border_y = horizontal.region.y + 1

        app.on_mouse_down(_FakeMouseEvent(button=0, x=border_x, y=border_y))
        app.on_mouse_move(_FakeMouseEvent(button=0, x=border_x + 10, y=border_y))
        app.on_mouse_up(_FakeMouseEvent(button=0, x=border_x + 10, y=border_y))

        await pilot.pause()

        assert app._weights[HISTORY_ID] != history_weight()
        assert app._weights[EDITOR_ID] != editor_weight()
        assert sum(app._weights.values()) == 4


async def test_keyboard_decrease_weight() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()

        editor = app.query_one(f"#{EDITOR_ID}")
        editor.focus()
        await pilot.pause()

        initial_editor = app._weights[EDITOR_ID]
        initial_history = app._weights[HISTORY_ID]

        await pilot.press("ctrl+left")
        await pilot.pause()

        assert app._weights[EDITOR_ID] == initial_editor - 1
        assert app._weights[HISTORY_ID] == initial_history + 1


async def test_keyboard_increase_weight() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()

        history = app.query_one(f"#{HISTORY_ID}")
        history.focus()
        await pilot.pause()

        initial_editor = app._weights[EDITOR_ID]
        initial_history = app._weights[HISTORY_ID]

        await pilot.press("ctrl+right")
        await pilot.pause()

        assert app._weights[HISTORY_ID] == initial_history + 1
        assert app._weights[EDITOR_ID] == initial_editor - 1


async def test_minimum_panel_size_enforced_keyboard() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()

        history = app.query_one(f"#{HISTORY_ID}")
        history.focus()
        await pilot.pause()

        for _ in range(10):
            await pilot.press("ctrl+left")
            await pilot.pause()

        assert app._weights[HISTORY_ID] >= MIN_PANEL_WEIGHT
        assert app._weights[EDITOR_ID] >= MIN_PANEL_WEIGHT
        assert app._weights[CONTEXT_ID] >= MIN_PANEL_WEIGHT
        assert all(w >= MIN_PANEL_WEIGHT for w in app._weights.values())


async def test_minimum_panel_size_enforced_mouse() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()

        history = app.query_one(f"#{HISTORY_ID}")
        editor = app.query_one(f"#{EDITOR_ID}")
        horizontal = app.query_one(Horizontal)

        border_x = history.region.right
        border_y = horizontal.region.y + 1

        app.on_mouse_down(_FakeMouseEvent(button=0, x=border_x, y=border_y))
        app.on_mouse_move(_FakeMouseEvent(button=0, x=0, y=border_y))
        app.on_mouse_up(_FakeMouseEvent(button=0, x=0, y=border_y))

        await pilot.pause()

        assert app._weights[HISTORY_ID] >= MIN_PANEL_WEIGHT
        assert app._weights[EDITOR_ID] >= MIN_PANEL_WEIGHT
        assert app._weights[CONTEXT_ID] >= MIN_PANEL_WEIGHT
        assert all(w >= MIN_PANEL_WEIGHT for w in app._weights.values())
