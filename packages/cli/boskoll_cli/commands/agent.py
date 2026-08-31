"""The ``agent`` subcommand."""

from __future__ import annotations

import click

from boskoll_cli.commands._help import command

COMMAND_NAME = "agent"


def build_command() -> click.Command:
    @command("boskoll agent", "boskoll agent --help")
    def agent() -> None:
        """Manage the specialized AI agents bundled with boskoll.

        Each agent is a domain-specific module pre-trained for a focused task,
        such as code generation, code review, or test generation. This command
        lists the agents available in the current project and provides access
        to their capabilities.
        """
        click.echo("Agents:")

    return agent
