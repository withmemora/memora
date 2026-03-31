# Memora

<p align="center">
  <img src="Assets/logo.svg" alt="memora" width="300" />
</p>

<p align="center">
  <strong>Git-style versioned memory for any LLM.</strong>
</p>

<p align="center">
  <a href="https://memora-website-tan.vercel.app/">Product Site</a>
  &nbsp;·&nbsp;
  <a href="#quick-start">Quick Start</a>
  &nbsp;·&nbsp;
  <a href="#commands">Commands</a>
  &nbsp;·&nbsp;
  <a href="#architecture">Architecture</a>
</p>

---

## What Is Memora?

LLMs don't remember you between conversations. Memora fixes that.

Memora sits between you and your LLM (Ollama or any other) and automatically extracts facts from every conversation. It stores them as structured, versioned, searchable memories -- all locally on your machine. Think of it as Git for your LLM's memory: every fact is hashed, every change is committed, every contradiction is detected, and you can branch memories by context just like code.

**Key capabilities:**

- **Automatic memory capture** -- intercepts Ollama conversations and extracts facts without any manual effort
- **Versioned storage** -- every memory change is committed with full history, like Git
- **Conflict detection** -- catches contradictions (e.g., "I live in NYC" vs "I live in LA") and resolves them
- **Branch-based organization** -- separate memories by project, persona, or context
- **Document ingestion** -- extract memories from TXT, Markdown, and PDF files
- **Local-first** -- nothing leaves your machine, no cloud dependencies
- **REST API + Dashboard** -- programmatic access and a web UI for browsing memories

## Quick Start

### 1. Install

```bash
git clone https://github.com/withmemora/memora.git
cd memora
poetry install
poetry run python -m spacy download en_core_web_sm
```

### 2. Initialize

```bash
poetry run memora init
```

### 3. Start Using It

**Option A -- Interactive chat with memory:**
```bash
poetry run memora chat
```

**Option B -- Automatic capture via Ollama proxy:**
```bash
poetry run memora proxy start --background
# Then set OLLAMA_HOST=http://localhost:11435 and use Ollama normally
```

**Option C -- Add memories manually:**
```bash
poetry run memora add "My name is John. I work at Google."
poetry run memora search "John"
```

**Option D -- Web dashboard:**
```bash
poetry run python -c "from memora.interface.server import start_server; start_server()"
# Open http://localhost:8000/dashboard
```

## Commands

### Memory

| Command | Description |
|---------|-------------|
| `memora add "text"` | Add a memory from text |
| `memora search "query"` | Search memories |
| `memora stats` | Show memory statistics |
| `memora chat` | Interactive chat with memory context |

### Branches

| Command | Description |
|---------|-------------|
| `memora branch list` | List all branches |
| `memora branch create <name>` | Create a new branch |
| `memora branch switch <name>` | Switch to a branch |
| `memora branch delete <name>` | Delete a branch |

### Documents

| Command | Description |
|---------|-------------|
| `memora ingest file.txt` | Extract memories from a file |
| `memora ingest docs/ --recursive` | Process a directory of files |

### Proxy (Ollama Integration)

| Command | Description |
|---------|-------------|
| `memora proxy start` | Start the Ollama proxy |
| `memora proxy start --background` | Run as background daemon |
| `memora proxy status` | Check proxy status |
| `memora proxy stop` | Stop the proxy |

### Setup

| Command | Description |
|---------|-------------|
| `memora init` | Initialize memory storage |
| `memora setup` | Interactive setup wizard |
| `memora version` | Show version |

## How It Works

### The Core Idea

When you talk to an LLM, Memora extracts structured facts from the conversation:

```
"My name is Sarah. I live in Seattle and work at Microsoft. I prefer Python."
```

Becomes:

| Entity | Attribute | Value | Confidence |
|--------|-----------|-------|------------|
| user | name | Sarah | 0.95 |
| user | location | Seattle | 0.92 |
| user | employer | Microsoft | 0.95 |
| user | preference | Python | 0.90 |

Each fact gets a SHA-256 hash, is stored in a content-addressable object store, and is committed with version tracking. When you later say "I moved to Portland," Memora detects the conflict with "Seattle" and flags it for resolution.

### The NLP Pipeline

Memora uses a 5-stage extraction pipeline:

1. **Text normalization** -- splits input into sentences using spaCy
2. **Pattern matching** -- 20+ regex rules for first-person statements ("My name is...", "I work at...", "I prefer...")
3. **Named Entity Recognition** -- spaCy NER detects people, organizations, locations, dates
4. **Code extraction** -- detects code blocks, function definitions, class declarations
5. **Deduplication** -- identical facts from different sources collapse into one

### Storage Architecture

```
memora_data/
└── .memora/
    ├── objects/          # Content-addressable fact store (SHA-256)
    │   ├── ab/
    │   │   └── cdef1234...  # Compressed fact data
    │   └── cd/
    │       └── ef567890...
    ├── refs/heads/       # Branch pointers (like Git refs)
    │   ├── main
    │   └── work
    ├── HEAD              # Current branch reference
    ├── staging/          # Facts pending commit
    ├── conflicts/        # Detected contradictions
    │   ├── open/
    │   └── resolved/
    └── index/            # Performance indices
```

### Branch Isolation

Each branch has its own commit chain. Facts added on one branch don't appear on another until you switch. This lets you maintain separate memory contexts -- work projects, personal info, different LLM personas -- without cross-contamination.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Interfaces                        │
│  CLI (Typer)  │  REST API (FastAPI)  │  Dashboard   │
├─────────────────────────────────────────────────────┤
│                    AI Layer                          │
│  Ollama Proxy  │  Chat Engine  │  File Processor    │
├─────────────────────────────────────────────────────┤
│                   Core Engine                        │
│  Ingestion Pipeline  │  Object Store  │  Conflicts  │
│  Branch Management   │  Commits       │  Search     │
├─────────────────────────────────────────────────────┤
│                   Shared Models                      │
│  Fact  │  MemoryTree  │  MemoryCommit  │  Conflict  │
└─────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| NLP | spaCy 3.7+ (en_core_web_sm) |
| CLI | Typer + Rich |
| API | FastAPI + Uvicorn |
| LLM Interface | Ollama Python SDK |
| Validation | Pydantic 2.7+ |
| File Processing | chardet, markdown, PyPDF2 |
| Testing | pytest, pytest-cov |
| Linting | Ruff |
| Type Checking | mypy |
| Dependency Management | Poetry |

## Prerequisites

- Python 3.11 or higher
- [Poetry](https://python-poetry.org/docs/#installation)
- [Ollama](https://ollama.ai/) (optional, for LLM integration)

## Development

```bash
# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src/memora --cov-report=html

# Lint
poetry run ruff check src/ tests/

# Format
poetry run ruff format src/ tests/

# Type check
poetry run mypy src/memora/

# Build package
poetry build
```

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `OLLAMA_HOST` | Ollama endpoint | `http://localhost:11434` |
| `MEMORA_MEMORY_PATH` | Memory storage path | `./memora_data` |
| `MEMORA_PROXY_PORT` | Proxy port | `11435` |
| `MEMORA_LOG_LEVEL` | Logging verbosity | `INFO` |

## License

MIT
