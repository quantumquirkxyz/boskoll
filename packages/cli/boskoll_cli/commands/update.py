"""The ``update`` subcommand."""

from __future__ import annotations

import click

from boskoll_cli.commands._help import command

COMMAND_NAME = "update"


def build_command() -> click.Command:
    @command("boskoll update")
    def update() -> None:
        """Check for and apply updates to boskoll.

        Contacts the update source to check whether a newer version of boskoll
        is available and, when one is found, applies it. Run this regularly to
        keep your installation current.
        """
        click.echo("Update:")

    return update
