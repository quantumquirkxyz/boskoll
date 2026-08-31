"""The ``agent`` subcommand."""

from __future__ import annotations

import click

COMMAND_NAME = "agent"


def build_command() -> click.Command:
    @click.command()
    def agent() -> None:
        """Manage specialized agents."""
        click.echo("Agents:")

    return agent
