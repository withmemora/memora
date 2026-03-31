# Memora

<p align="center">
  <img src="Assets/logo.svg" alt="memora" width="300" />
</p>

<p align="center">
  Git-style versioned memory for any LLM.
</p>

<p align="center">
  <a href="https://memora-website-tan.vercel.app/">Product Site</a>
</p>

---

## Overview

Memora is a persistent, versioned memory system for Large Language Models. It automatically captures, stores, and retrieves facts from your conversations with Ollama (or any LLM). Every fact is stored with a SHA-256 hash, organized into branches, and committed with full history tracking. Contradictions between facts are detected and resolved automatically. All data stays local -- nothing leaves your machine.

## Prerequisites

- Python 3.11 or higher
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management
- [Ollama](https://ollama.ai/) (optional, for LLM integration)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd Memora

# Install dependencies
poetry install

# Download the required spaCy English language model
poetry run python -m spacy download en_core_web_sm

# Initialize memory storage
poetry run memora init
```

## Quick Start

### Option 1: Interactive Setup (Recommended)

```bash
poetry run memora setup
```

The setup wizard checks for Ollama, initializes storage, and guides you through configuration.

### Option 2: Manual Setup with Proxy

```bash
# Start the proxy in background
poetry run memora proxy start --background

# Set environment variable to route Ollama through proxy
# Windows PowerShell:
$env:OLLAMA_HOST='http://localhost:11435'

# Mac/Linux:
export OLLAMA_HOST=http://localhost:11435

# Use Ollama normally -- memories are captured automatically
ollama run llama3.2:3b

# Check captured memories
poetry run memora search ""
```

## Commands

### Core Commands

```bash
# Initialize memory repository
poetry run memora init
poetry run memora init --path /custom/path

# Show version
poetry run memora version

# Interactive setup wizard
poetry run memora setup
```

### Memory Operations

```bash
# Add a memory manually
poetry run memora add "My name is John"
poetry run memora add "Project deadline is March 30" --source "meeting-notes"

# Search memories
poetry run memora search "Python programming"
poetry run memora search "project deadline" --limit 20

# View memory statistics
poetry run memora stats
```

### Chat with Memory

```bash
# Interactive chat with memory context
poetry run memora chat
poetry run memora chat --verbose              # Show memory extractions
poetry run memora chat --model llama3.2:3b    # Specify model
poetry run memora chat --branch work           # Use specific branch
```

### Document Ingestion

```bash
# Ingest a single document (TXT, MD, PDF)
poetry run memora ingest document.txt

# Ingest a directory recursively
poetry run memora ingest documents/ --recursive

# Ingest specific file types
poetry run memora ingest docs/ --file-types txt,md
```

### Branch Management

```bash
# List branches
poetry run memora branch list

# Create a new branch
poetry run memora branch create work-project

# Switch to a branch
poetry run memora branch switch personal

# Delete a branch
poetry run memora branch delete old-branch
```

### Proxy Management

```bash
# Start proxy (foreground)
poetry run memora proxy start

# Start proxy (background daemon)
poetry run memora proxy start --background

# Start proxy with custom port
poetry run memora proxy start --port 11436

# Check proxy status
poetry run memora proxy status

# Stop proxy
poetry run memora proxy stop
```

### API Server

```bash
# Start the FastAPI REST API server
poetry run python -c "from memora.interface.server import start_server; start_server()"

# Start with custom host/port
poetry run python -c "from memora.interface.server import start_server; start_server(host='0.0.0.0', port=8080)"
```

After starting the server:
- API documentation: `http://localhost:8000/docs`
- Web dashboard: `http://localhost:8000/dashboard`

## Development

### Testing

```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run with coverage report
poetry run pytest --cov=src/memora --cov-report=term --cov-report=html

# Run specific test file
poetry run pytest tests/core/test_store.py
```

### Code Quality

```bash
# Lint code
poetry run ruff check src/ tests/

# Format code
poetry run ruff format src/ tests/

# Type checking
poetry run mypy src/memora/
```

### Build for Distribution

```bash
# Build distributable package
poetry build

# Output: dist/memora-0.1.0-py3-none-any.whl
#         dist/memora-0.1.0.tar.gz
```

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `OLLAMA_HOST` | Routes Ollama through Memora proxy | `http://localhost:11434` |
| `MEMORA_HOME` | Custom repository location | `./memora_data` |
| `MEMORA_BRANCH` | Default branch override | `main` |
| `MEMORA_LOG_LEVEL` | Logging verbosity | `INFO` |
| `MEMORA_PROXY_PORT` | Proxy port override | `11435` |
| `MEMORA_MEMORY_PATH` | Path to memory storage | `./memora_data` |

## Architecture

Memora uses a three-layer architecture:

**Core Engine** (`src/memora/core/`)
- Content-addressable storage with SHA-256 hashing
- Git-style versioning with commits and branches
- Conflict detection and resolution
- NLP fact extraction pipeline using spaCy

**Interfaces** (`src/memora/interface/` and `src/memora/ai/`)
- CLI built with Typer
- REST API with FastAPI
- Ollama HTTP proxy for transparent memory capture
- File processor for TXT, MD, and PDF ingestion
- LangChain and LlamaIndex integrations

**Shared** (`src/memora/shared/`)
- Data models (Fact, MemoryTree, MemoryCommit, Conflict)
- Abstract interfaces and custom exceptions

## How Memory Storage Works

Memora stores facts as structured triples (entity, attribute, value) with SHA-256 content-addressable hashes. Each fact is deduplicated -- identical semantic content from different sources maps to the same hash. Facts are organized into memory trees and versioned through commits, similar to Git.

**Fact lifecycle:**
1. Text enters via CLI, chat, proxy, or file ingestion
2. NLP pipeline extracts structured facts using spaCy + pattern matching
3. Each fact gets a hash computed from entity + attribute + value only (metadata excluded)
4. Facts are written to content-addressable storage with zlib compression
5. Conflict detection runs against existing facts
6. Facts are staged and committed with parent pointers for version history

**Data retrieval:**
- `search` scans all fact objects in the store (not just current commit tree) to ensure nothing is missed
- The readable memory cache persists to disk between sessions
- Branches isolate memory contexts -- each branch has its own commit chain

## Tech Stack

- **Language:** Python 3.11+
- **Dependency Manager:** Poetry
- **NLP:** spaCy 3.7+ (en_core_web_sm)
- **CLI:** Typer 0.9+ with Rich
- **API:** FastAPI 0.119+, Uvicorn 0.30+
- **LLM Interface:** Ollama Python SDK 0.2+
- **Data Validation:** Pydantic 2.7+
- **File Processing:** chardet, markdown, PyPDF2
- **Testing:** pytest, pytest-cov, pytest-asyncio
- **Linting:** Ruff
- **Type Checking:** mypy

## License

MIT
