"""Integration tests for per-subcommand behavior via the Click test runner.

Covers the default (no-option) path and the secondary/combined option surface
of every subcommand — the gaps not exercised by ``test_cli.py``.
"""

from __future__ import annotations

import click.testing
import pytest
from conftest import invoke

from boskoll_cli import main

# ── Default (no-option) behavior ─────────────────────────────────────────────


@pytest.mark.parametrize(
    ("subcommand", "expected"),
    [
        ("agent", "Agents:"),
        ("collab", "Collaboration:"),
        ("config", "Configuration:"),
        ("plugin", "Plugins:"),
        ("sandbox", "Sandbox:"),
        ("workflow", "Workflows:"),
        ("update", "Check:"),
    ],
)
def test_bare_subcommand_prints_default_view(
    runner: click.testing.CliRunner, subcommand: str, expected: str
) -> None:
    result = invoke(runner, [subcommand])
    assert expected in result.output


def test_chat_without_args_launches_session(runner: click.testing.CliRunner) -> None:
    result = invoke(runner, ["chat"])
    assert "Welcome to boskoll chat" in result.output


# ── Secondary / combined options per subcommand ──────────────────────────────


def test_agent_describe_shows_name_and_not_list(runner: click.testing.CliRunner) -> None:
    result = invoke(runner, ["agent", "--describe", "devops"])
    assert "Agent: devops" in result.output
    assert "Agents:" not in result.output


def test_collab_role_option(runner: click.testing.CliRunner) -> None:
    result = invoke(runner, ["collab", "--role", "senior code reviewer"])
    assert "Role: senior code reviewer" in result.output


def test_collab_channel_and_role_combine(runner: click.testing.CliRunner) -> None:
    result = invoke(runner, ["collab", "--channel", "backend", "--role", "reviewer"])
    assert "Channel: backend" in result.output
    assert "Role: reviewer" in result.output


def test_config_show_path(runner: click.testing.CliRunner) -> None:
    result = invoke(runner, ["config", "--path"])
    assert "Config path:" in result.output


def test_config_get_specific_key(runner: click.testing.CliRunner) -> None:
    result = invoke(runner, ["config", "--get", "model"])
    assert "model =" in result.output


def test_config_path_takes_precedence_over_get(runner: click.testing.CliRunner) -> None:
    result = invoke(runner, ["config", "--path", "--get", "model"])
    assert "Config path:" in result.output


def test_plugin_remove_option(runner: click.testing.CliRunner) -> None:
    result = invoke(runner, ["plugin", "--remove", "legacy-agent"])
    assert "Removing plugin: legacy-agent" in result.output


def test_plugin_install_takes_precedence_over_remove(
    runner: click.testing.CliRunner,
) -> None:
    result = invoke(runner, ["plugin", "--install", "a", "--remove", "b"])
    assert "Installing plugin: a" in result.output
    assert "Removing plugin: b" not in result.output


def test_sandbox_with_file_and_runtime(runner: click.testing.CliRunner) -> None:
    result = invoke(runner, ["sandbox", "--file", "scripts/check.py", "--runtime", "firecracker"])
    assert "Running scripts/check.py in sandbox (firecracker)" in result.output


def test_sandbox_file_uses_default_runtime(runner: click.testing.CliRunner) -> None:
    result = invoke(runner, ["sandbox", "--file", "scripts/check.py"])
    assert "Running scripts/check.py in sandbox (default)" in result.output


def test_sandbox_rejects_unknown_runtime(runner: click.testing.CliRunner) -> None:
    result = runner.invoke(main, ["sandbox", "--runtime", "nomad"])
    assert result.exit_code != 0


def test_workflow_auto_flag(runner: click.testing.CliRunner) -> None:
    result = invoke(runner, ["workflow", "--name", "lint", "--auto"])
    assert "Workflow: lint (auto-approve: True)" in result.output


def test_workflow_without_auto(runner: click.testing.CliRunner) -> None:
    result = invoke(runner, ["workflow", "--name", "lint"])
    assert "Workflow: lint (auto-approve: False)" in result.output


def test_workflow_needs_name_for_auto(runner: click.testing.CliRunner) -> None:
    result = invoke(runner, ["workflow", "--auto"])
    assert "Workflows:" in result.output


def test_chat_system_prompt_option(runner: click.testing.CliRunner) -> None:
    result = invoke(runner, ["chat", "--system", "you are a reviewer"])
    assert "System prompt: you are a reviewer" in result.output


def test_chat_model_and_system_combine(runner: click.testing.CliRunner) -> None:
    result = invoke(runner, ["chat", "--model", "ollama/llama3.1", "--system", "be concise"])
    assert "Using model: ollama/llama3.1" in result.output
    assert "System prompt: be concise" in result.output
