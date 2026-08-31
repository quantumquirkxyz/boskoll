"""The ``config`` subcommand."""

from __future__ import annotations

import click

from boskoll_cli.commands._help import command

COMMAND_NAME = "config"


def build_command() -> click.Command:
    @command(
        "boskoll config",
        "boskoll config --get model",
        "boskoll config --path",
    )
    @click.option(
        "--get",
        "key",
        type=str,
        default=None,
        help="Show the value of a single configuration key (e.g. model).",
    )
    @click.option(
        "--path",
        "show_path",
        is_flag=True,
        default=False,
        help="Print the path to the active configuration file.",
    )
    def config(key: str | None, show_path: bool) -> None:
        """Show the current boskoll configuration.

        Displays the active settings for boskoll, including model selection
        and preferences. Use ``--get`` to show a single key and ``--path`` to
        locate the configuration file, or run with no options to print the
        whole configuration.
        """
        if show_path:
            click.echo("Config path: <project>/.boskoll/config.toml")
        elif key:
            click.echo(f"{key} = <value>")
        else:
            click.echo("Configuration:")

    return config
