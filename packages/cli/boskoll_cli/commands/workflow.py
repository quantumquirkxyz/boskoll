"""The ``workflow`` subcommand."""

from __future__ import annotations

import click

COMMAND_NAME = "workflow"


def build_command() -> click.Command:
    @click.command()
    def workflow() -> None:
        """Run autonomous workflows."""
        click.echo("Workflow:")

    return workflow
