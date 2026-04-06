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
  <a href="#how-to-use-it">How To Use It</a>
  &nbsp;·&nbsp;
  <a href="#commands">Commands</a>
  &nbsp;·&nbsp;
  <a href="#architecture">Architecture</a>
</p>

---

## The Problem

LLMs don't remember you. Every conversation starts from zero. You repeat your name, your preferences, your project context -- every single time.

Existing memory solutions send your data to the cloud, require a database server, or store it as raw text with no versioning and no way to handle contradictions when your information changes.

## What Memora Is

Memora is a **local-first memory layer** that sits transparently between you and Ollama. It captures conversations automatically, extracts human-readable memories, and stores them with Git-style versioning -- all on your machine.

No database. No Docker. No cloud. No LLM required for storage.

### The Core Idea

**Every memory is stored as a human-readable string.** Not a machine-format triple. Not a JSON blob. A plain English sentence that a person can read by opening any stored object file.

When you say *"My name is Sarah, I work at Microsoft, I prefer Python"*, Memora stores:

```
User's name is Sarah
User works at Microsoft
User prefers Python
```

Not `user.name = "Sarah"`. Not `{"entity": "user", "attribute": "name", "value": "Sarah"}`. Just readable text, compressed and content-addressed, versioned like Git commits.

### What Changed in v3.0

The entire codebase was rebuilt from the ground up:

| Before (v2.0) | After (v3.0) |
|---|---|
| Entity-attribute-value triples | Human-readable memory strings |
| Manual `memora commit` required | Auto-commit on session close |
| NER output polluted memory store | NER feeds knowledge graph instead |
| 708-line translation layer to make triples readable | Deleted -- content is already readable |
| Index layer was a 509-line stub | 4 real incremental indices (word, temporal, session, type) |
| No session concept | Full session lifecycle (open → accumulate → close → commit) |
| Branch limits unbounded | Configurable limits with auto-creation |
| 35+ dead files, stubs, TODOs | Zero dead code. Zero stubs. Zero TODOs. |
| Basic dashboard with colors | Pure black/white, monospace, minimal |

**24 Python source files remain. Every one of them does real work.**

## How It Works

```
You chat with Ollama
    ↓
Transparent proxy captures every message
    ↓
Type Detector classifies: conversation / code / document / file
    ↓
Type-specific extractor produces human-readable memories
    ↓
NER entities → Knowledge Graph (not memory store)
    ↓
Indices updated incrementally (word, temporal, session, type)
    ↓
Session accumulates memories
    ↓
You close Ollama → session closes → auto-commit fires
    ↓
Git-style commit with descriptive message
    ↓
Branch pointer updated
```

The entire process is invisible. You never run `memora commit`. You never think about versioning. It just works.

## How To Use It

### Step 1: Install

```bash
git clone https://github.com/withmemora/memora.git
cd memora
poetry install
poetry run python -m spacy download en_core_web_sm
```

### Step 2: Initialize

```bash
poetry run memora init
```

This creates a `.memora/` directory with Git-style object storage.

### Step 3: Start the Proxy

```bash
poetry run memora proxy start
```

The proxy runs on port 11435 and forwards everything to Ollama on 11434. Keep this terminal open.

### Step 4: Route Ollama Through Memora

**Windows (PowerShell):**
```powershell
$env:OLLAMA_HOST='http://localhost:11435'
```

**Mac/Linux:**
```bash
export OLLAMA_HOST=http://localhost:11435
```

This tells Ollama to talk through Memora's proxy. All conversations are captured automatically.

### Step 5: Chat Normally

```bash
ollama run llama3.2:3b
```

Now talk to the LLM like you normally would. Tell it things about yourself:

```
You: My name is Sarah. I live in Seattle and work at Microsoft.
You: I prefer Python over JavaScript. I always use black for formatting.
You: I'm building a project called Memora with my friend Marcus.
```

You don't need to do anything special. Memories are captured automatically.

### Step 6: Check What Was Captured

```bash
# Search for specific memories
poetry run memora search "Microsoft"

# View all statistics
poetry run memora stats

# See the full timeline
poetry run memora search ""
```

### Step 7: Open the Dashboard

```bash
poetry run python -c "from memora.interface.server import start_server; start_server()"
```

Then open **http://localhost:8000/dashboard** in your browser. You'll see four panels:

- **Profile** -- Assembled from the knowledge graph (works at, languages, tools, knows, building)
- **Timeline** -- Chronological list of all captured memories
- **Branch** -- Current branch size, session count, limits
- **Graph** -- Knowledge graph nodes and edges

### Step 8: Manage Sessions and Branches

```bash
# See active and closed sessions
poetry run memora session list

# See all branches and their status
poetry run memora branch status

# Create a new branch for a different context
poetry run memora branch create work
poetry run memora branch switch work
```

### Step 9: Forget Something

If you said something you don't want stored:

```bash
# Find the memory ID from search or dashboard
poetry run memora search "Sarah"

# Delete it
poetry run memora forget mem_abc123
```

This removes the memory from the object store, all indices, the active session, and the knowledge graph.

### Step 10: Export Everything

```bash
# Export as Markdown
poetry run memora export --format md

# Export as JSON
poetry run memora export --format json

# Export as plain text
poetry run memora export --format txt
```

### Step 11: Ingest Documents

```bash
# Ingest a single file
poetry run memora ingest architecture.md

# Ingest a directory
poetry run memora ingest docs/
```

Memories are extracted from the document and stored just like conversation memories.

## Commands

### Core

| Command | Description |
|---------|-------------|
| `memora init` | Initialize memory repository |
| `memora setup` | Interactive setup wizard |
| `memora version` | Show version |
| `memora stats` | Show memory statistics |
| `memora where` | Show storage location |

### Memory

| Command | Description |
|---------|-------------|
| `memora search "query"` | Search memories |
| `memora forget <id>` | Delete a specific memory |
| `memora ingest <file>` | Extract memories from a file |
| `memora export --format md\|json\|txt` | Export all memories |

### Sessions

| Command | Description |
|---------|-------------|
| `memora session list` | List all sessions |
| `memora session active` | Show active session |

### Branches

| Command | Description |
|---------|-------------|
| `memora branch list` | List all branches |
| `memora branch status` | Branch size vs limits |
| `memora branch create <name>` | Create a new branch |
| `memora branch switch <name>` | Switch to a branch |

### Graph

| Command | Description |
|---------|-------------|
| `memora graph` | Show knowledge graph summary |
| `memora graph query <entity>` | Query an entity in the graph |

### Proxy

| Command | Description |
|---------|-------------|
| `memora proxy start` | Start the Ollama proxy |
| `memora proxy stop` | Stop the proxy |
| `memora proxy status` | Check proxy status |
| `memora proxy-setup enable` | Set OLLAMA_HOST system-wide |
| `memora proxy-setup disable` | Remove OLLAMA_HOST |

### Other

| Command | Description |
|---------|-------------|
| `memora chat` | Interactive AI chat with memory context |
| `memora rollback <commit>` | Roll back to a previous commit |

## Architecture

```
src/memora/
├── shared/
│   ├── models.py              # Memory, Session, GraphNode, GraphEdge
│   └── exceptions.py          # Custom exceptions
├── core/
│   ├── engine.py              # CoreEngine orchestrator
│   ├── store.py               # ObjectStore with LRU cache
│   ├── ingestion.py           # Type-aware extraction pipeline
│   ├── session.py             # Session lifecycle
│   ├── graph.py               # Knowledge graph
│   ├── index.py               # 4 incremental indices
│   ├── branch_manager.py      # Branch limits + auto-creation
│   ├── conflicts.py           # String-based conflict detection
│   ├── refs.py                # Git-style branch pointers
│   ├── type_detector.py       # Detect input type
│   └── extractors/
│       ├── conversation.py    # Pattern matching → readable strings
│       ├── code.py            # Code block extraction
│       └── document.py        # Document/file extraction
├── ai/
│   ├── ollama_proxy.py        # HTTP proxy with session management
│   ├── file_processor.py      # Multi-format file ingestion
│   └── conversational_ai.py   # Ollama chat with context
└── interface/
    ├── cli.py                 # CLI commands (Typer)
    ├── server.py              # REST API (FastAPI)
    └── api.py                 # MemoraStore facade
```

**24 Python source files. Zero dead code. Zero stubs. Zero TODOs.**

### Storage

```
.memora/
├── objects/          # Content-addressable store (SHA-256 + zlib)
├── refs/heads/       # Branch pointers
├── HEAD              # Current branch
├── sessions/         # Session lifecycle (active/ + closed/)
├── graph/            # Knowledge graph (nodes.json + edges.json)
├── index/            # 4 indices (words, temporal, sessions, types)
├── branches/         # Branch size tracking
├── conflicts/        # Open + resolved
└── config            # All settings
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

# Lint
poetry run ruff check src/ tests/

# Format
poetry run ruff format src/ tests/

# Type check
poetry run mypy src/memora/

# Build
poetry build
```

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
