"""The ``collab`` subcommand."""

from __future__ import annotations

import click

COMMAND_NAME = "collab"


def build_command() -> click.Command:
    @click.command()
    def collab() -> None:
        """Start a real-time collaborative session."""
        click.echo("Collaboration:")

    return collab
