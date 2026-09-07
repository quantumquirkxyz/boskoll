"""The ``chat`` subcommand — interactive chat session."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator

import click

from boskoll_cli.commands._help import command
from boskoll_cli.models import (
    ModelAdapter,
    ModelManager,
    OllamaAdapter,
    OpenRouterAdapter,
    OpenRouterError,
)

COMMAND_NAME = "chat"
_GREETER = "Welcome to boskoll chat"
_PROMPT = "boskoll> "
_EXIT_KEYWORDS = frozenset({"exit", "quit"})


class _MissingOpenRouterAdapter(ModelAdapter):
    """Fallback that raises when no OpenRouter API key is configured."""

    def list_models(self) -> list[str]:
        raise OpenRouterError("OpenRouter API key is required")

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        raise OpenRouterError("OpenRouter API key is required")

    def stream(self, prompt: str, *, system: str | None = None) -> Iterator[str]:
        raise OpenRouterError("OpenRouter API key is required")
        yield  # pragma: no cover


def _build_model_manager(model: str | None) -> ModelManager | None:
    """Create a ModelManager from the ``--model`` flag value.

    Parsing rules:

    * ``None`` — return ``None`` (no model forced).
    * ``<name>`` — use a ModelManager with Ollama primary + OpenRouter fallback,
      both configured with ``<name>``.
    """
    if model is None:
        return None

    model = model.strip()
    if not model:
        return None

    primary = OllamaAdapter(model=model)
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if api_key:
        fallback: ModelAdapter = OpenRouterAdapter(api_key=api_key)
    else:
        fallback = _MissingOpenRouterAdapter()

    return ModelManager(primary=primary, fallback=fallback)


def run_chat(
    input_fn: Callable[[], str],
    output_fn: Callable[[str], None],
    model_manager: ModelManager | None = None,
) -> list[str]:
    """Run the interactive chat loop and return the session history.

    Parameters
    ----------
    input_fn:
        Called to read a line from the user. Must raise :class:`EOFError` on
        end-of-input.
    output_fn:
        Called to write a line to the user.
    model_manager:
        Optional model manager used to generate responses for each prompt.

    Returns
    -------
    list[str]
        A list of user prompts received during the session.
    """
    output_fn(_GREETER)
    history: list[str] = []
    while True:
        try:
            prompt = input_fn()
        except EOFError:
            break
        text = prompt.strip()
        if not text:
            continue
        if text.lower() in _EXIT_KEYWORDS:
            break
        history.append(text)
        output_fn(f"{_PROMPT}{text}")
        if model_manager is not None:
            response = model_manager.generate(text)
            output_fn(response)
    return history


def build_command() -> click.Command:
    @command(
        "boskoll chat",
        "boskoll chat --model llama3.1",
        "boskoll chat --system \"you are a senior python reviewer\"",
        "boskoll",
    )
    @click.option(
        "--model",
        "model",
        type=str,
        default=None,
        help="Model to use for the session (e.g. llama3.1).",
    )
    @click.option(
        "--system",
        "system_prompt",
        type=str,
        default=None,
        help="System prompt that frames the assistant's behaviour.",
    )
    def chat(model: str | None, system_prompt: str | None) -> None:
        """Start an interactive chat session with boskoll.

        Launches a conversational interface where you can ask questions, and
        prompt boskoll to generate or review code. The session keeps an
        in-memory history of your prompts, which is echoed back when the
        session ends. Type ``exit`` or ``quit`` to leave the session.

        Running ``boskoll`` with no subcommand starts chat mode by default.
        Use ``--model`` to pick a local or cloud model and ``--system`` to
        frame the assistant with a role or focus.
        """
        manager = _build_model_manager(model)
        if manager is not None:
            click.echo(f"Using model manager with model: {model}")
        if system_prompt:
            click.echo(f"System prompt: {system_prompt}")
        history = run_chat(input_fn=input, output_fn=click.echo, model_manager=manager)
        if history:
            click.echo("Session history:")
            for prompt in history:
                click.echo(f"{_PROMPT}{prompt}")

    return chat
