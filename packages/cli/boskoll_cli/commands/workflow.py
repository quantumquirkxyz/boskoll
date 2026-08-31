"""The ``workflow`` subcommand."""

from __future__ import annotations

import click

from boskoll_cli.commands._help import command

COMMAND_NAME = "workflow"


def build_command() -> click.Command:
    @command(
        "boskoll workflow",
        "boskoll workflow --name release",
        "boskoll workflow --name lint --auto",
    )
    @click.option(
        "--name",
        "name",
        type=str,
        default=None,
        help="Name of the workflow to run (e.g. release, lint).",
    )
    @click.option(
        "--auto",
        "auto_approve",
        is_flag=True,
        default=False,
        help="Run without pausing for human approval on critical decisions.",
    )
    def workflow(name: str | None, auto_approve: bool) -> None:
        """Run autonomous workflows.

        Workflows decompose a complex task into subtasks, assign each one to
        the relevant specialized agent, and execute them without manual
        intervention. Critical decisions still pause for human approval unless
        ``--auto`` is passed. Use ``--name`` to select a workflow.
        """
        if name:
            click.echo(f"Workflow: {name} (auto-approve: {auto_approve})")
        else:
            click.echo("Workflows:")

    return workflow
