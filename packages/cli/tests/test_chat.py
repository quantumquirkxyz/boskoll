"""Tests for interactive chat mode — TDD seam: chat loop and CLI routing."""

from __future__ import annotations

import click
import click.testing
import pytest

from boskoll_cli import main
from boskoll_cli.commands.chat import _GREETER, run_chat


@pytest.fixture
def runner() -> click.testing.CliRunner:
    return click.testing.CliRunner()


# ── Seam A: CLI routing ──────────────────────────────────────────────────────


class TestChatCLIRouting:
    """CLI routing — 'boskoll' (no args) and 'boskoll chat' launch chat mode."""

    def test_no_args_launches_chat(self, runner: click.testing.CliRunner) -> None:
        result = runner.invoke(main, [])
        assert result.exit_code == 0
        assert _GREETER in result.output

    def test_chat_subcommand_launches_chat(self, runner: click.testing.CliRunner) -> None:
        result = runner.invoke(main, ["chat"])
        assert result.exit_code == 0
        assert _GREETER in result.output

    def test_no_args_exit_status_is_zero(self, runner: click.testing.CliRunner) -> None:
        result = runner.invoke(main, [])
        assert result.exit_code == 0

    def test_chat_greeter_is_friendly_acknowledgement(
        self, runner: click.testing.CliRunner
    ) -> None:
        result = runner.invoke(main, ["chat"])
        assert _GREETER in result.output

    def test_live_chat_session_surfaces_history(
        self, runner: click.testing.CliRunner
    ) -> None:
        result = runner.invoke(main, ["chat"], input="hello boskoll\nworld\nexit\n")
        assert result.exit_code == 0
        assert _GREETER in result.output
        assert "Session history" in result.output
        assert "hello boskoll" in result.output
        assert "world" in result.output


# ── Seam B: chat loop function ────────────────────────────────────────────────


class TestChatLoop:
    """run_chat reads from input_fn, writes to output_fn, accumulates history."""

    def test_eof_returns_empty_history(self) -> None:
        lines: list[str] = []
        history = run_chat(
            input_fn=lambda: (_ for _ in ()).throw(EOFError),
            output_fn=lines.append,
        )
        assert history == []

    def test_exit_keyword_returns_history(self) -> None:
        lines: list[str] = []
        prompts = iter(["hello", "exit"])
        history = run_chat(
            input_fn=lambda: next(prompts),
            output_fn=lines.append,
        )
        assert len(history) == 1
        assert history[0] == "hello"

    def test_quit_keyword_returns_history(self) -> None:
        lines: list[str] = []
        prompts = iter(["ping", "quit"])
        history = run_chat(
            input_fn=lambda: next(prompts),
            output_fn=lines.append,
        )
        assert len(history) == 1
        assert history[0] == "ping"

    def test_response_contains_user_prompt(self) -> None:
        lines: list[str] = []
        prompts = iter(["what is boskoll?", "exit"])
        run_chat(
            input_fn=lambda: next(prompts),
            output_fn=lines.append,
        )
        response_lines = [line for line in lines if "what is boskoll?" in line]
        assert len(response_lines) == 1

    def test_multiple_prompts_accumulate_history(self) -> None:
        lines: list[str] = []
        prompts = iter(["first", "second", "third", "exit"])
        history = run_chat(
            input_fn=lambda: next(prompts),
            output_fn=lines.append,
        )
        assert history == ["first", "second", "third"]

    def test_history_returns_list_of_user_prompts(self) -> None:
        lines: list[str] = []
        prompts = iter(["alpha", "beta", "exit"])
        history = run_chat(
            input_fn=lambda: next(prompts),
            output_fn=lines.append,
        )
        assert isinstance(history, list)
        assert all(isinstance(h, str) for h in history)

    def test_empty_line_skipped_no_response(self) -> None:
        lines: list[str] = []
        prompts = iter(["", "", "exit"])
        history = run_chat(
            input_fn=lambda: next(prompts),
            output_fn=lines.append,
        )
        assert history == []

    def test_greeter_output_before_prompt(self) -> None:
        lines: list[str] = []
        prompts = iter(["exit"])
        run_chat(
            input_fn=lambda: next(prompts),
            output_fn=lines.append,
        )
        greeter_line = [line for line in lines if _GREETER in line]
        assert len(greeter_line) == 1
