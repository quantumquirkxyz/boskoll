"""Subcommand modules and registry for the boskoll CLI.

Each public module below exposes ``COMMAND_NAME`` and ``build_command()`` and
is auto-discovered by :func:`boskoll_cli.commands._registry.register_commands`.
"""

from boskoll_cli.commands._registry import (
    discover_command_modules,
    load_command_module,
    register_commands,
)

__all__ = [
    "discover_command_modules",
    "load_command_module",
    "register_commands",
]
