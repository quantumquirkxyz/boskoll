"""The ``config`` subcommand."""

from __future__ import annotations

import click

from boskoll_cli.commands._help import command

COMMAND_NAME = "config"


def build_command() -> click.Command:
    @command("boskoll config")
    def config() -> None:
        """Show the current boskoll configuration.

        Displays the active settings for boskoll, including model selection
        and preferences. Use this command to review your current configuration
        before changing it.
        """
        click.echo("Configuration:")

    return config
