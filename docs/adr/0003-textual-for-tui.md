# Use Textual as the TUI framework

Status: accepted
Date: 2026-08-30

## Context

boskoll's primary user interface is a Terminal User Interface (TUI) with syntax highlighting, inline code editing, divisible panels, and interactive menus. The TUI must be built in Python to align with the backend language choice (ADR-0001).

## Decision

Use Textual as the TUI framework for boskoll.

## Consequences

- Positive: Native Python integration (no CGo bindings needed). Rich widget system with CSS-like styling. Active development by Textualize (creators of Rich). Built-in support for async, mouse input, and composability.
- Negative: Textual is younger than some alternatives (e.g., urwid). Widget ecosystem is smaller than web frameworks. CSS-like styling has a learning curve.
- Follow-up: Contribute upstream if custom widgets are needed; evaluate Textual's performance for large code displays.

## Considered Options

- **Textual**: Best Python TUI framework, native integration with Rich, active development, modern API.
- **Bubble Tea (Go)**: Excellent performance and design, but requires CGo bindings or a separate binary.
- **urwid**: Mature Python TUI library, but older API and less actively maintained.
- **Prompt Toolkit**: Good for simple CLIs, but lacks advanced widget system needed for boskoll's TUI.
