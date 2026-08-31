"""The ``workflow`` subcommand."""

from __future__ import annotations

import click

from boskoll_cli.commands._help import command

COMMAND_NAME = "workflow"


def build_command() -> click.Command:
    @command("boskoll workflow")
    def workflow() -> None:
        """Run autonomous workflows.

        Workflows decompose a complex task into subtasks, assign each one to
        the relevant specialized agent, and execute them without manual
        intervention. Critical decisions still pause for human approval.
        """
        click.echo("Workflow:")

    return workflow
