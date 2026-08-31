# Use Python as the primary language for boskoll

Status: accepted
Date: 2026-08-30

## Context

boskoll is a CLI + TUI tool for AI-assisted software development. It needs deep integration with AI/ML ecosystems (Hugging Face, Ollama, LangChain), code analysis (AST, tree-sitter), and agent orchestration. The primary alternatives were Python and TypeScript.

## Decision

Use Python as the primary language for the backend, CLI, and agent logic.

## Consequences

- Positive: Native access to the AI/ML ecosystem (Hugging Face, Ollama, LangChain, transformers). Rich library support for code analysis (AST, tree-sitter). Large community and ecosystem for AI projects.
- Negative: Slower execution compared to TypeScript/Go for CPU-bound tasks. Type safety less strict than TypeScript (mitigated by type hints and mypy).
- Follow-up: Monitor performance bottlenecks in agent orchestration; consider Cython or Rust extensions if needed.

## Considered Options

- **Python**: Best ecosystem fit for AI/ML, largest community, most libraries for code analysis.
- **TypeScript**: Better DX, stricter typing, but weaker AI/ML ecosystem integration.
- **Go**: Best performance, but smallest AI/ML ecosystem; would require CGo bindings for most AI libraries.
