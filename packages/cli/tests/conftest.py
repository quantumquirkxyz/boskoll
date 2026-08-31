"""Shared pytest fixtures and helpers for the boskoll CLI integration tests."""

from __future__ import annotations

import click.testing
import pytest

from boskoll_cli import main


@pytest.fixture
def runner() -> click.testing.CliRunner:
    return click.testing.CliRunner()


def invoke(runner: click.testing.CliRunner, args: list[str]) -> click.testing.Result:
    result = runner.invoke(main, args)
    assert result.exit_code == 0, result.output
    return result
