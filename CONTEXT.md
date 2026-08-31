# Context

## Project

**boskoll** — CLI + TUI for software development with hyper-specialized AI agents, autonomous workflows, sandbox execution, and full privacy.

GitHub: `quantumquirkxyz/boskoll`

## Unique Value Proposition (USP)

boskoll differentiates from competitors (Cursor, Claude Code, OpenCode, KiloCode, pi.dev, etc.) through a combination of innovative features:

### 1. Hyper-Specialized Agent System + Autonomous Workflows

Modular, customizable agents pre-trained in specific domains:

- **Blockchain Agent**: Generates Solidity smart contracts, analyzes vulnerabilities, suggests gas optimizations.
- **DevOps Agent**: Creates CI/CD pipelines (GitHub Actions, GitLab CI), configures Kubernetes, deploys to AWS/GCP.
- **Security Agent**: Scans code for vulnerabilities (OWASP Top 10), suggests patches, validates dependencies.
- **Performance Agent**: Optimizes SQL queries, identifies code bottlenecks, suggests algorithm improvements.
- **AI/ML Agent**: Generates ML model code (PyTorch, TensorFlow), preprocesses data, validates metrics.

Users can create custom agents using templates or from scratch (Python/TypeScript).

Autonomous workflows decompose complex tasks into subtasks, assign them to relevant agents, and execute without human intervention (except critical decisions).

### 2. Intelligent Code Context + Project Memory

- **AST (Abstract Syntax Tree) mapping**: Analyzes entire codebase (not just open file) to generate dependency graphs and relationships between classes, functions, and modules.
- **Consistency maintenance**: Follows existing patterns (e.g., TypeScript + NestJS).
- **Redundancy detection**: Detects installed libraries and suggests alternatives.
- **Persistent project memory**: Saves decision history, associates with Git commits, allows resuming conversations.

### 3. Sandbox Code Execution + Real-Time Validation

- **Integrated sandbox**: Every generated code is executed in an isolated environment (Docker/Firecracker) to validate syntax, test functionality, and measure performance.
- **Linter/formatter integration**: Auto-applies ESLint, Pylint, Black, Prettier.

### 4. Absolute Privacy + Local/Hybrid Models

- **100% Local Mode**: Run models locally via Ollama, LM Studio, Hugging Face — no data sent to cloud.
- **Hybrid Mode (Local + Cloud)**: For powerful models (e.g., Mixtral 8x7B) via OpenRouter with encryption.
- **Smart model manager**: Prioritizes local models, auto-switches to cloud when needed.

### 5. Advanced TUI + Editor Integration

- **TUI with Textual (Python)**: Syntax highlighting, inline editing, divisible panels.
- **Editor plugins**: VS Code, Neovim (LSP), JetBrains support.
- **CLI commands**: `boskoll --vs-code`, `boskoll --apply`.

### 6. Real-Time Collaboration + Pair Programming

- **Collaborative mode**: Multiple users connected via SSH/WebSocket.
- **AI pair programming**: Assign roles (e.g., "act as senior dev and review my code").

### 7. Plugin System + Agent Marketplace

- **Plugin architecture**: Users develop and share agents/workflows as plugins (Python, TypeScript, Go).
- **Agent marketplace**: Publish, download, rate, and monetize plugins.

### 8. Net Productivity Focus

- **Productivity metrics**: Time saved, code quality (cyclomatic complexity, code smells, test coverage), bug reduction.
- **Productivity reports**: Weekly/monthly with tasks completed, time saved, quality improvements.

### 9. No-Code/Low-Code in Terminal

- Generate Bash/Python scripts, Makefiles, Git workflows from natural language descriptions.

### 10. Developer Experience (DX) Superior

- Guided onboarding, customizable keyboard shortcuts, themes, real-time feedback (thumbs up/down).

## Competitive Landscape (2026)

| Feature | boskoll | Cursor | Claude Code | OpenCode | KiloCode | pi.dev | GitHub Copilot |
|---|---|---|---|---|---|---|---|
| Type | CLI + TUI | IDE | CLI | CLI | CLI | CLI | IDE/Editor |
| Specialized Agents | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Autonomous Workflows | ✅ | ❌ | Partial | ❌ | ❌ | ❌ | ❌ |
| Global Project Context | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Sandbox Execution | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Privacy (Local Mode) | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Advanced TUI | ✅ | ❌ | ❌ | Partial | Partial | ✅ | ❌ |
| Real-Time Collaboration | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Plugin/Agent Marketplace | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Free Models | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ |

## Tech Stack

### Backend (CLI + Agent Logic)

| Component | Technology | Justification |
|---|---|---|
| Primary Language | **Python** | Native AI ecosystem: Hugging Face, Ollama, LangChain, AST analysis |
| Agent Orchestrator | **LangChain** | Complex workflow management, native integrations with Ollama/HuggingFace/OpenRouter |
| Model Manager | **Ollama → OpenRouter fallback** | Local-first: if Ollama is available and capable, use local; fallback to OpenRouter for complex tasks or when local is unavailable. User can force with `--model`. |
| Sandbox Execution | **Docker** (MVP), Firecracker (roadmap) | Docker for MVP simplicity; Firecracker for enterprise-grade isolation later |
| Code Analysis | **AST + tree-sitter** | Multi-language support (40+ languages), fast parsing, code understanding and validation |
| Storage | **SQLite + JSON** | SQLite for structured data (history, decisions); JSON for configuration files |
| Auth | **JWT** (MVP), OAuth 2.0 (roadmap) | JWT for MVP sessions; OAuth for future external integrations |

### TUI

| Component | Technology | Justification |
|---|---|---|
| Framework | **Textual** (Python) | Advanced widgets, native Python, easy customization |
| Syntax Highlighting | **Rich + Pygments** | Rich for TUI integration; Pygments for code export and advanced highlighting |
| Inline Editing | Textual (with custom keybindings) | Edit code directly in TUI; custom boskoll-specific keybinding scheme |

### Integrations

| Component | Technology | Purpose |
|---|---|---|
| Git | **GitPython** | Repository integration (history, commits, decision association) |
| Code Editors | **LSP + VS Code API** | LSP for Neovim/JetBrains; VS Code API for native VS Code extension |
| CI/CD | **GitHub Actions + GitLab CI** | GitHub Actions for repo; GitLab CI support for users |
| Cloud | **Multi-cloud** (AWS, GCP, Azure) | Support for multiple providers; provider-agnostic architecture |
| Collaboration | **WebSocket + SSH** (5+ users from MVP) | WebSocket for general sessions (pub/sub architecture); SSH for secure enterprise sessions |
| Plugin Marketplace | **Django** | Plugin upload, search, payment API; ORM, admin, auth built-in |

## Business Model

### Free Version (Open-Source)

- 3 predefined agents (Code Generator, Code Reviewer, Test Generator)
- Free models (CodeLlama 7B, Mistral 7B) via OpenRouter
- Local mode with small models (llama-2-7b)
- Basic TUI (no advanced inline editing)
- Limited history (last 100 interactions)
- No real-time collaboration

### Premium Plans

| Plan | Price | Features |
|---|---|---|
| Pro | $10/mes | All agents, premium models (Mixtral 8x7B, GPT-4, Claude 3), unlimited sandbox, advanced TUI, unlimited history, collaboration (3 users) |
| Team | $25/mes/user | Everything in Pro + priority support, IDE integration, custom workflows, collaboration (10 users) |
| Enterprise | Custom | Everything in Team + on-premise deployment, 24/7 support, internal tool integration, custom agents |

### Plugin Marketplace (Django)

- Creators publish agents/plugins (free or paid)
- 10% commission on plugin sales
- First 1,000 downloads/month free for creators

### Payment Processing

- **Stripe**: Subscriptions (Pro/Team/Enterprise), plugin marketplace commissions
- **PayPal**: One-time plugin purchases, alternative payment method

### Optional: boskoll Cloud

- Hosted version at $20/mes
- Access to shared GPUs for large models

## Roadmap

### Phase 1: MVP (3-6 months)

Backend CLI, basic TUI with Textual, model manager with auto-switching (OpenRouter + Ollama), 3 agents (Code Generator, Code Reviewer, Test Generator), sandbox execution (Docker), local storage (SQLite), complete documentation.

### Phase 2: Expansion (6-12 months)

Autonomous workflows, execution sandbox, test agent, DevOps agent, advanced TUI, Git integration, local mode (Ollama), collaboration scaling (10+ users).

### Phase 3: Maturity (12-18 months)

Plugin marketplace, specialized agents (Blockchain, Security, AI/ML), advanced collaboration (10+ users), IDE integration, productivity metrics, no-code mode, monetization.

### Phase 4: Scalability (18+ months)

On-premise deployment, 24/7 support, enterprise tool integration (Jira, GitLab, Slack), custom enterprise agents, boskoll Cloud.

## Glossary

**Agent**
: A modular, domain-specific AI component pre-trained by boskoll that performs a focused task (e.g., code generation, security scanning). Agents are internal to boskoll.
_Use when_: referring to individual AI specialists that ship with boskoll.
_Avoid_: bot, assistant, helper

**Autonomous Workflow**
: A multi-step task decomposition and execution flow that runs without human intervention (except critical decisions).
_Use when_: describing multi-agent orchestration.
_Avoid_: pipeline, automation

**Sandbox**
: An isolated execution environment (Docker/Firecracker) where generated code is validated before being shown to the user.
_Use when_: referring to code execution and validation.
_Avoid_: environment, container

**TUI (Terminal User Interface)**
: The interactive terminal-based interface for boskoll with syntax highlighting, inline editing, and divisible panels.
_Use when_: referring to the user-facing interface.
_Avoid_: CLI interface, terminal UI

**Net Productivity**
: The real impact of boskoll on development workflow — measured by time saved, code quality improvement, and bug reduction.
_Use when_: discussing measurable outcomes.
_Avoid_: efficiency, speed

**Plugin**
: A user-developed or community-contributed extension that extends boskoll's capabilities. Plugins can contain agents, workflows, or both. They live in the marketplace.
_Use when_: referring to community-contributed extensions and marketplace.
_Avoid_: extension, module

**Context Memory**
: Persistent storage of project decisions, architecture choices, and conversation history associated with Git commits.
_Use when_: referring to project knowledge persistence.
_Avoid_: history, cache
