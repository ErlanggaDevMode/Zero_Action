# TECH.md

# Zero Action Technology Stack

Version: 1.0.0

Status: Draft

---

# 1. Overview

Zero Action dibangun sebagai **CLI-first AI Development Partner** dengan arsitektur modular, extensible, dan provider-agnostic. Semua komponen dirancang agar dapat diganti atau diperluas tanpa memengaruhi bagian lain dari sistem.

## Design Goals

* CLI First
* Cross Platform
* AI Provider Agnostic
* Local AI Friendly
* Fast Startup
* Modular
* Plugin Ready
* Async First
* Open Source
* Easy Maintenance

---

# 2. Core Technology

| Layer           | Technology        |
| --------------- | ----------------- |
| Language        | Python 3.12+      |
| Package Manager | uv                |
| Build System    | pyproject.toml    |
| CLI Framework   | Typer             |
| Terminal UI     | Rich              |
| Async Runtime   | asyncio           |
| Configuration   | Pydantic Settings |
| Serialization   | TOML + JSON       |
| Logging         | Loguru            |
| Testing         | pytest            |
| Documentation   | Markdown          |

---

# 3. Programming Language

## Python

Python dipilih karena:

* Cross-platform
* Ekosistem AI terbesar
* Dukungan async yang matang
* Banyak library untuk CLI
* Mudah dikembangkan komunitas

Minimum Version

```text
Python 3.12+
```

---

# 4. Package Management

Menggunakan **uv**.

Alasan:

* Sangat cepat
* Lock file modern
* Pengganti pip
* Pengganti virtualenv
* Resolusi dependency lebih baik

Contoh:

```bash
uv sync
uv add typer
uv run zero
```

---

# 5. CLI Framework

Menggunakan **Typer**.

Alasan:

* Dibangun di atas Click
* Type Hint
* Auto Help
* Auto Completion
* Mudah dikembangkan

Command Example

```bash
zero setup
zero chat
zero review
zero doctor
```

---

# 6. Terminal UI

Menggunakan **Rich**.

Digunakan untuk:

* Table
* Tree
* Progress
* Spinner
* Markdown
* Code Highlight
* Panel
* Prompt
* Status

Contoh:

* Setup Wizard
* Progress Repository Scan
* Provider Status
* AI Streaming

---

# 7. AI Abstraction Layer

Menggunakan **LiteLLM**.

Alasan:

* Mendukung banyak provider
* API seragam
* Mudah mengganti provider
* Streaming
* Tool Calling
* Embeddings

Provider yang didukung:

* OpenAI
* Anthropic
* Google Gemini
* OpenRouter
* Groq
* Mistral
* Azure OpenAI
* DeepSeek
* Ollama
* OpenAI-Compatible API

---

# 8. AI Provider Architecture

Semua provider harus mengimplementasikan interface berikut:

```python
connect()
chat()
stream()
embeddings()
health_check()
list_models()
token_count()
```

Zero Action tidak berinteraksi langsung dengan provider, tetapi melalui abstraction layer.

---

# 9. Supported Providers

## Cloud

* OpenAI
* Anthropic
* Gemini
* OpenRouter
* Groq
* Mistral
* Azure OpenAI
* Together AI
* DeepSeek

---

## Local

* Ollama
* LM Studio
* LocalAI
* vLLM
* llama.cpp Server
* Text Generation WebUI

---

## Custom

Provider apa pun yang kompatibel dengan OpenAI API.

User hanya perlu memasukkan:

* Base URL
* API Key
* Model

---

# 10. Configuration System

Menggunakan:

Pydantic Settings

Format konfigurasi:

TOML

Lokasi:

```text
~/.zero/
```

Struktur:

```text
config.toml
providers.toml
settings.toml
```

---

# 11. Secrets Management

API Key tidak disimpan dalam source code.

Disimpan secara lokal.

Dukungan:

* Environment Variable
* .env
* Local Config
* OS Keyring (future)

---

# 12. Local Database

Menggunakan SQLite.

Digunakan untuk:

* Memory
* Session
* Prompt History
* Provider Cache
* Command History

Alasan:

* Tidak memerlukan server
* Cepat
* Cross Platform

---

# 13. Memory System

Memory dibagi menjadi:

## Session Memory

Percakapan aktif.

---

## Project Memory

Informasi repository.

---

## Global Memory

Preferensi user.

---

## Decision Memory

Keputusan arsitektur.

---

## Knowledge Memory

Dokumentasi yang telah dipelajari.

---

# 14. Vector Database

Opsional.

Menggunakan ChromaDB.

Digunakan untuk:

* Repository Search
* Documentation Search
* Semantic Search
* Context Retrieval

Fallback:

Tanpa ChromaDB, sistem tetap berjalan menggunakan pencarian berbasis file.

---

# 15. Context Engine

Menganalisis:

* Folder
* File
* README
* Git
* Docker
* Package Manager
* Framework
* Dependency
* Configuration

Menghasilkan context yang digunakan AI.

---

# 16. Repository Scanner

Scanner mendeteksi:

* Python
* JavaScript
* TypeScript
* Java
* Go
* Rust
* PHP
* C#
* Docker
* Kubernetes
* Terraform

---

# 17. Git Integration

Menggunakan GitPython.

Fitur:

* Status
* Branch
* Commit
* Diff
* Log
* Blame
* Checkout
* Tag

---

# 18. Prompt Engine

Semua prompt disimpan sebagai file Markdown.

Contoh:

```text
prompts/
├── planner.md
├── architect.md
├── coder.md
├── reviewer.md
├── debugger.md
├── tester.md
├── documentation.md
├── devops.md
└── master.md
```

Keuntungan:

* Mudah dikustomisasi
* Mudah diuji
* Tidak di-hardcode

---

# 19. Template Engine

Menggunakan Jinja2.

Digunakan untuk:

* README
* PRD
* API Docs
* Dockerfile
* GitHub Actions
* Changelog

---

# 20. Logging

Menggunakan Loguru.

Log disimpan berdasarkan kategori:

* CLI
* Provider
* AI
* Memory
* Git
* Error
* Plugin

Level:

* DEBUG
* INFO
* WARNING
* ERROR
* CRITICAL

---

# 21. Testing Framework

Menggunakan pytest.

Jenis pengujian:

* Unit Test
* Integration Test
* CLI Test
* Provider Test
* Regression Test

Coverage Target

> 90%

---

# 22. Static Analysis

Menggunakan:

* Ruff
* Black
* isort
* mypy

Tujuan:

* Konsistensi kode
* Type Safety
* Format otomatis
* Deteksi bug dini

---

# 23. Documentation

Semua dokumentasi menggunakan Markdown.

Struktur:

```text
docs/
README.md
PRD.md
TECH.md
STRUCTURE.md
COMMANDS.md
AI_PROVIDERS.md
ARCHITECTURE.md
SECURITY.md
```

---

# 24. Packaging

Menggunakan:

pyproject.toml

Distribusi:

* pip
* uv
* GitHub Release

Future:

* Homebrew
* Scoop
* Winget
* AUR

---

# 25. Plugin System

Plugin memiliki lifecycle:

* Install
* Enable
* Disable
* Update
* Remove

Plugin dapat menambahkan:

* Command
* AI Provider
* Prompt
* Tool
* Workflow

---

# 26. Tool System

Setiap tool memiliki interface:

```python
name()
description()
execute()
validate()
```

Contoh Tool:

* File Reader
* File Writer
* Git
* Terminal
* Search
* Replace
* Documentation

Future:

* Browser
* Docker
* Kubernetes
* GitHub
* Database

---

# 27. Async Architecture

Menggunakan asyncio.

Semua operasi berikut berjalan asynchronous:

* AI Streaming
* Repository Scan
* Provider Connection
* File Reading
* Plugin Loading

---

# 28. Error Handling

Jenis Error:

* ProviderError
* NetworkError
* ConfigError
* ValidationError
* PluginError
* MemoryError
* ToolError

Semua error memiliki pesan yang informatif dan solusi yang disarankan.

---

# 29. Security

Prinsip:

* Never expose API keys
* No telemetry by default
* Local-first data storage
* Explicit user confirmation for destructive actions
* Sandboxed tool execution (future)

---

# 30. Performance Targets

Startup CLI: < 2 detik

Repository Scan: < 10 detik

Provider Switch: < 3 detik

Memory Load: < 2 detik

Command Parsing: < 100 ms

Streaming Latency: mengikuti provider

---

# 31. Cross Platform Support

Didukung:

* Windows 10/11
* macOS
* Linux (Ubuntu, Debian, Fedora, Arch)

Shell:

* PowerShell
* CMD
* Bash
* Zsh
* Fish

---

# 32. CI/CD

Continuous Integration:

* GitHub Actions

Pipeline:

1. Lint
2. Type Check
3. Unit Test
4. Integration Test
5. Build Package
6. Publish Release

---

# 33. Coding Standards

Mengikuti prinsip:

* SOLID
* DRY
* KISS
* YAGNI
* Composition over Inheritance
* Explicit is better than implicit (PEP 20)

Semua kode harus memiliki type hints, dokumentasi publik, dan struktur modul yang konsisten.

---

# 34. Future Technology Roadmap

## Phase 1

* CLI Foundation
* Provider Abstraction
* Configuration System

## Phase 2

* Context Engine
* Memory Engine
* Repository Scanner

## Phase 3

* Multi-Agent Orchestrator
* Tool Calling
* Workflow Engine

## Phase 4

* Plugin Marketplace
* MCP Integration
* Remote Execution

## Phase 5

* Distributed Agent
* Collaborative Sessions
* Web Dashboard
* Mobile Companion

---

# 35. Technology Principles

1. Semua dependensi harus memiliki alasan yang jelas.
2. Hindari vendor lock-in dengan abstraction layer.
3. Prioritaskan teknologi open source.
4. Dukung model AI lokal dan cloud secara setara.
5. Seluruh sistem harus modular dan dapat diuji.
6. Konfigurasi tidak boleh di-hardcode.
7. Semua komponen harus dapat diganti tanpa mengubah arsitektur inti.

---

# 36. Final Technology Statement

Zero Action dibangun sebagai platform AI Development Partner yang modern, ringan, dan modular. Dengan memanfaatkan Python, Typer, Rich, LiteLLM, serta arsitektur provider-agnostic, sistem mampu beradaptasi dengan perkembangan model AI dan kebutuhan developer tanpa mengorbankan performa, keamanan, maupun kemudahan pengembangan. Seluruh teknologi dipilih berdasarkan prinsip kesederhanaan, interoperabilitas, dan keberlanjutan jangka panjang.
