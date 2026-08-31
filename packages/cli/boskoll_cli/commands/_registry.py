"""Subcommand registry for boskoll.

Each subcommand lives in its own module under ``boskoll_cli.commands`` and
declares two public names:

- ``COMMAND_NAME`` (``str``): the name used on the CLI.
- ``build_command()`` (``CommandFactory``): a factory returning a fully
  configured Click command, including its help text.

The registry auto-discovers command modules with :func:`pkgutil.iter_modules`
and registers each command into the root :class:`click.Group`.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable

import click

from boskoll_cli import commands as _commands_package

CommandFactory = Callable[[], click.Command]


def discover_command_modules() -> list[str]:
    """Return the import names of all subcommand modules in this package."""
    return [
        module.name
        for module in pkgutil.iter_modules(_commands_package.__path__)
        if not module.name.startswith("_")
    ]


def load_command_module(module_name: str) -> tuple[str, CommandFactory]:
    """Import a subcommand module and return its (name, factory) pair."""
    module = importlib.import_module(f"{_commands_package.__name__}.{module_name}")
    name = module.COMMAND_NAME
    factory = module.build_command
    return name, factory


def register_commands(group: click.Group) -> click.Group:
    """Discover subcommand modules and register them onto ``group`` in place."""
    for module_name in discover_command_modules():
        name, factory = load_command_module(module_name)
        group.add_command(factory(), name=name)
    return group
