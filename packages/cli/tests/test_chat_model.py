"""Tests for wiring ``boskoll chat --model`` to the model manager.

Covers ticket #46 (force a model with --model), ticket #47 (streaming
responses), and ticket #48 (session usage reporting) at the CLI seam.
"""

from __future__ import annotations

from collections.abc import Iterator

import click.testing
import pytest

from boskoll_cli.commands.chat import build_command
from boskoll_cli.models import (
    ModelAdapter,
    ModelConnectionError,
    ModelInfo,
    ModelManager,
    ModelResponse,
)


class FakeAdapter(ModelAdapter):
    provider = "fake"

    def list_models(self) -> list[ModelInfo]:
        return [ModelInfo(id="fake-model", provider="fake")]

    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse:
        return ModelResponse(
            text=f"generated: {prompt}",
            model=model or "fake-model",
            prompt_tokens=4,
            completion_tokens=8,
        )

    def stream(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        yield "streamed: "
        yield prompt


class FailingAdapter(FakeAdapter):
    def stream(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        raise ModelConnectionError("Ollama is not running")


@pytest.fixture
def runner() -> click.testing.CliRunner:
    return click.testing.CliRunner()


def invoke_with_model(
    runner: click.testing.CliRunner, manager: ModelManager, args: list[str], input_text: str
) -> click.testing.Result:
    command = build_command(manager=manager)
    # stderr is mixed into ``output`` on this Click version.
    return runner.invoke(command, args, input=input_text)


def test_chat_with_model_streams_response(
    runner: click.testing.CliRunner,
) -> None:
    manager = ModelManager(local_adapter=FakeAdapter())
    result = invoke_with_model(
        runner,
        manager,
        ["--model", "ollama/fake-model"],
        input_text="hello\nexit\n",
    )
    assert result.exit_code == 0
    assert "Using model: ollama/fake-model" in result.output
    assert "streamed:" in result.output
    assert "hello" in result.output  # streamed chunk and session history


def test_chat_reports_session_usage(
    runner: click.testing.CliRunner,
) -> None:
    manager = ModelManager(local_adapter=FakeAdapter())
    result = invoke_with_model(
        runner,
        manager,
        ["--model", "ollama/fake-model"],
        input_text="hello\nexit\n",
    )
    assert "Usage: 1 request(s)" in result.output
    assert manager.usage.requests == 1


def test_chat_without_model_never_touches_manager(
    runner: click.testing.CliRunner,
) -> None:
    manager = ModelManager(local_adapter=FakeAdapter())
    result = runner.invoke(build_command(manager=manager), [], input="hi\nexit\n")
    assert result.exit_code == 0
    assert "Welcome to boskoll chat" in result.output
    assert manager.usage.requests == 0
    assert "streamed:" not in result.output


def test_chat_model_error_is_clear_and_exits_nonzero(
    runner: click.testing.CliRunner,
) -> None:
    manager = ModelManager(local_adapter=FailingAdapter())
    result = invoke_with_model(
        runner,
        manager,
        ["--model", "ollama/fake-model"],
        input_text="hello\nexit\n",
    )
    assert result.exit_code == 1
    assert "Error:" in result.output
    assert "Ollama is not running" in result.output


def test_chat_empty_session_with_model_makes_no_requests(
    runner: click.testing.CliRunner,
) -> None:
    """Invoking with --model but sending no prompts must not hit the model."""
    manager = ModelManager(local_adapter=FailingAdapter())
    result = runner.invoke(
        build_command(manager=manager),
        ["--model", "ollama/fake-model"],
        input="",
    )
    assert result.exit_code == 0
    assert manager.usage.requests == 0
