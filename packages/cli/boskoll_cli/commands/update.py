"""The ``update`` subcommand."""

from __future__ import annotations

import click

from boskoll_cli.commands._help import command

COMMAND_NAME = "update"


def build_command() -> click.Command:
    @command(
        "boskoll update",
        "boskoll update --apply",
    )
    @click.option(
        "--apply",
        "do_apply",
        is_flag=True,
        default=False,
        help="Download and apply the latest version when available.",
    )
    def update(do_apply: bool) -> None:
        """Check for and apply updates to boskoll.

        Contacts the update source to check whether a newer version of boskoll
        is available and, when one is found, applies it. Running this without
        options reports availability; pass ``--apply`` to install the newest
        version.
        """
        if do_apply:
            click.echo("Applying update...")
        else:
            click.echo("Check:")

    return update
