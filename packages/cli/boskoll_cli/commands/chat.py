"""The ``chat`` subcommand — interactive chat session."""

from __future__ import annotations

import os
from collections.abc import Callable

import click

from boskoll_cli.commands._help import command
from boskoll_cli.models import ModelManager, OllamaAdapter, OpenRouterAdapter

COMMAND_NAME = "chat"
_GREETER = "Welcome to boskoll chat"
_PROMPT = "boskoll> "
_EXIT_KEYWORDS = frozenset({"exit", "quit"})


def _build_model_manager(model: str | None) -> ModelManager | None:
    """Create a ModelManager from the ``--model`` flag value.

    Parsing rules:

    * ``ollama/<name>`` — use Ollama only.
    * ``openrouter/<name>`` — use OpenRouter only (requires ``OPENROUTER_API_KEY``).
    * ``<name>`` — use a ModelManager with Ollama primary + OpenRouter fallback,
      both configured with ``<name>``.
    * ``None`` — return ``None`` (no model forced).
    """
    if model is None:
        return None

    model = model.strip()
    if model.startswith("ollama/"):
        name = model[len("ollama/") :]
        return ModelManager(primary=OllamaAdapter(model=name), fallback=OllamaAdapter())

    if model.startswith("openrouter/"):
        name = model[len("openrouter/") :]
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise click.ClickException(
                "OPENROUTER_API_KEY environment variable is required for OpenRouter."
            )
        return ModelManager(
            primary=OpenRouterAdapter(api_key=api_key, model=name),
            fallback=OpenRouterAdapter(api_key=api_key),
        )

    return ModelManager(
        primary=OllamaAdapter(model=model),
        fallback=OpenRouterAdapter(api_key=os.environ.get("OPENROUTER_API_KEY") or ""),
    )


def run_chat(
    input_fn: Callable[[], str],
    output_fn: Callable[[str], None],
) -> list[str]:
    """Run the interactive chat loop and return the session history.

    Parameters
    ----------
    input_fn:
        Called to read a line from the user. Must raise :class:`EOFError` on
        end-of-input.
    output_fn:
        Called to write a line to the user.

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
    return history


def build_command() -> click.Command:
    @command(
        "boskoll chat",
        "boskoll chat --model ollama/llama3.1",
        "boskoll chat --system \"you are a senior python reviewer\"",
        "boskoll",
    )
    @click.option(
        "--model",
        "model",
        type=str,
        default=None,
        help="Model to use for the session (e.g. ollama/llama3.1 or llama3.1).",
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
        history = run_chat(input_fn=input, output_fn=click.echo)
        if history:
            click.echo("Session history:")
            for prompt in history:
                click.echo(f"{_PROMPT}{prompt}")

    return chat
