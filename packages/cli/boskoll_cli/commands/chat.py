"""The ``chat`` subcommand — interactive chat session."""

from __future__ import annotations

from collections.abc import Callable

import click

COMMAND_NAME = "chat"
_GREETER = "Welcome to boskoll chat"
_PROMPT = "boskoll> "
_EXIT_KEYWORDS = frozenset({"exit", "quit"})


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
    @click.command()
    def chat() -> None:
        """Start an interactive chat session."""
        history = run_chat(input_fn=input, output_fn=click.echo)
        if history:
            click.echo("Session history:")
            for prompt in history:
                click.echo(f"{_PROMPT}{prompt}")

    return chat
