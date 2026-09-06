"""The ``config`` subcommand."""

from __future__ import annotations

import click

from boskoll_cli.commands._help import command
from boskoll_cli.settings import Theme, config_path, load_theme, save_theme

COMMAND_NAME = "config"


def build_command() -> click.Command:
    @command(
        "boskoll config",
        "boskoll config --get model",
        "boskoll config --theme light",
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
    @click.option(
        "--theme",
        type=click.Choice([theme.value for theme in Theme], case_sensitive=False),
        default=None,
        help="Set the TUI theme (dark or light).",
    )
    def config(key: str | None, show_path: bool, theme: str | None) -> None:
        """Show the current boskoll configuration.

        Displays or updates the active settings for boskoll. Dark is the
        default theme. Use ``--theme`` to persist a theme selection, ``--get``
        to show a single key, and ``--path`` to locate the configuration file.
        """
        if show_path:
            click.echo(f"Config path: {config_path()}")
        elif theme is not None:
            selected_theme = Theme(theme)
            path = save_theme(selected_theme)
            click.echo(f"Theme: {selected_theme.value}")
            click.echo(f"Config path: {path}")
        elif key:
            if key == "theme":
                click.echo(f"theme = {load_theme().value}")
            else:
                click.echo(f"{key} = <value>")
        else:
            click.echo("Configuration:")
            click.echo(f"theme = {load_theme().value}")

    return config
