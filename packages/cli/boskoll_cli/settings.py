"""Persistent settings shared by the CLI and TUI."""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path


class Theme(str, Enum):
    """Themes supported by boskoll."""

    DARK = "dark"
    LIGHT = "light"


DEFAULT_THEME = Theme.DARK
_CONFIG_PATH_ENV = "BOSKOLL_CONFIG_PATH"


def config_path() -> Path:
    """Return the active configuration path."""
    configured_path = os.environ.get(_CONFIG_PATH_ENV)
    if configured_path:
        return Path(configured_path).expanduser()
    return Path.cwd() / ".boskoll" / "config.toml"


def load_theme(path: Path | None = None) -> Theme:
    """Load the configured theme, defaulting to dark when no setting exists."""
    active_path = path or config_path()
    if not active_path.exists():
        return DEFAULT_THEME

    configured_theme = DEFAULT_THEME.value
    for line in active_path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if key.strip() == "theme" and separator:
            configured_theme = value.strip().strip('"')
            break
    try:
        return Theme(configured_theme)
    except ValueError as error:
        raise ValueError(
            f"Invalid theme {configured_theme!r}; expected 'dark' or 'light'."
        ) from error


def save_theme(theme: Theme, path: Path | None = None) -> Path:
    """Persist ``theme`` and return the path written."""
    active_path = path or config_path()
    active_path.parent.mkdir(parents=True, exist_ok=True)
    active_path.write_text(f'theme = "{theme.value}"\n', encoding="utf-8")
    return active_path
