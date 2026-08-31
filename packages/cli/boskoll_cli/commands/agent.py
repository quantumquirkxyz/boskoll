"""The ``agent`` subcommand."""

from __future__ import annotations

import click

from boskoll_cli.commands._help import command

COMMAND_NAME = "agent"


def build_command() -> click.Command:
    @command(
        "boskoll agent",
        "boskoll agent --describe security",
    )
    @click.option(
        "--describe",
        "agent_name",
        type=str,
        default=None,
        help="Show a description of a specific agent (e.g. security, devops).",
    )
    def agent(agent_name: str | None) -> None:
        """Manage the specialized AI agents bundled with boskoll.

        Each agent is a domain-specific module pre-trained for a focused task,
        such as code generation, code review, or test generation. With no
        options, this command lists the agents available in the current
        project. Pass ``--describe`` with an agent name to inspect a specific
        one's capabilities.
        """
        if agent_name:
            click.echo(f"Agent: {agent_name}")
        else:
            click.echo("Agents:")

    return agent
