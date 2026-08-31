"""The ``plugin`` subcommand."""

from __future__ import annotations

import click

from boskoll_cli.commands._help import command

COMMAND_NAME = "plugin"


def build_command() -> click.Command:
    @command(
        "boskoll plugin",
        "boskoll plugin --install security-scan",
        "boskoll plugin --remove legacy-agent",
    )
    @click.option(
        "--install",
        "install_name",
        type=str,
        default=None,
        help="Install a plugin by name from the marketplace.",
    )
    @click.option(
        "--remove",
        "remove_name",
        type=str,
        default=None,
        help="Remove an installed plugin by name.",
    )
    def plugin(install_name: str | None, remove_name: str | None) -> None:
        """Manage boskoll plugins.

        Plugins are user-developed or community-contributed extensions that
        add agents, workflows, or both to boskoll. With no options, list the
        plugins installed in the current project. Use ``--install`` or
        ``--remove`` to manage a specific plugin.
        """
        if install_name:
            click.echo(f"Installing plugin: {install_name}")
        elif remove_name:
            click.echo(f"Removing plugin: {remove_name}")
        else:
            click.echo("Plugins:")

    return plugin
