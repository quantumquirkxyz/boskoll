"""Main CLI entry point for boskoll."""

from __future__ import annotations

import click

from boskoll_cli._version import __version__
from boskoll_cli.commands import register_commands
from boskoll_cli.commands._help import HelpGroup, _example_block


@click.group(
    cls=HelpGroup,
    invoke_without_command=True,
    epilog=_example_block(
        "boskoll",
        "boskoll chat",
        "boskoll config",
        "boskoll agent",
        "boskoll workflow",
        "boskoll sandbox",
        "boskoll plugin",
        "boskoll collab",
        "boskoll update",
    ),
)
@click.version_option(version=__version__, prog_name="boskoll")
@click.pass_context
def main(ctx: click.Context) -> None:
    """boskoll — CLI + TUI for software development with AI agents.

    It provides hyper-specialized agents, autonomous workflows, sandbox
    execution, and a real-time collaborative terminal experience.
    """
    if ctx.invoked_subcommand is None:
        chat = main.get_command(ctx, "chat")
        if chat is not None:
            ctx.invoke(chat)


register_commands(main)
