"""Main CLI entry point for boskoll."""

from __future__ import annotations

import click

from boskoll_cli._version import __version__
from boskoll_cli.commands import load_command_module, register_commands


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="boskoll")
@click.pass_context
def main(ctx: click.Context) -> None:
    """boskoll — CLI + TUI for software development with hyper-specialized AI agents."""
    if ctx.invoked_subcommand is None:
        _, chat_factory = load_command_module("chat")
        ctx.invoke(chat_factory())


register_commands(main)
