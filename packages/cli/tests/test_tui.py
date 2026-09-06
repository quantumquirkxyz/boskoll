"""Tests for the boskoll Textual application and its three-panel layout.

These exercise the acceptance criteria of the TUI foundation ticket and
the panel resizing ticket: mouse drag resizing, keyboard shortcuts, and
minimum panel size enforcement.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from textual.app import App
from textual.containers import Horizontal
from textual.events import MouseDown, MouseMove, MouseUp, Key
from textual.widgets import Footer, Header, Input, Static

from boskoll_cli.settings import Theme
from boskoll_cli.tui import (
    CONTEXT_ID,
    CONTEXT_TITLE,
    EDITOR_ID,
    EDITOR_TITLE,
    HISTORY_ID,
    HISTORY_TITLE,
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


def test_dark_theme_is_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("BOSKOLL_CONFIG_PATH", str(tmp_path / "config.toml"))
    app = BoskollApp()
    assert app.boskoll_theme is Theme.DARK
    assert app.dark is True


def test_light_theme_can_be_selected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("BOSKOLL_CONFIG_PATH", str(tmp_path / "config.toml"))
    app = BoskollApp(theme=Theme.LIGHT)
    assert app.boskoll_theme is Theme.LIGHT
    assert app.dark is False


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
        editor_static = app.query_one(f"#{EDITOR_ID}").query_one(Static)
        # Editor panel now shows syntax-highlighted code instead of title
        editor_render = str(editor_static.render())
        assert "Syntax" in editor_render or "def" in editor_render
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


async def test_mouse_drag_resizes_panels() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()

        history = app.query_one(f"#{HISTORY_ID}")
        horizontal = app.query_one(Horizontal)

        border_x = history.region.right
        border_y = horizontal.region.y + 1

        app.on_mouse_down(MouseDown(None, border_x, border_y, 0, 0, 0, False, False, False))
        app.on_mouse_move(MouseMove(None, border_x + 10, border_y, 0, 0, 0, False, False, False))
        app.on_mouse_up(MouseUp(None, border_x + 10, border_y, 0, 0, 0, False, False, False))

        await pilot.pause()

        assert app._weights[HISTORY_ID] != history_weight()
        assert app._weights[EDITOR_ID] != editor_weight()
        assert sum(app._weights.values()) == 4


async def test_mouse_drag_is_incremental() -> None:
    app = BoskollApp()
    async with app.run_test(size=(160, 24)) as pilot:
        await pilot.pause()

        history = app.query_one(f"#{HISTORY_ID}")
        horizontal = app.query_one(Horizontal)

        border_x = history.region.right
        border_y = horizontal.region.y + 1

        app.on_mouse_down(MouseDown(None, border_x, border_y, 0, 0, 0, False, False, False))
        app.on_mouse_move(MouseMove(None, border_x + 40, border_y, 0, 0, 0, False, False, False))
        await pilot.pause()
        weight_after_forward = app._weights[HISTORY_ID]

        app.on_mouse_move(MouseMove(None, border_x, border_y, 0, 0, 0, False, False, False))
        await pilot.pause()
        weight_after_backward = app._weights[HISTORY_ID]

        app.on_mouse_up(MouseUp(None, border_x, border_y, 0, 0, 0, False, False, False))
        await pilot.pause()

        assert weight_after_backward < weight_after_forward


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
        horizontal = app.query_one(Horizontal)

        border_x = history.region.right
        border_y = horizontal.region.y + 1

        app.on_mouse_down(MouseDown(None, border_x, border_y, 0, 0, 0, False, False, False))
        app.on_mouse_move(MouseMove(None, 0, border_y, 0, 0, 0, False, False, False))
        app.on_mouse_up(MouseUp(None, 0, border_y, 0, 0, 0, False, False, False))

        await pilot.pause()

        assert app._weights[HISTORY_ID] >= MIN_PANEL_WEIGHT
        assert app._weights[EDITOR_ID] >= MIN_PANEL_WEIGHT
        assert app._weights[CONTEXT_ID] >= MIN_PANEL_WEIGHT
        assert all(w >= MIN_PANEL_WEIGHT for w in app._weights.values())


async def test_tab_navigation() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        assert app.focused is None or app.focused.id == HISTORY_ID
        await pilot.press("tab")
        await pilot.pause()
        assert app.focused.id == EDITOR_ID
        await pilot.press("tab")
        await pilot.pause()
        assert app.focused.id == CONTEXT_ID


async def test_shift_tab_navigation() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        assert app.focused is None or app.focused.id == HISTORY_ID
        await pilot.press("shift+tab")
        await pilot.pause()
        assert app.focused.id == CONTEXT_ID
        await pilot.press("shift+tab")
        await pilot.pause()
        assert app.focused.id == EDITOR_ID


async def test_arrow_key_navigation_within_panels() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)) as pilot:
        editor = app.query_one(f"#{EDITOR_ID}")
        editor.focus()
        await pilot.pause()

        await pilot.press("up")
        await pilot.pause()
        assert app.focused.id == EDITOR_ID

        await pilot.press("down")
        await pilot.pause()
        assert app.focused.id == EDITOR_ID

        await pilot.press("left")
        await pilot.pause()
        assert app.focused.id == EDITOR_ID

        await pilot.press("right")
        await pilot.pause()
        assert app.focused.id == EDITOR_ID


async def test_arrow_key_navigation_keeps_focus_in_same_panel() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)) as pilot:
        editor = app.query_one(f"#{EDITOR_ID}")
        editor.focus()
        await pilot.pause()

        for _ in range(5):
            await pilot.press("up", "down", "left", "right")
            await pilot.pause()

        assert app.focused.id == EDITOR_ID


async def test_enter_submits_input() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        input_widget = app.query_one(Input)
        assert input_widget is not None

        input_widget.focus()
        await pilot.press("a", "b", "c", "enter")
        await pilot.pause()
        assert input_widget.value == ""


async def test_enter_does_not_switch_focus_when_focused_on_input() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        input_widget = app.query_one(Input)
        input_widget.focus()
        await pilot.pause()

        initial_focused_id = app.focused.id

        await pilot.press("enter")
        await pilot.pause()

        assert app.focused.id == initial_focused_id
        assert isinstance(app.focused, Input)


async def test_enter_moves_focus_to_editor_panel_from_non_input_panel_child() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        history = app.query_one(f"#{HISTORY_ID}")
        history.focus()
        await pilot.pause()

        assert app.focused.id == HISTORY_ID

        await pilot.press("enter")
        await pilot.pause()

        assert app.focused.id == EDITOR_ID


async def test_enter_switches_to_editor_panel_when_focused_on_context_panel() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        context = app.query_one(f"#{CONTEXT_ID}")
        context.focus()
        await pilot.pause()

        assert app.focused.id == CONTEXT_ID

        await pilot.press("enter")
        await pilot.pause()

        assert app.focused.id == EDITOR_ID


async def test_arrow_keys_stop_propagation_within_panel() -> None:
    app = BoskollApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        editor = app.query_one(f"#{EDITOR_ID}")
        editor.focus()
        await pilot.pause()

        await pilot.press("down")
        await pilot.pause()
        assert app.focused.id == EDITOR_ID

        await pilot.press("up")
        await pilot.pause()
        assert app.focused.id == EDITOR_ID

        await pilot.press("right")
        await pilot.pause()
        assert app.focused.id == EDITOR_ID

        await pilot.press("left")
        await pilot.pause()
        assert app.focused.id == EDITOR_ID
