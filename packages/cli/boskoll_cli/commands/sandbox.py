"""The ``sandbox`` subcommand."""

from __future__ import annotations

import click

from boskoll_cli.commands._help import command

COMMAND_NAME = "sandbox"


def build_command() -> click.Command:
    @command("boskoll sandbox", "boskoll sandbox --help")
    def sandbox() -> None:
        """Run code in an isolated sandbox.

        Executes generated code in a secure, isolated environment so it can be
        validated for syntax, correctness, and performance before it is shown
        to you. This keeps your system safe while testing untrusted or
        generated code.
        """
        click.echo("Sandbox:")

    return sandbox
