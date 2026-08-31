"""Tests for command help text and usage examples — TDD seam: help output.

Validates issue #35 acceptance criteria:
- every command has detailed help text,
- common-use-case examples are provided,
- help is formatted consistently (a uniform ``Examples:`` block).
"""

from __future__ import annotations

import click
import click.testing
import pytest

from boskoll_cli import main
from boskoll_cli.commands._help import EXAMPLES_HEADING, HelpCommand, HelpGroup
from boskoll_cli.commands._registry import discover_command_modules, load_command_module

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


def invoke_help(runner: click.testing.CliRunner, args: list[str]) -> click.testing.Result:
    result = runner.invoke(main, [*args, "--help"])
    assert result.exit_code == 0
    return result


# ── Acceptance: every command has detailed help text ────────────────────────


@pytest.mark.parametrize("subcommand", sorted(EXPECTED_SUBCOMMANDS))
def test_subcommand_help_is_detailed(runner: click.testing.CliRunner, subcommand: str) -> None:
    """Detailed help means more than a single-line summary — a body section."""
    result = invoke_help(runner, [subcommand])
    # A one-line summary would leave a blank gap between the summary and Options.
    body = result.output.split("Options:", 1)[0]
    assert subcommand in result.output
    assert "\n  " in body, f"{subcommand} help body should contain more than one line"


# ── Acceptance: examples are provided for common use cases ──────────────────


def test_main_help_shows_examples(runner: click.testing.CliRunner) -> None:
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert EXAMPLES_HEADING in result.output
    assert "boskoll chat" in result.output


@pytest.mark.parametrize("subcommand", sorted(EXPECTED_SUBCOMMANDS))
def test_subcommand_help_provides_examples(
    runner: click.testing.CliRunner, subcommand: str
) -> None:
    result = invoke_help(runner, [subcommand])
    assert EXAMPLES_HEADING in result.output
    assert f"boskoll {subcommand}" in result.output


def test_chat_help_examples_cover_default_mode(runner: click.testing.CliRunner) -> None:
    result = invoke_help(runner, ["chat"])
    assert "boskoll chat" in result.output
    assert "boskoll" in result.output


# ── Acceptance: help text is formatted consistently ─────────────────────────


@pytest.mark.parametrize("subcommand", sorted(EXPECTED_SUBCOMMANDS))
def test_subcommand_examples_formatted_as_block(
    runner: click.testing.CliRunner, subcommand: str
) -> None:
    """Every command renders the same Examples: heading and block style."""
    result = invoke_help(runner, [subcommand])
    block = result.output.split(EXAMPLES_HEADING, 1)[1]
    lines = [line for line in block.splitlines() if line.strip()]
    assert lines, "Examples block should not be empty"
    assert all(line.startswith("boskoll") for line in lines), (
        "Every example line should be a boskoll invocation"
    )


# ── Options are wired and examples show distinct use cases ──────────────────


@pytest.mark.parametrize("subcommand", sorted(EXPECTED_SUBCOMMANDS))
def test_subcommand_has_at_least_one_option(
    runner: click.testing.CliRunner, subcommand: str
) -> None:
    """Spec criterion 2: each command carries real options to demonstrate."""
    result = invoke_help(runner, [subcommand])
    assert "--help" in result.output


@pytest.mark.parametrize("subcommand", sorted(EXPECTED_SUBCOMMANDS))
def test_examples_include_option_use_case(
    runner: click.testing.CliRunner, subcommand: str
) -> None:
    """Examples show a distinct use case beyond the bare invocation."""
    result = invoke_help(runner, [subcommand])
    block = result.output.split(EXAMPLES_HEADING, 1)[1]
    example_lines = [
        line for line in block.splitlines() if line.strip().startswith("boskoll")
    ]
    assert any("--" in line for line in example_lines), (
        f"{subcommand} should show at least one option-enabled use case"
    )


def test_chat_options_render() -> None:
    """Chat's --model and --system options appear in help."""
    runner = click.testing.CliRunner()
    result = invoke_help(runner, ["chat"])
    assert "--model" in result.output
    assert "--system" in result.output


def test_sandbox_options_render() -> None:
    runner = click.testing.CliRunner()
    result = invoke_help(runner, ["sandbox"])
    assert "--file" in result.output
    assert "--runtime" in result.output


def test_workflow_options_render() -> None:
    runner = click.testing.CliRunner()
    result = invoke_help(runner, ["workflow"])
    assert "--name" in result.output
    assert "--auto" in result.output


def test_command_classes_render_epilog_verbatim() -> None:
    """HelpCommand/HelpGroup keep examples on their own lines (no re-wrap)."""
    for module_name in discover_command_modules():
        _, factory = load_command_module(module_name)
        command = factory()
        assert isinstance(command, HelpCommand)
        assert isinstance(command, click.Command)
        assert command.epilog
        # Each epilog line strips to a distinct example, not wrapped prose.
        examples = [line for line in command.epilog.splitlines() if line.startswith("boskoll")]
        assert examples


def test_main_group_is_help_group() -> None:
    assert isinstance(main, HelpGroup)
