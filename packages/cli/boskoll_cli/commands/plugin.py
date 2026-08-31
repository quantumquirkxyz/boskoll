"""The ``plugin`` subcommand."""

from __future__ import annotations

import click

from boskoll_cli.commands._help import command

COMMAND_NAME = "plugin"


def build_command() -> click.Command:
    @command("boskoll plugin", "boskoll plugin --help")
    def plugin() -> None:
        """Manage boskoll plugins.

        Plugins are user-developed or community-contributed extensions that
        add agents, workflows, or both to boskoll. This command lists the
        plugins installed in the current project.
        """
        click.echo("Plugins:")

    return plugin
