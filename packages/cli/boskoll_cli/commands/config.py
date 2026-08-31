"""The ``config`` subcommand."""

from __future__ import annotations

import click

COMMAND_NAME = "config"


def build_command() -> click.Command:
    @click.command()
    def config() -> None:
        """Show current configuration."""
        click.echo("Configuration:")

    return config
