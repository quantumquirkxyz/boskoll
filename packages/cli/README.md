# boskoll-cli

CLI + TUI for software development with hyper-specialized AI agents, autonomous workflows, sandbox execution, and full privacy.

## Install

```bash
pip install -e packages/cli
```

## Usage

The `boskoll` command is the main entry point. Without a subcommand it starts an interactive chat session (foundational — chat mode is implemented in a later ticket).

```bash
boskoll --version
boskoll chat
boskoll config
boskoll init
boskoll agents
boskoll status
boskoll history
boskoll models
boskoll plugins
```

## Development

```bash
pip install -e "packages/cli[dev]"
ruff check boskoll_cli
pytest
```
