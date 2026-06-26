# STRUCTURE.md

# Zero Action Project Structure

Version: 1.0.0

Status: Draft

---

# 1. Overview

Zero Action menggunakan arsitektur **modular**, **domain-driven**, dan **plugin-ready**. Setiap modul memiliki tanggung jawab yang jelas (Single Responsibility Principle) sehingga mudah dipelihara, diuji, dan dikembangkan.

Prinsip utama struktur proyek:

* Modular
* Extensible
* Testable
* Provider Agnostic
* Plugin Friendly
* Separation of Concerns

---

# 2. Project Layout

```text
zero-action/
│
├── zero/                      # Main application package
│
├── docs/                      # Project documentation
│
├── tests/                     # Automated tests
│
├── scripts/                   # Development scripts
│
├── examples/                  # Example projects
│
├── plugins/                   # Built-in plugins
│
├── pyproject.toml
├── README.md
├── LICENSE
└── CHANGELOG.md
```

---

# 3. Main Application

```text
zero/
│
├── __init__.py
├── __main__.py
├── version.py
│
├── cli/
├── core/
├── providers/
├── agents/
├── memory/
├── repository/
├── prompts/
├── tools/
├── plugins/
├── workflow/
├── config/
├── storage/
├── utils/
├── services/
└── models/
```

---

# 4. CLI Layer

```text
cli/
│
├── app.py
├── parser.py
├── context.py
├── completion.py
│
├── commands/
│   ├── init.py
│   ├── setup.py
│   ├── chat.py
│   ├── ask.py
│   ├── plan.py
│   ├── architect.py
│   ├── code.py
│   ├── review.py
│   ├── fix.py
│   ├── docs.py
│   ├── deploy.py
│   ├── provider.py
│   ├── memory.py
│   ├── doctor.py
│   ├── config.py
│   ├── plugin.py
│   └── update.py
```

## Responsibility

* Parse command
* Parse options
* Help
* Validation
* Dispatch command

CLI tidak boleh berisi business logic.

---

# 5. Core Layer

```text
core/
│
├── orchestrator.py
├── planner.py
├── architect.py
├── coder.py
├── reviewer.py
├── debugger.py
├── tester.py
├── documentation.py
├── deployment.py
└── workflow.py
```

## Responsibility

Mengatur logika utama aplikasi.

Semua command akan memanggil modul ini.

---

# 6. Provider Layer

```text
providers/
│
├── base.py
├── manager.py
├── registry.py
│
├── openai.py
├── anthropic.py
├── gemini.py
├── openrouter.py
├── groq.py
├── mistral.py
├── ollama.py
├── azure.py
├── deepseek.py
└── compatible.py
```

## Responsibility

Semua komunikasi dengan AI provider.

Semua provider wajib mengimplementasikan interface yang sama.

---

# 7. Agent Layer

```text
agents/
│
├── planner.py
├── architect.py
├── coder.py
├── reviewer.py
├── debugger.py
├── tester.py
├── documentation.py
├── devops.py
└── manager.py
```

## Responsibility

Setiap agent memiliki spesialisasi.

Planner Agent

Architect Agent

Coder Agent

Reviewer Agent

QA Agent

Documentation Agent

DevOps Agent

Manager Agent

---

# 8. Workflow Layer

```text
workflow/
│
├── planning.py
├── coding.py
├── review.py
├── testing.py
├── deployment.py
└── pipeline.py
```

Workflow menggabungkan beberapa agent menjadi satu proses.

Contoh:

Plan

↓

Architect

↓

Coder

↓

Reviewer

↓

Tester

↓

Documentation

---

# 9. Memory Layer

```text
memory/
│
├── manager.py
├── session.py
├── project.py
├── global.py
├── decision.py
├── knowledge.py
└── embeddings.py
```

Jenis memory:

Session

Project

Global

Decision

Knowledge

---

# 10. Repository Layer

```text
repository/
│
├── scanner.py
├── analyzer.py
├── dependency.py
├── language.py
├── git.py
├── docker.py
├── framework.py
└── summary.py
```

Repository Scanner membaca:

Folder

README

Package

Docker

Git

Framework

Language

Dependency

---

# 11. Prompt Layer

```text
prompts/
│
├── master.md
├── planner.md
├── architect.md
├── coder.md
├── reviewer.md
├── debugger.md
├── tester.md
├── documentation.md
├── devops.md
└── setup.md
```

Prompt disimpan sebagai Markdown agar mudah dikustomisasi.

---

# 12. Tool Layer

```text
tools/
│
├── base.py
├── registry.py
│
├── file_reader.py
├── file_writer.py
├── search.py
├── replace.py
├── git.py
├── shell.py
├── markdown.py
├── json.py
├── yaml.py
└── terminal.py
```

Semua tool menggunakan interface yang sama.

---

# 13. Plugin Layer

```text
plugins/
│
├── loader.py
├── registry.py
├── installer.py
├── validator.py
└── manager.py
```

Plugin dapat menambahkan:

* Command
* Tool
* Provider
* Workflow
* Prompt
* Agent

---

# 14. Services Layer

```text
services/
│
├── ai.py
├── git.py
├── config.py
├── provider.py
├── memory.py
├── project.py
├── logging.py
└── cache.py
```

Service digunakan oleh Core Layer.

---

# 15. Storage Layer

```text
storage/
│
├── sqlite.py
├── vector.py
├── cache.py
└── history.py
```

Digunakan untuk:

SQLite

Cache

Vector

History

---

# 16. Models Layer

```text
models/
│
├── provider.py
├── message.py
├── project.py
├── repository.py
├── task.py
├── workflow.py
└── memory.py
```

Semua model menggunakan Pydantic.

---

# 17. Utils Layer

```text
utils/
│
├── paths.py
├── filesystem.py
├── process.py
├── env.py
├── formatting.py
├── hashing.py
├── terminal.py
└── validation.py
```

Utility tidak boleh memiliki business logic.

---

# 18. Configuration Directory

Disimpan di:

```text
~/.zero/
```

Isi:

```text
~/.zero/

config.toml

providers.toml

settings.toml

memory.db

cache/

history/

logs/

sessions/

plugins/

embeddings/
```

---

# 19. Documentation Structure

```text
docs/

README.md

PRD.md

TECH.md

STRUCTURE.md

COMMANDS.md

CONFIG.md

AI_PROVIDERS.md

MEMORY.md

AGENTS.md

WORKFLOW.md

SECURITY.md

CONTRIBUTING.md

ROADMAP.md

CHANGELOG.md
```

---

# 20. Tests Structure

```text
tests/

unit/

integration/

cli/

provider/

workflow/

repository/

memory/

plugin/

fixtures/
```

Target Coverage:

90%

---

# 21. Examples

```text
examples/

python/

flask/

fastapi/

react/

nextjs/

django/

java/

golang/
```

Digunakan untuk testing dan demonstrasi.

---

# 22. Built-in Plugins

```text
plugins/

docker/

github/

gitlab/

markdown/

python/

javascript/

react/

fastapi/

django/
```

---

# 23. Configuration Flow

CLI

↓

Load Config

↓

Load Provider

↓

Load Memory

↓

Load Plugin

↓

Load Context

↓

Execute Command

↓

Save State

---

# 24. AI Request Flow

User

↓

CLI

↓

Command

↓

Core

↓

Workflow

↓

Agent

↓

Provider

↓

LLM

↓

Response

↓

Memory

↓

Output

---

# 25. Repository Analysis Flow

Repository

↓

Scanner

↓

Dependency Detector

↓

Framework Detector

↓

Language Detector

↓

Git Analyzer

↓

Summary Builder

↓

Context Memory

↓

AI

---

# 26. Plugin Lifecycle

Install

↓

Validate

↓

Register

↓

Enable

↓

Execute

↓

Update

↓

Disable

↓

Remove

---

# 27. Provider Lifecycle

Setup

↓

Health Check

↓

Authentication

↓

Model Discovery

↓

Streaming Test

↓

Ready

---

# 28. Command Lifecycle

User Command

↓

Argument Parser

↓

Validation

↓

Configuration

↓

Provider

↓

Workflow

↓

AI

↓

Memory

↓

Logging

↓

Output

---

# 29. Dependency Rules

CLI hanya boleh memanggil Core.

Core tidak boleh mengetahui implementasi CLI.

Provider tidak boleh mengetahui Agent.

Agent tidak boleh mengetahui CLI.

Tool tidak boleh mengetahui Provider.

Plugin hanya boleh menggunakan Public API.

Semua komunikasi dilakukan melalui interface.

---

# 30. Naming Convention

Folder:

snake_case

Python File:

snake_case.py

Class:

PascalCase

Function:

snake_case()

Constant:

UPPER_CASE

Private:

_prefix

---

# 31. Architectural Principles

* Single Responsibility Principle
* Dependency Inversion Principle
* Interface-based Design
* Composition over Inheritance
* Modular Architecture
* Feature Isolation
* Configuration over Hardcoding
* Provider Abstraction
* Plugin-first Extension
* Test-first Development

---

# 32. Scalability Strategy

Struktur dirancang agar fitur baru dapat ditambahkan tanpa mengubah modul yang sudah ada.

Contoh:

Menambah AI provider baru hanya memerlukan implementasi interface pada folder `providers/` dan registrasi ke `ProviderManager`.

Menambah command baru cukup membuat file baru di `cli/commands/` dan menghubungkannya ke `core/` tanpa memengaruhi command lain.

---

# 33. Future Structure

```text
zero/

mcp/

telemetry/

marketplace/

voice/

remote/

cloud/

collaboration/

dashboard/

analytics/
```

Folder tersebut disiapkan untuk pengembangan jangka panjang tanpa mengubah struktur inti proyek.

---

# 34. Final Structure Statement

Struktur Zero Action dirancang mengikuti prinsip **Clean Architecture** dengan pemisahan yang tegas antara antarmuka (CLI), logika bisnis (Core), integrasi eksternal (Providers dan Tools), penyimpanan (Storage dan Memory), serta ekstensi (Plugins). Pendekatan ini memastikan proyek tetap mudah dipelihara, mudah diuji, dan mampu berkembang menjadi platform AI Development Partner berskala besar tanpa kehilangan konsistensi arsitektur.
