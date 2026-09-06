# boskoll-cli

CLI + TUI for software development with hyper-specialized AI agents, autonomous workflows, sandbox execution, and full privacy.

## Install

```bash
pip install -e packages/cli
```

## Usage

The `boskoll` command is the main entry point. Without a subcommand it starts an
interactive chat session (foundational — prompts receive a stub acknowledgement
and history is kept for the session).

```bash
boskoll --version
boskoll chat
boskoll config
boskoll config --theme light
boskoll agent
boskoll workflow
boskoll sandbox
boskoll plugin
boskoll collab
boskoll update
```

The TUI uses the dark theme by default. Set `--theme dark` or `--theme light`
to persist the preference in `.boskoll/config.toml`; use `ctrl+t` while the TUI
is running to switch themes for the current session.

Subcommands are registered through the auto-discovered command modules under
`boskoll_cli/commands/`; each module exposes `COMMAND_NAME` and `build_command()`.

## Development

```bash
pip install -e "packages/cli[dev]"
ruff check boskoll_cli
pytest
```
