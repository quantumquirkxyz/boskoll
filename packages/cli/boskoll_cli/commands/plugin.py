"""The ``plugin`` subcommand."""

from __future__ import annotations

import click

COMMAND_NAME = "plugin"


def build_command() -> click.Command:
    @click.command()
    def plugin() -> None:
        """Manage plugins."""
        click.echo("Plugins:")

    return plugin
