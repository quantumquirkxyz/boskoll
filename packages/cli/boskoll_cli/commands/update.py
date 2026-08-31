"""The ``update`` subcommand."""

from __future__ import annotations

import click

COMMAND_NAME = "update"


def build_command() -> click.Command:
    @click.command()
    def update() -> None:
        """Check for and apply updates."""
        click.echo("Update:")

    return update
