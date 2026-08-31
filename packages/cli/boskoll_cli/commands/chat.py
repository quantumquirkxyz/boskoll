"""The ``chat`` subcommand."""

from __future__ import annotations

import click

COMMAND_NAME = "chat"


def build_command() -> click.Command:
    @click.command()
    def chat() -> None:
        """Start an interactive chat session."""
        click.echo("Chat:")

    return chat
