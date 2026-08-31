"""Tests for the boskoll CLI main entry point."""

import importlib.metadata

import click.testing
import pytest

from boskoll_cli import __version__, main
from boskoll_cli.cli import main as cli_main


@pytest.fixture
def runner() -> click.testing.CliRunner:
    return click.testing.CliRunner()


def invoke_and_assert_ok(runner: click.testing.CliRunner, args: list[str]) -> click.testing.Result:
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    return result


def test_main_is_click_group() -> None:
    assert isinstance(cli_main, click.Group)


def test_console_scripts_entry_point_exists() -> None:
    entry_points = importlib.metadata.entry_points()
    assert any(
        ep.name == "boskoll" and ep.value == "boskoll_cli.cli:main"
        for ep in entry_points.select(group="console_scripts")
    )


def test_help_shows_usage(runner: click.testing.CliRunner) -> None:
    result = invoke_and_assert_ok(runner, ["--help"])
    assert "Usage:" in result.output
    assert "--version" in result.output
    assert "--help" in result.output


def test_version_shows_version(runner: click.testing.CliRunner) -> None:
    result = invoke_and_assert_ok(runner, ["--version"])
    assert __version__ in result.output
