# Changelog

All notable changes to Zero Action are documented here.

---

## [1.0.0] — 2026-06-26

### Added

#### Core Infrastructure
- `pyproject.toml` — packaging, entry point, dependency declarations
- `zero/cli/app.py` — Typer application with `--debug` / `--verbose` flags and `CliContext`
- `zero/core/exceptions.py` — `ZeroError`, `ConfigError`, `ProviderError` hierarchy
- `zero/cli/context.py` — typed `CliContext` dataclass for CLI→service boundary

#### Services Layer
- `zero/services/config.py` — TOML-backed configuration manager with Pydantic Settings
- `zero/services/logging.py` — Loguru logging router with per-category file sinks and secret masking
- `zero/services/ai.py` — `AIService` wrapping LiteLLM; builds system prompt from cached repo context

#### Repository Intelligence
- `zero/repository/scanner.py` — file traverser with `.gitignore` support via `pathspec`
- `zero/repository/language.py` — extension-based language classifier
- `zero/repository/dependency.py` — manifest parser (pyproject.toml, package.json, go.mod, Cargo.toml, etc.)
- `zero/repository/framework.py` — framework detector (FastAPI, Django, Flask, React, Vue, Next.js, etc.)
- `zero/repository/docker.py` — Docker/Compose presence detection
- `zero/repository/git.py` — GitPython-backed commit count, branch, and author metrics
- `zero/repository/analyzer.py` — orchestrator producing unified `RepositorySummary`

#### Database & Memory
- `zero/storage/sqlite.py` — parameterised SQLite wrapper with foreign-key enforcement
- `zero/memory/manager.py` — top-level `MemoryManager` aggregating all memory types
- `zero/memory/session.py` — session (conversation) memory
- `zero/memory/project.py` — project-scoped key/value memory
- `zero/memory/decision.py` — architectural decision records
- `zero/memory/global.py` — user-global preference memory
- `zero/memory/knowledge.py` — document knowledge base

#### Provider Layer
- `zero/providers/base.py` — `BaseProvider` interface (`chat`, `stream`, `embeddings`, `health_check`, `list_models`)
- `zero/providers/manager.py` — provider registry and factory
- Provider implementations: OpenAI, Anthropic, Gemini, OpenRouter, Groq, Mistral, Azure, DeepSeek, Ollama, Compatible

#### CLI Commands
- `zero init` — repository scan and context caching
- `zero setup` — interactive AI provider wizard with connection test
- `zero ask` — single-shot question with repo context
- `zero chat` — interactive conversation loop with session memory
- `zero plan` — AI-generated PRD from requirements; auto-loads `docs/prd.md`
- `zero architect` — AI-generated architecture design; auto-loads `docs/prd.md`
- `zero code` — source file generation; spec auto-discovery; `File:` header protocol; overwrite protection
- `zero review` — structured code review: security, performance, maintainability, scalability, readability; `--focus` filter; batch `--dir` mode
- `zero fix` — surgical AI fix with unified diff preview; confirmation required before write; `--error` / `--review` / `--instruction` inputs
- `zero provider` — list, add, remove, switch, test, models subcommands
- `zero memory` — sessions, decisions, knowledge subcommands
- `zero config` — show, set subcommands
- `zero version` — version and environment info
- `zero verify` — config and logging health check

#### Prompt Templates
- `zero/prompts/planner.md` — PRD structure guidelines
- `zero/prompts/architect.md` — architecture document format guidelines
- `zero/prompts/coder.md` — code generation rules (production-ready, no placeholders, typed)
- `zero/prompts/reviewer.md` — 7-section structured review format
- `zero/prompts/fixer.md` — surgical fix rules (raw code output, preserve unrelated logic)

#### Test Suite
- 80 pytest cases across unit and CLI integration tests
- Coverage: config, AI service, logging, memory, providers, repository, SQLite, all CLI commands

---

## Roadmap

### [1.1.0] — Planned
- `zero docs` — automated README and API documentation generation
- `zero doctor` — system diagnostics and health check command
- `zero deploy` — deployment assistant (Dockerfile, GitHub Actions, etc.)

### [1.2.0] — Planned
- Plugin system (`zero plugin install / list / remove`)
- `zero update` — self-update command
- Vector embeddings for semantic repository search (ChromaDB)

### [2.0.0] — Future
- Multi-agent orchestrator (Planner → Architect → Coder → Reviewer pipeline)
- Web dashboard companion
- MCP (Model Context Protocol) integration
- Distributed agent sessions
