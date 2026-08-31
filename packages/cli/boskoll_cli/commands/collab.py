"""The ``collab`` subcommand."""

from __future__ import annotations

import click

from boskoll_cli.commands._help import command

COMMAND_NAME = "collab"


def build_command() -> click.Command:
    @command(
        "boskoll collab",
        "boskoll collab --channel backend",
        "boskoll collab --role \"senior code reviewer\"",
    )
    @click.option(
        "--channel",
        "channel",
        type=str,
        default=None,
        help="Name of the shared collaboration channel to join.",
    )
    @click.option(
        "--role",
        "role",
        type=str,
        default=None,
        help="Assign boskoll a role in the session (e.g. senior code reviewer).",
    )
    def collab(channel: str | None, role: str | None) -> None:
        """Start a real-time collaborative session with other developers.

        Collaborative mode lets multiple users work together on the same
        boskoll session and engage in AI pair programming, such as assigning
        boskoll the role of a senior developer to review your work. Use
        ``--channel`` to join a named session and ``--role`` to frame how
        boskoll participates.
        """
        if channel:
            click.echo(f"Channel: {channel}")
        if role:
            click.echo(f"Role: {role}")
        click.echo("Collaboration:")

    return collab
