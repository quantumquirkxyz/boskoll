"""Tests for the boskoll CLI main entry point."""

import importlib.metadata

import click
import click.testing
import pytest

from boskoll_cli import __version__, main
from boskoll_cli.cli import main as cli_main
from boskoll_cli.commands import (
    discover_command_modules,
    load_command_module,
    register_commands,
)

EXPECTED_SUBCOMMANDS = {
    "agent",
    "chat",
    "collab",
    "config",
    "plugin",
    "sandbox",
    "update",
    "workflow",
}


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


def test_all_subcommands_registered_on_group() -> None:
    assert isinstance(cli_main, click.Group)
    registered = set(cli_main.commands)
    assert EXPECTED_SUBCOMMANDS <= registered


def test_subcommand_modules_auto_discovered() -> None:
    module_names = discover_command_modules()
    assert len(module_names) == len(EXPECTED_SUBCOMMANDS)
    for module_name in module_names:
        name, factory = load_command_module(module_name)
        assert name in EXPECTED_SUBCOMMANDS
        assert callable(factory)


def test_each_subcommand_module_exposes_contract() -> None:
    for module_name in discover_command_modules():
        name, factory = load_command_module(module_name)
        command = factory()
        assert isinstance(command, click.Command)
        assert command.name == name


@pytest.mark.parametrize("subcommand", sorted(EXPECTED_SUBCOMMANDS))
def test_subcommand_help_text_generated(runner: click.testing.CliRunner, subcommand: str) -> None:
    result = invoke_and_assert_ok(runner, [subcommand, "--help"])
    assert subcommand in result.output
    assert "--help" in result.output


def test_register_commands_registers_in_place() -> None:
    group = click.Group()
    register_commands(group)
    assert EXPECTED_SUBCOMMANDS <= set(group.commands)


@pytest.mark.parametrize(
    ("subcommand", "option_args", "expected"),
    [
        ("agent", ["--describe", "security"], "Agent: security"),
        ("chat", ["--model", "ollama/llama3.1"], "Using model: ollama/llama3.1"),
        ("collab", ["--channel", "backend"], "Channel: backend"),
        ("config", ["--get", "model"], "model ="),
        ("plugin", ["--install", "security-scan"], "Installing plugin: security-scan"),
        ("sandbox", ["--file", "scripts/check.py"], "Running scripts/check.py"),
        ("update", ["--apply"], "Applying update..."),
        ("workflow", ["--name", "release"], "Workflow: release"),
    ],
)
def test_subcommand_options_execute(
    runner: click.testing.CliRunner,
    subcommand: str,
    option_args: list[str],
    expected: str,
) -> None:
    """Each subcommand's documented option actually runs."""
    result = invoke_and_assert_ok(runner, [subcommand, *option_args])
    assert expected in result.output


def test_update_default_action_is_check_not_apply(
    runner: click.testing.CliRunner,
) -> None:
    """Bare `boskoll update` reports a check; it does not apply."""
    result = invoke_and_assert_ok(runner, ["update"])
    assert "Check:" in result.output
    assert "Applying update..." not in result.output


def test_update_apply_still_works(runner: click.testing.CliRunner) -> None:
    result = invoke_and_assert_ok(runner, ["update", "--apply"])
    assert "Applying update..." in result.output


def test_update_has_no_dead_check_flag(runner: click.testing.CliRunner) -> None:
    """The removed dead `--check` flag is no longer accepted."""
    result = runner.invoke(main, ["update", "--check"])
    assert result.exit_code != 0
    assert "No such option" in result.output
