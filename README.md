<div align="center">

# ⚡ Zero Action

**Think Less. Build More.**

AI Development Partner CLI — from idea to production, all from the terminal.

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-80%20passed-brightgreen)](#testing)
[![Ruff](https://img.shields.io/badge/linter-ruff-orange)](https://docs.astral.sh/ruff/)
[![Mypy](https://img.shields.io/badge/types-mypy-blue)](https://mypy-lang.org/)

</div>

---

## What is Zero Action?

Zero Action is a **CLI-first AI Development Partner** that understands your entire project — reads your repository, remembers architectural decisions, generates code, reviews it, fixes issues, and helps you ship production-quality software.

It is **not** a simple code autocomplete. It is a combination of:

- 🏗️ **Software Architect** — plans your folder structure, ERDs, APIs
- 🧑‍💻 **Senior Engineer** — generates production-ready, fully typed code
- 🔍 **Code Reviewer** — analyses security, performance, maintainability
- 🔧 **Auto-Fixer** — patches issues with a diff preview before writing
- 🧠 **Memory System** — remembers decisions across sessions
- 🌐 **Provider Agnostic** — works with any AI: OpenAI, Gemini, Claude, Ollama, and more

---

## Features

| Feature | Command |
|---|---|
| Scan & understand the current repo | `zero init` |
| Configure AI provider | `zero setup` |
| Ask a one-shot question | `zero ask` |
| Interactive chat with memory | `zero chat` |
| Generate a PRD | `zero plan` |
| Design a system architecture | `zero architect` |
| Generate source code files | `zero code` |
| AI code review (security, perf, etc.) | `zero review` |
| Fix code from error or review report | `zero fix` |
| Manage memory (sessions, decisions) | `zero memory` |
| Manage AI providers | `zero provider` |
| View / update config | `zero config` |

---

## Installation

### Requirements

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`

### Install with uv

```bash
git clone https://github.com/your-org/zero-action.git
cd zero-action
uv sync
```

### Run

```bash
uv run zero --help
```

### Install globally (optional)

```bash
uv pip install -e .
zero --help
```

---

## Quick Start

### 1. Set up your AI provider

```bash
zero setup
```

Supports: **OpenAI**, **Anthropic**, **Gemini**, **OpenRouter**, **Groq**, **Mistral**, **Azure OpenAI**, **DeepSeek**, **Ollama**, and any OpenAI-compatible endpoint.

### 2. Scan your project

```bash
cd your-project/
zero init
```

Zero Action reads your folder structure, languages, dependencies, Docker setup, and Git history to build a repository context used by all subsequent AI commands.

### 3. Plan → Architect → Code → Review → Fix

```bash
# Generate a PRD from your idea
zero plan --requirements "Build a REST API for a task management app"

# Design the system architecture
zero architect

# Generate code based on the architecture
zero code --requirements "Implement the task model and CRUD endpoints"

# Review the generated code
zero review --file src/tasks/routes.py --output docs/review.md

# Fix issues found in the review
zero fix --file src/tasks/routes.py --review docs/review.md
```

---

## Command Reference

### `zero init`
Scans the current working directory and caches repository context (languages, frameworks, dependencies, Git info).

### `zero setup`
Interactive wizard to configure an AI provider (name, API key, base URL, model). Tests the connection before saving.

### `zero ask`
Single-shot question with full repository context.
```bash
zero ask --question "What framework does this project use?"
```

### `zero chat`
Interactive conversation loop with persistent session memory.
```bash
zero chat
```

### `zero plan`
Generate a Product Requirement Document (PRD) in Markdown.
```bash
zero plan --requirements "SaaS billing system with Stripe"
zero plan --output docs/prd.md
```

### `zero architect`
Generate a system architecture design document.
```bash
zero architect --requirements "Microservices with FastAPI and PostgreSQL"
zero architect --output docs/architecture.md
```
Auto-loads `docs/prd.md` if no `--requirements` given.

### `zero code`
Generate source code files from requirements and specs.
```bash
zero code --requirements "Implement the User model with SQLAlchemy"
zero code --spec docs/architecture.md --output src/models/user.py
```
Auto-loads `docs/prd.md` and `docs/architecture.md` if present.  
The AI can declare the output file with `File: path/to/output.py` — prompts before overwriting.

### `zero review`
AI code review covering security, performance, maintainability, scalability, and readability.
```bash
zero review --file src/app.py
zero review --dir src/ --output docs/review.md
zero review --file src/app.py --focus security,performance
```

### `zero fix`
Fix a source file from an error, a review report, or a plain instruction. Always shows a diff and asks for confirmation before writing.
```bash
zero fix --file src/app.py --error "TypeError: unsupported operand"
zero fix --file src/app.py --review docs/review.md
zero fix --file src/app.py --instruction "Add input validation to all endpoints"
zero fix --file src/app.py --error "..." --output src/app_fixed.py
```

### `zero provider`
Manage AI providers.
```bash
zero provider list
zero provider add
zero provider switch openai
zero provider test
zero provider models
zero provider remove groq
```

### `zero memory`
Manage project memory stored in SQLite.
```bash
zero memory sessions list
zero memory decisions add --content "Use PostgreSQL over SQLite for production"
zero memory knowledge import docs/architecture.md
```

### `zero config`
View and update configuration values.
```bash
zero config show
zero config set app.debug true
```

---

## AI Provider Support

| Provider | Type | Notes |
|---|---|---|
| OpenAI | Cloud | GPT-4o, GPT-4, GPT-3.5 |
| Anthropic | Cloud | Claude 3.5 Sonnet, Haiku |
| Google Gemini | Cloud | Gemini 1.5 Pro/Flash |
| OpenRouter | Cloud | Access to 100+ models |
| Groq | Cloud | Ultra-fast inference |
| Mistral | Cloud | mistral-large, codestral |
| Azure OpenAI | Cloud | Enterprise deployments |
| DeepSeek | Cloud | deepseek-coder, deepseek-chat |
| Ollama | Local | llama3, mistral, codellama, etc. |
| Any OpenAI-compatible | Custom | Provide base URL + model |

API keys are stored locally in `~/.zero/providers.toml` and never sent to third parties.

---

## Configuration

All configuration lives in `~/.zero/`:

```
~/.zero/
├── config.toml       # App settings (debug, log level)
├── providers.toml    # Provider configs and API keys
├── settings.toml     # User preferences
├── memory.db         # SQLite memory database
├── logs/             # Rotating log files
└── sessions/         # Chat session history
```

Override the config directory:
```bash
ZERO_HOME=/custom/path zero --help
```

---

## Architecture

Zero Action follows a **modular, domain-driven architecture** with strict separation of concerns:

```
zero/
├── cli/          # Typer CLI layer — commands only, no business logic
├── services/     # AI, config, and logging services
├── repository/   # Scanner, language detector, Git analyser, etc.
├── memory/       # Session, project, decision, knowledge managers
├── providers/    # LiteLLM-backed provider abstraction
├── prompts/      # Markdown prompt templates (planner, architect, coder…)
├── storage/      # SQLite wrapper
├── core/         # Shared exceptions and utilities
└── models/       # Pydantic data models
```

### Prompt Templates

All AI behaviour is driven by Markdown templates in `zero/prompts/`:

| File | Purpose |
|---|---|
| `planner.md` | PRD structure and format rules |
| `architect.md` | Architecture document format rules |
| `coder.md` | Code generation rules (no placeholders, typed, documented) |
| `reviewer.md` | 7-section review format (security → readability) |
| `fixer.md` | Surgical fix rules (raw code output, preserve unrelated logic) |

Templates are plain Markdown — customise them directly to change AI behaviour.

---

## Development

### Run tests
```bash
uv run pytest
uv run pytest -v                          # verbose
uv run pytest tests/cli/test_fix_command.py  # single file
```

### Static analysis
```bash
uv run ruff check zero tests              # lint
uv run mypy zero tests --ignore-missing-imports  # type check
```

### Auto-fix lint issues
```bash
uv run ruff check --fix zero tests
```

---

## Testing

The test suite covers 80 cases across unit and CLI integration tests:

| Module | Tests |
|---|---|
| Config system | 8 |
| AI service | 2 |
| Logging | 2 |
| Memory subsystem | 5 |
| Provider layer | 5 |
| Repository intelligence | 9 |
| SQLite storage | 3 |
| CLI — init, setup, version, verify | 6 |
| CLI — ask & chat | 2 |
| CLI — plan | 1 |
| CLI — architect | 1 |
| CLI — code | 6 |
| CLI — review | 10 |
| CLI — fix | 8 |
| CLI — provider | 4 |
| CLI — memory | 3 |
| CLI — config | 4 |

---

## Project Philosophy

- **Plan before code** — always understand before implementing
- **Human in control** — AI never writes to disk without explicit confirmation
- **Provider agnostic** — swap any model without changing commands
- **Local first** — works fully offline with Ollama
- **Modular** — every layer is independently testable and replaceable
- **No vendor lock-in** — open formats (TOML, SQLite, Markdown)

---

## License

MIT © Zero Action Team
