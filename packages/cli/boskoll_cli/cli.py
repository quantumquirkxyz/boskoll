"""Main CLI entry point for boskoll."""

from __future__ import annotations

import click

from boskoll_cli._version import __version__
from boskoll_cli.commands import register_commands


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="boskoll")
@click.pass_context
def main(ctx: click.Context) -> None:
    """boskoll — CLI + TUI for software development with hyper-specialized AI agents."""
    if ctx.invoked_subcommand is None:
        chat = main.get_command(ctx, "chat")
        if chat is not None:
            ctx.invoke(chat)


register_commands(main)
