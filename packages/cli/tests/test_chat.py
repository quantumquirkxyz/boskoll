"""Tests for interactive chat mode — TDD seam: chat loop and CLI routing."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any

import click
import click.testing
import pytest

from boskoll_cli import main
from boskoll_cli.commands.chat import _GREETER, run_chat
from boskoll_cli.models import ModelManager, ModelManagerError, OllamaAdapter
from boskoll_cli.models.ollama import OllamaError


@dataclass
class FakeResponse:
    status: int
    body: bytes
    headers: Mapping[str, str] = field(default_factory=dict)

    def read(self) -> bytes:
        return self.body

    def info(self) -> Mapping[str, str]:
        return self.headers

    def __iter__(self) -> Iterator[bytes]:
        yield from self.body.splitlines()


@dataclass
class FakeTransport:
    responses: dict[tuple[str, str], FakeResponse] = field(default_factory=dict)
    calls: list[tuple[str, str, Any]] = field(default_factory=list)

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
    ) -> FakeResponse:
        self.calls.append((method, path, body))
        return self.responses[(method, path)]


@dataclass
class RaisingTransport:
    error: Exception

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
    ) -> Any:  # pragma: no cover - never returns
        raise self.error


def _make_manager(transport: FakeTransport, response_text: str = "model reply") -> ModelManager:
    primary_transport = FakeTransport(
        responses={
            ("POST", "/api/generate"): FakeResponse(
                status=200,
                body=json.dumps({"response": response_text}).encode(),
            )
        }
    )
    return ModelManager(
        primary=OllamaAdapter(model="llama3.1", transport=primary_transport),
        fallback=OllamaAdapter(transport=transport),
    )


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


# ── Seam C: model manager integration ────────────────────────────────────────


class TestChatLoopWithModelManager:
    """run_chat uses the model manager to generate responses."""

    def test_generate_response_appended_after_prompt(self) -> None:
        manager = _make_manager(FakeTransport(), response_text="hello there")
        lines: list[str] = []
        prompts = iter(["hi", "exit"])
        run_chat(
            input_fn=lambda: next(prompts),
            output_fn=lines.append,
            model_manager=manager,
        )
        assert "boskoll> hi" in lines
        assert "hello there" in lines

    def test_no_model_manager_preserves_original_behavior(self) -> None:
        lines: list[str] = []
        prompts = iter(["hi", "exit"])
        run_chat(
            input_fn=lambda: next(prompts),
            output_fn=lines.append,
        )
        assert "boskoll> hi" in lines
        assert all("model" not in line.lower() for line in lines)

    def test_model_manager_failure_propagates(self) -> None:
        manager = ModelManager(
            primary=OllamaAdapter(
                model="llama3.1",
                transport=RaisingTransport(OllamaError("down")),
            ),
            fallback=OllamaAdapter(
                model="llama3.1",
                transport=RaisingTransport(OllamaError("fallback down")),
            ),
        )
        lines: list[str] = []
        prompts = iter(["hi", "exit"])
        with pytest.raises(ModelManagerError, match="Both providers failed generate"):
            run_chat(
                input_fn=lambda: next(prompts),
                output_fn=lines.append,
                model_manager=manager,
            )
