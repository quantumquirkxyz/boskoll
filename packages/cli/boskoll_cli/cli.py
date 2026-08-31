"""Main CLI entry point for boskoll."""

from __future__ import annotations

import click

from boskoll_cli._version import __version__
from boskoll_cli.commands import register_commands


@click.group()
@click.version_option(version=__version__, prog_name="boskoll")
def main() -> None:
    """boskoll — CLI + TUI for software development with hyper-specialized AI agents."""


register_commands(main)
