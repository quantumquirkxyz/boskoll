"""The ``chat`` subcommand — interactive chat session."""

from __future__ import annotations

from collections.abc import Callable, Iterator

import click

from boskoll_cli.commands._help import command
from boskoll_cli.models import ModelError, ModelManager, OllamaAdapter, OpenRouterAdapter

COMMAND_NAME = "chat"
_GREETER = "Welcome to boskoll chat"
_PROMPT = "boskoll> "
_EXIT_KEYWORDS = frozenset({"exit", "quit"})

Responder = Callable[[str], Iterator[str]]


def run_chat(
    input_fn: Callable[[], str],
    output_fn: Callable[[str], None],
    responder: Responder | None = None,
) -> list[str]:
    """Run the interactive chat loop and return the session history.

    Parameters
    ----------
    input_fn:
        Called to read a line from the user. Must raise :class:`EOFError` on
        end-of-input.
    output_fn:
        Called to write a line to the user.
    responder:
        Optional callable that turns a user prompt into a stream of response
        chunks. When provided, each prompt is sent to the responder and its
        chunks are written to ``output_fn`` instead of echoing the prompt
        back. When omitted the prompt is echoed (offline/echo mode).

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
        if responder is None:
            output_fn(f"{_PROMPT}{text}")
        else:
            for chunk in responder(text):
                output_fn(chunk)
    return history


def default_manager() -> ModelManager:
    """Build the model manager used when none is injected."""
    return ModelManager(
        local_adapter=OllamaAdapter(),
        cloud_adapter=OpenRouterAdapter(),
    )


def build_command(manager: ModelManager | None = None) -> click.Command:
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
        help="Model to use for the session (e.g. ollama/llama3.1).",
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
        frame the assistant with a role or focus. Without ``--model`` the
        session runs in echo mode (offline); with ``--model`` each prompt is
        sent to that model and its response is streamed to the terminal.
        """
        if model:
            click.echo(f"Using model: {model}")
        if system_prompt:
            click.echo(f"System prompt: {system_prompt}")

        active_manager = manager
        responder: Responder | None = None
        if model is not None:
            active_manager = manager if manager is not None else default_manager()

            def stream_response(text: str) -> Iterator[str]:
                return active_manager.stream(
                    text, model=model, system_prompt=system_prompt
                )

            responder = stream_response

        try:
            history = run_chat(input_fn=input, output_fn=click.echo, responder=responder)
        except ModelError as error:
            click.echo(f"Error: {error}", err=True)
            raise click.exceptions.Exit(1) from error

        if history:
            click.echo("Session history:")
            for prompt in history:
                click.echo(f"{_PROMPT}{prompt}")
        if model is not None and active_manager is not None and active_manager.usage.requests:
            click.echo(f"Usage: {active_manager.usage.summary()}")

    return chat
