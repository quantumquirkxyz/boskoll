"""The ``sandbox`` subcommand."""

from __future__ import annotations

import click

COMMAND_NAME = "sandbox"


def build_command() -> click.Command:
    @click.command()
    def sandbox() -> None:
        """Run code in an isolated sandbox."""
        click.echo("Sandbox:")

    return sandbox
