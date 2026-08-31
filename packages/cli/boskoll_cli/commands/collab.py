"""The ``collab`` subcommand."""

from __future__ import annotations

import click

from boskoll_cli.commands._help import command

COMMAND_NAME = "collab"


def build_command() -> click.Command:
    @command("boskoll collab")
    def collab() -> None:
        """Start a real-time collaborative session with other developers.

        Collaborative mode lets multiple users work together on the same
        boskoll session and engage in AI pair programming, such as assigning
        boskoll the role of a senior developer to review your work.
        """
        click.echo("Collaboration:")

    return collab
