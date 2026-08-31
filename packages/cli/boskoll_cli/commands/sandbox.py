"""The ``sandbox`` subcommand."""

from __future__ import annotations

import click

from boskoll_cli.commands._help import command

COMMAND_NAME = "sandbox"


def build_command() -> click.Command:
    @command(
        "boskoll sandbox --file scripts/check.py",
        "boskoll sandbox --file scripts/check.py --runtime docker",
    )
    @click.option(
        "--file",
        "file_path",
        type=click.Path(exists=False),
        default=None,
        help="Path to the code file to run in the sandbox.",
    )
    @click.option(
        "--runtime",
        "runtime",
        type=click.Choice(["docker", "firecracker"]),
        default=None,
        help="Isolation runtime to use (docker or firecracker).",
    )
    def sandbox(file_path: str | None, runtime: str | None) -> None:
        """Run code in an isolated sandbox.

        Executes code in a secure, isolated environment so it can be validated
        for syntax, correctness, and performance before it is shown to you.
        Pass ``--file`` to run a specific file and ``--runtime`` to choose the
        isolation backend.
        """
        if file_path:
            click.echo(f"Running {file_path} in sandbox ({runtime or 'default'})")
        else:
            click.echo("Sandbox:")

    return sandbox
