"""Main CLI entry point for boskoll."""

import click

from boskoll_cli._version import __version__


@click.group()
@click.version_option(version=__version__, prog_name="boskoll")
def main() -> None:
    """boskoll — CLI + TUI for software development with hyper-specialized AI agents."""


@main.command()
def chat() -> None:
    """Start an interactive chat session."""
    click.echo("Starting chat session...")


@main.command()
def config() -> None:
    """Show current configuration."""
    click.echo("Configuration:")


@main.command()
def init() -> None:
    """Initialize a new project."""
    click.echo("Initializing project...")


@main.command()
def agents() -> None:
    """List available agents."""
    click.echo("Available agents:")


@main.command()
def status() -> None:
    """Show current status."""
    click.echo("Status:")


@main.command()
def history() -> None:
    """Show interaction history."""
    click.echo("History:")


@main.command()
def models() -> None:
    """Manage AI models."""
    click.echo("Models:")


@main.command()
def plugins() -> None:
    """Manage plugins."""
    click.echo("Plugins:")
