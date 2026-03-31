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
  <a href="#how-it-works">How It Works</a>
</p>

---

## The Problem

Large Language Models are powerful, but they have a fundamental limitation: **they don't remember you**. Every conversation starts from scratch. You repeat your preferences, your context, your project details -- over and over.

Existing solutions either send your data to the cloud or store it as raw text with no structure, no versioning, and no way to resolve contradictions when your information changes.

## The Solution

Memora is a local, versioned memory system that sits between you and your LLM. It automatically extracts facts from conversations, stores them as structured data with full version history, detects contradictions, and retrieves relevant context when you need it.

Think of it as Git for your LLM's memory -- but instead of code, it tracks what you've told the AI about yourself.

## Key Features

- **Automatic Memory Capture** -- Intercepts Ollama conversations and extracts facts without manual effort
- **Versioned Storage** -- Every change is committed with full history, like Git commits
- **Conflict Detection** -- Catches contradictions (e.g., "I live in NYC" vs "I live in LA") and resolves them automatically
- **Branch-Based Organization** -- Separate memories by project, persona, or context
- **Document Ingestion** -- Extract memories from TXT, Markdown, and PDF files
- **Local-First** -- Nothing leaves your machine, no cloud dependencies
- **REST API + Dashboard** -- Programmatic access and a web UI for browsing memories
- **Code Intelligence** -- Detects and stores code snippets, function definitions, and class declarations

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [Poetry](https://python-poetry.org/docs/#installation)
- [Ollama](https://ollama.ai/) (optional, for LLM integration)

### Installation

```bash
# Clone the repository
git clone https://github.com/withmemora/memora.git
cd memora

# Install dependencies
poetry install

# Download the spaCy English language model
poetry run python -m spacy download en_core_web_sm

# Initialize memory storage
poetry run memora init
```

### Usage

**Option 1: Interactive Setup (Recommended)**
```bash
poetry run memora setup
```
The setup wizard checks for Ollama, initializes storage, and guides you through configuration.

**Option 2: Automatic Memory Capture via Proxy**
```bash
# Start the proxy in background
poetry run memora proxy start --background

# Route Ollama through Memora proxy
# Windows PowerShell:
$env:OLLAMA_HOST='http://localhost:11435'
# Mac/Linux:
export OLLAMA_HOST=http://localhost:11435

# Use Ollama normally -- memories are captured automatically
ollama run llama3.2:3b

# Check captured memories
poetry run memora search ""
```

**Option 3: Interactive Chat with Memory**
```bash
poetry run memora chat
```

**Option 4: Web Dashboard**
```bash
poetry run python -c "from memora.interface.server import start_server; start_server()"
# Open http://localhost:8000/dashboard
```

## Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `memora init` | Initialize memory repository |
| `memora setup` | Interactive setup wizard |
| `memora version` | Show version |

### Memory Operations

| Command | Description |
|---------|-------------|
| `memora add "text"` | Add a memory from text |
| `memora search "query"` | Search memories |
| `memora stats` | Show memory statistics |
| `memora chat` | Interactive chat with memory context |

### Branch Management

| Command | Description |
|---------|-------------|
| `memora branch list` | List all branches |
| `memora branch create <name>` | Create a new branch |
| `memora branch switch <name>` | Switch to a branch |
| `memora branch delete <name>` | Delete a branch |

### Document Ingestion

| Command | Description |
|---------|-------------|
| `memora ingest file.txt` | Extract memories from a file |
| `memora ingest docs/ --recursive` | Process a directory of files |

### Proxy Management

| Command | Description |
|---------|-------------|
| `memora proxy start` | Start the Ollama proxy |
| `memora proxy start --background` | Run as background daemon |
| `memora proxy status` | Check proxy status |
| `memora proxy stop` | Stop the proxy |

## How It Works

### Fact Extraction

When you talk to an LLM, Memora extracts structured facts from the conversation:

```
Input: "My name is Sarah. I live in Seattle and work at Microsoft. I prefer Python."
```

Becomes structured facts:

| Entity | Attribute | Value | Confidence |
|--------|-----------|-------|------------|
| user | name | Sarah | 0.95 |
| user | location | Seattle | 0.92 |
| user | employer | Microsoft | 0.95 |
| user | preference | Python | 0.90 |

### The NLP Pipeline

Memora uses a 5-stage extraction pipeline:

1. **Text Normalization** -- Splits input into sentences using spaCy
2. **Pattern Matching** -- 20+ regex rules for first-person statements ("My name is...", "I work at...", "I prefer...")
3. **Named Entity Recognition** -- spaCy NER detects people, organizations, locations, dates
4. **Code Extraction** -- Detects code blocks, function definitions, class declarations
5. **Deduplication** -- Identical facts from different sources collapse into one

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

### Conflict Resolution

When you update information, Memora detects and resolves conflicts automatically:

```
Day 1: "I live in New York"    → Stored as fact
Day 30: "I live in Portland"   → Conflict detected!
```

Memora applies a 4-policy resolution chain:
1. **Recency Policy** -- Newer fact wins if gap >= 7 days
2. **Confidence Policy** -- Higher confidence wins if difference >= 0.3
3. **Source Priority** -- Configurable source priority list
4. **Manual Review** -- Flags for human review when automatic resolution isn't possible

### Branch Isolation

Each branch maintains its own commit chain. Facts added on one branch don't appear on another until you switch. This enables:

- Separate work and personal memory contexts
- Different LLM personas with distinct knowledge
- Project-specific memory isolation
- Safe experimentation without affecting main memories

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

## Development

```bash
# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src/memora --cov-report=html

# Lint code
poetry run ruff check src/ tests/

# Format code
poetry run ruff format src/ tests/

# Type checking
poetry run mypy src/memora/

# Build distributable package
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
