"""Shared helpers for consistently formatted command help and usage examples.

All boskoll subcommands use :func:`command` (backed by :class:`HelpCommand`)
so that every command renders its usage examples in the same preformatted
``Examples:`` block, keeping help consistent across the CLI.
"""

from __future__ import annotations

from collections.abc import Callable

import click

EXAMPLES_HEADING = "Examples:"


def _example_block(*examples: str) -> str:
    """Build a preformatted ``Examples:`` block from ``examples``."""
    return "\n".join([EXAMPLES_HEADING, *examples])


class HelpCommandBase(click.Command):
    """Base for commands that render their usage examples verbatim.

    Click normally re-wraps an ``epilog`` into a single paragraph, which
    destroys code-style example formatting. This base overrides
    :meth:`format_epilog` to emit the epilog lines without re-wrapping so the
    ``Examples:`` block stays readable and consistent.
    """

    def format_epilog(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        if not self.epilog:
            return
        formatter.write_paragraph()
        for line in self.epilog.splitlines():
            formatter.write(line.strip() + "\n")


class HelpCommand(HelpCommandBase):
    """A leaf :class:`click.Command` that renders examples verbatim."""


class HelpGroup(HelpCommandBase, click.Group):
    """A :class:`click.Group` that renders its epilog examples verbatim."""


def command(*examples: str) -> Callable[[Callable[..., object]], HelpCommand]:
    """Build a :class:`HelpCommand` factory carrying the given usage examples.

    Mirrors :func:`click.command` (including deriving ``help`` from the
    decorated function's docstring) while attaching a consistent ``Examples:``
    block built from ``examples``. Use it inside each subcommand module's
    ``build_command()``::

        @command("boskoll agent")
        def agent() -> None:
            ...
    """

    def decorate(func: Callable[..., object]) -> HelpCommand:
        return HelpCommand(
            func.__name__,
            help=func.__doc__,
            epilog=_example_block(*examples),
            callback=func,
        )

    return decorate
