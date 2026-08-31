# Use LangChain as the agent orchestrator

Status: accepted
Date: 2026-08-30

## Context

boskoll needs an orchestrator to manage complex multi-step workflows across multiple specialized agents (Code Generator, Code Reviewer, Test Generator, DevOps, Security, etc.). The orchestrator must support tool composition, memory, and integration with multiple LLM providers (Ollama, OpenRouter).

## Decision

Use LangChain as the primary agent orchestration framework.

## Consequences

- Positive: Native integrations with Ollama, Hugging Face, and OpenRouter. Rich ecosystem of tools, chains, and agents. Active community and extensive documentation. Supports memory, tool composition, and complex workflows out of the box.
- Negative: LangChain's abstractions can be heavyweight for simple tasks. API changes frequently between versions. Some developers find the abstraction layers confusing.
- Follow-up: Evaluate LangChain's performance for complex multi-agent workflows; consider LangGraph for stateful orchestration if needed.

## Considered Options

- **LangChain**: Most mature Python framework for agent orchestration, best LLM provider integrations.
- **Semantic Kernel**: Microsoft's framework, better for .NET/TypeScript, less mature Python support.
- **Custom orchestration**: More control, but reinvents the wheel for common patterns (memory, tools, chains).
