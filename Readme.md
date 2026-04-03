# Memora

<p align="center">
  <img src="Assets/logo.svg" alt="memora" width="300" />
</p>

<p align="center">
  <strong>Local-first, Git-style AI memory for Ollama.</strong>
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

Existing solutions either send your data to the cloud, require a database server, or store it as raw text with no versioning and no way to resolve contradictions.

## The Solution

Memora is a **local-first, versioned memory system** that sits transparently between you and Ollama. It captures conversations automatically, extracts human-readable memories, builds a knowledge graph, and stores everything with Git-style versioning -- all on your machine, no database required.

Think of it as Git for your LLM's memory. But instead of code, it tracks what you've told the AI about yourself.

## Key Features

- **Automatic Memory Capture** -- Transparent HTTP proxy captures every Ollama conversation without changing your workflow
- **Session Lifecycle & Auto-Commit** -- Sessions open on first chat, close on disconnect, and auto-commit with descriptive messages
- **Human-Readable Storage** -- Memories are stored as natural language strings, not machine-format triples
- **Knowledge Graph** -- NER entities become graph nodes (people, orgs, locations, tech) with relationship edges
- **Versioned Storage** -- Every change is committed with full history, like Git commits
- **Branch-Based Organization** -- Separate memories by project, persona, or context with auto-creation at size limits
- **Selective Forgetting** -- `memora forget <id>` removes any memory from all stores
- **Document Ingestion** -- Extract memories from TXT, Markdown, and PDF files
- **Local-First** -- Nothing leaves your machine, no cloud, no database, no Docker
- **REST API + 4-Panel Dashboard** -- Programmatic access and a web UI with Profile, Timeline, Branch, and Graph panels
- **Code Intelligence** -- Detects and stores code snippets with language, function names, and summaries

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
# Start the proxy
poetry run memora proxy start

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
| `memora version` | Show version (3.0.0) |
| `memora search "query"` | Search memories |
| `memora stats` | Show memory statistics |
| `memora where` | Show storage location |

### Memory Operations

| Command | Description |
|---------|-------------|
| `memora ingest file.txt` | Extract memories from a file |
| `memora forget <memory_id>` | Delete a specific memory (selective forgetting) |
| `memora export --format json\|md\|txt` | Export all memories |

### Session Management

| Command | Description |
|---------|-------------|
| `memora session list` | List all sessions |
| `memora session active` | Show active session |

### Branch Management

| Command | Description |
|---------|-------------|
| `memora branch list` | List all branches |
| `memora branch status` | Current branch size vs limits |
| `memora branch create <name>` | Create a new branch |
| `memora branch switch <name>` | Switch to a branch |

### Knowledge Graph

| Command | Description |
|---------|-------------|
| `memora graph` | Show knowledge graph summary |
| `memora graph query <entity>` | Show what the graph knows about an entity |

### Proxy Management

| Command | Description |
|---------|-------------|
| `memora proxy start` | Start the Ollama proxy |
| `memora proxy stop` | Stop the proxy |
| `memora proxy status` | Check proxy status |
| `memora proxy-setup enable` | Configure OLLAMA_HOST system-wide |
| `memora proxy-setup disable` | Remove OLLAMA_HOST |

## How It Works

### Memory Extraction

When you talk to an LLM, Memora extracts human-readable memories from the conversation:

```
Input: "My name is Sarah. I live in Seattle and work at Microsoft. I prefer Python."
```

Becomes structured memories:

| Memory Content | Type | Confidence |
|----------------|------|------------|
| User's name is sarah | conversation | 0.95 |
| User lives in seattle | conversation | 0.92 |
| User works at Microsoft | conversation | 0.95 |

Named entities (Sarah, Seattle, Microsoft) are sent to the **knowledge graph**, not the memory store -- eliminating junk facts from your dashboard.

### The Extraction Pipeline

Memora uses a type-aware extraction pipeline:

1. **Type Detection** -- Classifies input as conversation, code, document, or file
2. **Type-Specific Extraction:**
   - **Conversation:** Pattern matching → human-readable strings (20+ regex rules)
   - **Code:** Language detection, function/class extraction, summary generation
   - **Document:** Key fact extraction, filename tracking, word count
3. **Named Entity Recognition** -- spaCy NER feeds the knowledge graph (not memory store)
4. **Index Updates** -- Word, temporal, session, and type indices updated incrementally
5. **Graph Updates** — NER entities added as nodes with relationship edges

### Session Lifecycle

Sessions replace manual commits entirely:

```
1. First Ollama request → opens a session
2. Every chat message → accumulates memories into the session
3. User disconnects or 15min silence → session closes
4. Auto-commit fires → creates Git commit with descriptive message
   → e.g. "lives in seattle, works at microsoft, name is sarah"
5. User never runs `memora commit` — it's completely invisible
```

The 15-minute timeout is based on **last activity**, not start time. Every request resets the clock, so a user who pauses mid-conversation to make coffee won't trigger a timeout.

### Storage Architecture

```
memora_data/
└── .memora/
    ├── objects/          # Content-addressable memory store (SHA-256 + zlib)
    │   ├── ab/
    │   │   └── cdef1234...  # Compressed memory object
    │   └── cd/
    │       └── ef567890...
    ├── refs/heads/       # Branch pointers (like Git refs)
    │   ├── main
    │   ├── main-2        # Auto-created when main hits limit
    │   └── work
    ├── HEAD              # Current branch reference
    ├── sessions/         # Session lifecycle
    │   ├── active/       # Open sessions
    │   └── closed/       # Completed sessions (auto-committed)
    ├── graph/            # Knowledge graph
    │   ├── nodes.json    # Entity nodes (person, org, location, tech)
    │   └── edges.json    # Relationship edges
    ├── index/            # 4 real incremental indices
    │   ├── words.json    # word → [memory_ids]
    │   ├── temporal.json # date → [memory_ids]
    │   ├── sessions.json # session_id → [memory_ids]
    │   └── types.json    # memory_type → [memory_ids]
    ├── branches/
    │   └── meta.json     # Branch size tracking
    ├── conflicts/        # Detected contradictions
    │   ├── open/
    │   └── resolved/
    └── config            # All settings
```

### Knowledge Graph

The graph tracks entities and relationships separately from memories:

```
[User] --works_at--> [Microsoft]
[User] --lives_in--> [Seattle]
[User] --knows--> [Sarah]
```

The dashboard's Profile Card is assembled from graph data, showing works at, languages, tools, knows, and building at a glance.

### Conflict Resolution

When you update information, Memora detects and resolves conflicts:

```
Day 1: "I live in New York"    → Stored
Day 30: "I live in Portland"   → Conflict detected!
Result: TEMPORAL_SUPERSESSION → Portland wins (newer)
```

### Branch Management with Auto-Creation

Branches have configurable limits (100 sessions, 5000 memories, 90 days). When a limit is hit:

1. Current branch status → "full"
2. New branch auto-created (main → main-2)
3. Context inheritance: new branch inherits from the **entire predecessor chain** (main-3 → main-2 → main)
4. The branch boundary is transparent to both user and LLM

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Interfaces                        │
│  CLI (Typer)  │  REST API (FastAPI)  │  Dashboard   │
├─────────────────────────────────────────────────────┤
│                    AI Layer                          │
│  Ollama Proxy  │  Chat Engine  │  File Processor    │
│  Type Detector │  Extractors  │  Conversational AI │
├─────────────────────────────────────────────────────┤
│                   Core Engine                        │
│  Ingestion Pipeline  │  Object Store (LRU cached)  │
│  Session Manager     │  Auto-Commit                │
│  Knowledge Graph     │  4 Incremental Indices      │
│  Branch Manager      │  Conflict Detection         │
├─────────────────────────────────────────────────────┤
│                   Shared Models                      │
│  Memory  │  Session  │  GraphNode  │  GraphEdge    │
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

### Project Structure

```
src/memora/
├── shared/
│   ├── models.py          # Memory, Session, GraphNode, GraphEdge dataclasses
│   └── exceptions.py      # Custom exceptions
├── core/
│   ├── engine.py          # CoreEngine orchestrator
│   ├── store.py           # ObjectStore with LRU cache
│   ├── ingestion.py       # Type-aware extraction pipeline
│   ├── session.py         # Session lifecycle (open → accumulate → close)
│   ├── graph.py           # Knowledge graph (nodes, edges, profile)
│   ├── index.py           # 4 real indices (word, temporal, session, type)
│   ├── branch_manager.py  # Branch limits + auto-creation + chain inheritance
│   ├── conflicts.py       # String-based conflict detection
│   ├── refs.py            # Git-style branch pointers
│   ├── type_detector.py   # Detect input type
│   └── extractors/
│       ├── conversation.py  # Pattern matching → human-readable strings
│       ├── code.py          # Code block extraction with language detection
│       └── document.py      # Document/file memory extraction
├── ai/
│   ├── ollama_proxy.py      # HTTP proxy with session management
│   ├── file_processor.py    # Multi-format file ingestion
│   └── conversational_ai.py # Ollama chat with context injection
└── interface/
    ├── cli.py               # CLI commands (Typer)
    ├── server.py            # REST API (FastAPI, 20+ endpoints)
    └── api.py               # MemoraStore facade
```

**24 Python source files. Zero dead code. Zero stubs. Zero TODOs.**

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `OLLAMA_HOST` | Ollama endpoint | `http://localhost:11434` |
| `MEMORA_MEMORY_PATH` | Memory storage path | `./memora_data` |
| `MEMORA_PROXY_PORT` | Proxy port | `11435` |
| `MEMORA_LOG_LEVEL` | Logging verbosity | `INFO` |

## What Makes It Different

| | Memora | Mem0 | Memoria |
|---|---|---|---|
| Requires database | No | Yes | Yes (MatrixOne) |
| Requires Docker | No | No | Yes |
| Requires LLM for storage | No | Yes | No |
| Git versioning | Native | No | Via DB |
| 100% local files | Yes | No | No |
| Auto-commit on session end | Yes | No | No |
| Branch size limits | Yes | No | No |
| Knowledge graph | Yes | No | No |
| Human-readable storage | Yes | No | No |
| Selective forgetting | Yes | No | No |
| Dead code / stubs | Zero | N/A | N/A |

## License

Apache-2.0
