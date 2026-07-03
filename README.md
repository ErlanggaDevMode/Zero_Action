<div align="center">

# Zero Action

**Think Less. Build More.**

AI Development Partner CLI — from raw idea to production release, all directly from your terminal.

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-95%20passed-brightgreen)](#testing)
[![Ruff](https://img.shields.io/badge/linter-ruff-orange)](https://docs.astral.sh/ruff/)
[![Mypy](https://img.shields.io/badge/types-mypy-blue)](https://mypy-lang.org/)

</div>

---

## 💡 What is Zero Action?

Zero Action is a **CLI-first AI Development Partner** designed to act as your Architect, Senior Engineer, Code Reviewer, and DevOps Lead directly inside your terminal. It scans your repository, maintains a persistent memory of architectural decisions in a local SQLite database, writes fully typed source code, and helps you ship pull requests automatically.

Unlike basic code autocomplete extensions, Zero Action acts as a full team:
- 🏗️ **Software Architect** — maps folder structures, designs DDL schemas, plans APIs, and graphs systems.
- 🧑‍💻 **Senior Engineer** — writes modular, clean, and fully typed code.
- 🔍 **QA & Security Reviewer** — scans for security flaws, performance bottlenecks, and code smells.
- 🔧 **Auto-Fixer & Self-Healer** — runs test suites, parses error tracebacks, drafts surgical fixes, and verifies them autonomously.
- 🧠 **Memory Engine** — preserves sessions, choices, and semantic vectors locally.
- 🌐 **Provider Agnostic** — works out-of-the-box with OpenAI, Gemini, Claude, Ollama, DeepSeek, and more.

---

## 🚀 Commands & Features

| Feature | Command | Description |
|---|---|---|
| **Scan & Index Repo** | `zero init` | Scan project directory and store semantic embeddings in SQLite. |
| **Setup Wizard** | `zero setup` | Interactive wizard to configure default AI endpoints. |
| **Instant Q&A** | `zero ask` | Query project codebase with full context. |
| **Interactive REPL** | `zero chat` | Persistent interactive console session inspired by Claude Code. |
| **Web Search** | `zero search` / `/search` | Search DuckDuckGo with *Google DNS-over-HTTPS (DoH) Bypass* (anti-censorship). |
| **Web Reader** | `zero read` / `/read` | Fetch clean webpage texts, stripping scripts and unescaping HTML entities. |
| **Product Manager** | `zero plan` | Generate a Product Requirements Document (`prd.md`). |
| **Architect Engine** | `zero architect` | Design system architectures based on requirements (`architecture.md`). |
| **Coding Engine** | `zero code` | Write source files matching the system design. |
| **QA Lead Review** | `zero review` | Inspect source files for security, performance, and style. |
| **Auto-Patch** | `zero fix` | Apply code fixes from review reports or errors with interactive diffs. |
| **QA Auto-Healer** | `zero test` / `/test` | Run linter/tests in the background and auto-heal tracebacks. |
| **DevOps Pilot** | `zero pr` / `/pr` | Draft Conventional Commits, check out branch, push, and open PRs. |
| **Memory Manager** | `zero memory` | Read and write SQLite tables (sessions, decisions, knowledge). |
| **Provider Control** | `zero provider` | List, add, switch, test, or remove AI models. |
| **System Config** | `zero config` | Show and set app settings (debug, logging levels). |
| **Schema Explorer** | `zero schema` / `/schema` | Static AST analysis of DB models and endpoints as a terminal tree. |
| **Refactor Wizard** | `zero refactor` / `/refactor` | AI-guided codebase refactoring with automatic test validation and git rollback on failure. |
| **Docker Pilot** | `zero docker` / `/docker` | Auto-detect environment, generate Dockerfiles, spin up containers, inspect logs, and auto-heal startup crashes. |
| **Voice Mode REPL** | `/voice` | Record mic, transcribe, process, and read response speech using local Whisper or API. |

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.12 or higher.
- [**`uv`**](https://docs.astral.sh/uv/) (Astral's fast Python package resolver).
- Git.

### Steps

First, clone the repository:
```bash
git clone https://github.com/ErlanggaDevMode/Zero_Action.git
cd Zero_Action
```

Choose **one** of the following methods to install and run Zero Action on your computer:

#### Method 1: Using `uv` (Recommended / Fastest)
Requires Astral's [**`uv`**](https://docs.astral.sh/uv/) installed.
```bash
# 1. Sync dependencies and build virtualenv automatically
uv sync

# 2. Run commands inside virtualenv
uv run zero setup
uv run zero chat
```

#### Method 2: Using standard Python `venv`
Create and activate a virtual environment manually:
```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# 3. Install package in editable mode with dependencies
pip install -e .

# 4. Run commands directly
zero setup
zero chat
```

#### Method 3: Using `pipx` (Cleanest for Global CLI Tool)
Install globally in an isolated environment without manual virtualenv activation:
```bash
# 1. Install globally from local repository
pipx install .

# 2. Run from anywhere on your system
zero setup
zero chat
```

---

### AI Provider Configuration
Zero Action is provider agnostic. You can configure your model settings using three methods:

#### Method A: Interactive Setup Wizard (Recommended)
Run the built-in configuration utility:
```bash
uv run zero setup
```
This utility lets you select your active provider, paste API keys, and configure default models interactively.

#### Method B: Manual config file edits
Configurations are saved under `~/.zero/providers.toml` (located at `C:\Users\<Name>\.zero\providers.toml` on Windows). Open this file and configure your active provider details:
```toml
[provider]
active_provider = "openrouter"

[provider.openrouter]
api_key = "sk-or-v1-your-key-here"
model = "openrouter/meta-llama/llama-3.3-70b-instruct"

[provider.openai]
api_key = "sk-proj-your-key-here"
model = "gpt-4o"
```

#### Method C: Environment Variables (CI/CD and automation)
You can define keys directly in your shell or a `.env` file in the workspace root. Prefix variables with `ZERO_PROVIDER__<PROVIDER_NAME>__`:
```bash
# Set active provider
export ZERO_PROVIDER__ACTIVE_PROVIDER="openrouter"

# Set provider details
export ZERO_PROVIDER__OPENROUTER__API_KEY="sk-or-v1-..."
export ZERO_PROVIDER__OPENROUTER__MODEL="openrouter/meta-llama/llama-3.3-70b-instruct"
```

---

## ⚡ Quick Start

### 1. Initialize local context
Inside your project directory, scan the codebase:
```bash
zero init
```
Zero Action reads project frameworks, dependencies, Dockerfiles, and Git history to build a local vector index in SQLite.

### 2. Standard Coding Workflow
```bash
# Generate a PRD from an idea
zero plan --requirements "Build a FastAPI JWT authentication microservice"

# Design system architecture
zero architect

# Write actual code matching the architecture
zero code

# Review code for security flaws
zero review --file zero/services/auth.py

# Auto-fix issues flagged in the review
zero fix --file zero/services/auth.py --review docs/review.md
```

### 3. Live Web Search & Documentation Ingestion
Search the web or read API specifications directly inside the active chat memory:
```text
# Launch REPL chat
zero chat

# Search DuckDuckGo (uses Google DoH bypass if blocked by local ISP)
zero-action > /search fastapi background tasks example

# Extract clean documentation text (unescapes HTML entities like &bull; -> •)
zero-action > /read https://fastapi.tiangolo.com/tutorial/background-tasks/

# Command the AI to code based on the freshly ingested web context
zero-action > Write a background task wrapper using the documentation above.
```

### 4. Advanced Otonom & Collaboration (Set 2)
```bash
# 📐 Visualise project schemas and endpoint maps
uv run zero schema

# 🔧 Agentic refactor modules with auto-tests check and git rollback on failure
uv run zero refactor --file zero/services/auth.py --instruction "Optimize token hash check performance" --attempts 3

# 🐳 DevOps Container Pilot: generate configs, build docker, check logs, and self-heal
uv run zero docker

# 🎙️ Voice Mode REPL: talk directly to terminal (uses local offline Whisper)
uv run zero chat
zero-action > /voice
```
> [!TIP]
> Always prefix commands with `uv run` to ensure python imports packages (like local offline `whisper`) from the project's local virtual environment instead of global system python scopes!

---

## 🎨 Premium UI & Latency Tracker
Zero Action features a world-class terminal interface:
- **Welcome Panel & Pixel-Logo:** Greets developers with a luxurious gold panel and high-fidelity crimson-outlined pixel logo rendered via Unicode half-blocks (`▀`).
- **TTFT Tracker:** Displays a dynamic dot spinner `⠋ Thinking (X.Xs)...` showing latency until the first response token is streamed.

---

## ⚙️ Directory Structure

```text
zero/
├── cli/          # 🖥️ CLI Layer: Parsing parameters & Typer routing. No business logic.
├── core/         # ⚙️ Shared Core: UI Spinner, custom terminal panels, Exceptions.
├── services/     # 🛠️ Services: Config manager (TOML), Logging, AI Wrapper, Web Search.
├── repository/   # 🔍 Repo Intel: Framework detector, Git metrics, package analyzer.
├── memory/       # 🧠 Memory: SQLite vector store, sessions, decisions managers.
├── providers/    # 🌐 Providers: LiteLLM abstract wrappers.
├── prompts/      # 📝 Prompts: System prompt Markdown templates (planner, coder, reviewer).
└── models/       # 📦 Data Models: Pydantic typed schemas.
```

---

## 🧪 Testing & Code Quality (QA)

Zero Action maintains **95 unit & integration tests** passing 100%.

```bash
# Run all tests
uv run pytest

# Check linter compliance (0 warnings enforced)
uv run ruff check zero tests

# Verify type safety
uv run mypy zero tests --ignore-missing-imports
```

---

## 📘 Documentation Guides
- **Manual Verification & Testing Scenarios:** Read [docs/panduan_fitur_lengkap.md](file:///c:/T/Zero_Action/docs/panduan_fitur_lengkap.md)
- **Product Feature Roadmap (56+ Advanced Features):** Read [update.md](file:///c:/T/Zero_Action/update.md)

---

## 📄 License

MIT © Zero Action Team
