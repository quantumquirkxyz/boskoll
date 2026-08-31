"""The ``agent`` subcommand."""

from __future__ import annotations

import click

COMMAND_NAME = "agent"


def build_command() -> click.Command:
    @click.command()
    @click.argument("action", type=click.Choice(["list", "create", "remove"]))
    def agent(action: str) -> None:
        """Manage specialized agents."""
        click.echo(f"Agents: {action}")

    return agent
