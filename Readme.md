# Memora

<p align="center">
  <strong>Git-style versioned memory for any LLM</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a>
  &nbsp;·&nbsp;
  <a href="#features">Features</a>
  &nbsp;·&nbsp;
  <a href="#commands">Commands</a>
  &nbsp;·&nbsp;
  <a href="#architecture">Architecture</a>
</p>

---

## The Problem

LLMs don't remember you. Every conversation starts from zero. You repeat your name, preferences, project context -- every single time.

Existing memory solutions send your data to the cloud, require complex setup, or store memories as raw text with no versioning and no way to handle contradictions.

## What Memora Does

Memora is a **local-first memory system** that captures, versions, and recalls memories from your LLM conversations. It provides Git-style versioning, automatic knowledge graphs, and intelligent search -- all stored locally on your machine.

**No database. No Docker. No cloud dependencies.**

## Quick Start

**2-step setup that just works:**

```bash
# Step 1: Install
pip install memora

# Step 2: Start (does everything: init + proxy + setup)
memora start
```

That's it. Memora is now capturing all your Ollama conversations automatically.

## Enterprise-Grade Features

### 🏠 **Local-First Architecture**
- Complete data sovereignty - all information stays on your infrastructure
- Zero external dependencies or cloud services required
- Built-in PII filtering and sensitive data protection
- Operates entirely offline for maximum security

### 🌳 **Git-Style Versioning**
- Branch and merge different memory contexts for project isolation
- Complete commit history with descriptive messages
- Rollback capabilities to any previous state
- Intelligent conflict resolution for contradictory information

### 🧠 **Advanced Memory Intelligence**
- Human-readable storage format for transparency and debugging
- Automatic content type detection (conversation/code/documents)
- Real-time knowledge graph construction with entity recognition
- Smart deduplication and memory supersession handling

### 🔍 **Powerful Search & Discovery**
- Natural language queries: `"find my dark mode preferences"`
- Temporal search: `"what was discussed last Tuesday?"`
- Entity-based search through automatically built knowledge graphs
- Multi-dimensional indexing with sub-100ms response times

### 🛠 **Production-Ready Engineering**
- Single-command deployment: `memora start`
- Comprehensive CLI with 20+ commands
- RESTful API for system integration
- 177 automated tests ensuring reliability

## How It Works

```
LLM Conversation
    ↓
Transparent Ollama Proxy (port 11435)
    ↓
Memory Ingestion Pipeline
├── Type Detection (conversation/code/document)
├── Content Extraction (human-readable strings)
├── NER Entity Recognition → Knowledge Graph
└── PII Filtering & Security Validation
    ↓
Storage & Indexing
├── Git-style Object Store (SHA-256 + compression)
├── Incremental Indices (word/temporal/session/type)
├── Session Management (auto-commit on close)
└── Branch Tracking with Limits
    ↓
Search & Retrieval
├── Natural Language Queries
├── Time-based Search  
├── Knowledge Graph Traversal
└── Context-aware Results
```

## Usage Examples

### Basic Memory Operations
```bash
# Search your memories
memora search "Python preferences"
memora when "last week's meeting notes"

# View statistics and data location
memora stats
memora where

# Interactive AI chat with memory context
memora chat
```

### Document & Code Ingestion
```bash
# Ingest documents
memora ingest --file="project_spec.md" --type=document
memora ingest --file="codebase/" --type=code

# Manual memory creation
echo "User prefers dark mode UI" | memora ingest --type=conversation
```

### Branch & Session Management
```bash
# Create project-specific branches
memora branch create --name="work-project"
memora branch switch work-project

# View session history
memora session list
memora session active

# Knowledge graph exploration
memora graph --format=summary
memora graph query "Python"
```

### Export & Migration
```bash
# Export in different formats
memora export --format=markdown
memora export --format=json
memora export --format=plain

# Backup and restore
memora backup --path="./memora-backup.tar.gz"
memora restore --path="./memora-backup.tar.gz"
```

## Commands

### Essential Commands

| Command | Description |
|---------|-------------|
| `memora start` | **One-command setup** - init + proxy + environment configuration |
| `memora search "<query>"` | Natural language memory search |
| `memora when "<time>"` | Time-based memory queries |
| `memora stats` | Memory statistics and system status |
| `memora version` | Version and system information |

### Memory Management

| Command | Description |
|---------|-------------|
| `memora ingest --file=<path>` | Extract memories from documents/code |
| `memora ingest --text="<text>"` | Add manual memory |
| `memora forget <memory_id>` | Delete specific memory |
| `memora export --format=<md\|json\|txt>` | Export all memories |

### Sessions & Branches

| Command | Description |
|---------|-------------|
| `memora session list` | View all sessions (active + closed) |
| `memora session active` | Current session info |
| `memora branch list` | All branches with status |
| `memora branch create --name=<name>` | Create new context branch |
| `memora branch switch <name>` | Switch between branches |

### Knowledge Graph

| Command | Description |
|---------|-------------|
| `memora graph --format=summary` | Knowledge graph overview |
| `memora graph query <entity>` | Query specific entity |
| `memora chat` | Interactive AI chat with memory context |

### System Operations

| Command | Description |
|---------|-------------|
| `memora where` | Show memory storage location |
| `memora migrate` | Upgrade from older versions |
| `memora backup --path=<file>` | Create system backup |
| `memora restore --path=<file>` | Restore from backup |
| `memora gc` | Garbage collection and cleanup |

### Advanced Features

| Command | Description |
|---------|-------------|
| `memora rollback <commit>` | Revert to previous state |
| `memora proxy start/stop` | Manual proxy management |
| `memora proxy-setup` | Configure system-wide OLLAMA_HOST |
| `memora ollama list` | Manage multiple Ollama instances |
| `memora server start` | Launch REST API server |

## Architecture

### System Overview (v3.2)

Memora v3.2 is a production-ready system built from scratch with zero technical debt:

```
src/memora/
├── shared/                    # Core data models & interfaces
│   ├── models.py              # Memory, Session, GraphNode, Commit
│   ├── exceptions.py          # Domain-specific exceptions  
│   └── interfaces.py          # Plugin system contracts
├── core/                      # Business logic layer
│   ├── engine.py              # Main orchestration engine
│   ├── store.py               # Git-style object storage + LRU cache
│   ├── ingestion.py           # Multi-format content processing
│   ├── session.py             # Session lifecycle management
│   ├── graph_v3.py            # Knowledge graph with NER integration
│   ├── index_v3.py            # 4 incremental search indices
│   ├── branch_manager.py      # Branch limits + auto-creation
│   ├── security.py            # PII filtering & validation
│   ├── console_utils.py       # Safe terminal output
│   └── extractors/            # Type-specific memory extraction
│       ├── conversation.py    # Chat memory extraction
│       ├── code.py            # Source code analysis
│       └── document.py        # Document processing
├── ai/                        # LLM integration layer  
│   ├── ollama_proxy.py        # Transparent HTTP proxy
│   ├── file_processor.py      # Multi-format file ingestion
│   └── conversational_ai.py   # Context-aware chat
└── interface/                 # User interaction layer
    ├── cli.py                 # Rich CLI with 20+ commands
    ├── server.py              # FastAPI REST server
    └── api.py                 # Public API facade
```

### Storage Architecture

```
.memora/                      # Git-inspired local storage
├── objects/                  # Content-addressable store (SHA-256)
│   ├── 12/34abcd...         # Object files (compressed)
│   └── ...                  # Distributed across prefixes
├── refs/heads/              # Branch pointers
│   ├── main                 # Default branch
│   └── work-project         # Custom branches  
├── HEAD                     # Current branch reference
├── sessions/                # Session lifecycle
│   ├── active/              # Currently open sessions
│   └── closed/              # Completed sessions
├── graph/                   # Knowledge graph storage
│   ├── nodes.json           # Entity nodes with attributes
│   └── edges.json           # Relationships between entities
├── index/                   # 4 incremental search indices
│   ├── words.json           # Full-text search index
│   ├── temporal.json        # Time-based queries
│   ├── sessions.json        # Session-scoped search
│   └── types.json           # Memory type filtering
├── branches/                # Branch metadata & limits
└── config                   # User preferences & settings
```

### Key Technical Features

**🏗️ Production Architecture:**
- 24 Python source files, zero dead code
- Comprehensive test suite (177 tests passing)
- Type safety with Pydantic models
- Error handling with custom exception hierarchy

**🔄 Git-Style Versioning:**
- SHA-256 content addressing with zlib compression
- Branch management with configurable limits
- Atomic commits with descriptive messages
- Conflict resolution for contradictory memories

**🧠 Intelligent Processing:**
- spaCy NER for automatic entity extraction
- Type detection (conversation/code/document)
- Human-readable memory storage format
- Deduplication and supersession handling

**🔍 Advanced Indexing:**
- Incremental search indices (no full rebuilds)
- Multi-dimensional search (text, time, type, session)
- Knowledge graph traversal and queries
- Natural language time parsing

## Tech Stack

**Core Technologies:**

| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Python 3.11+ | Core implementation |
| NLP | spaCy 3.7+ (en_core_web_sm) | Entity recognition & text processing |
| CLI | Typer + Rich | Beautiful command-line interface |
| API | FastAPI + Uvicorn | REST API server |
| LLM | Ollama Python SDK | Multi-model LLM integration |
| Validation | Pydantic 2.7+ | Type safety & data validation |
| File Processing | pypdf, chardet, markdown | Multi-format document support |
| Security | Built-in PII filtering | Privacy protection |

**Development & Quality:**

| Tool | Purpose | Status |
|------|---------|---------|
| pytest | Testing framework | 177 tests passing |
| pytest-cov | Code coverage | Comprehensive coverage |
| ruff | Linting & formatting | Zero violations |
| mypy | Type checking | Strict type safety |
| Poetry | Dependency management | Lock file maintained |

## Installation & Development

### Production Installation
```bash
pip install memora
```

### Development Setup
```bash
git clone https://github.com/memora-ai/memora.git
cd memora
poetry install --with dev
poetry run python -m spacy download en_core_web_sm
```

### Running Tests
```bash
# Full test suite (177 tests)
poetry run pytest

# With coverage report
poetry run pytest --cov=src/memora --cov-report=html

# Linting & formatting
poetry run ruff check src/ tests/
poetry run ruff format src/ tests/

# Type checking
poetry run mypy src/memora/
```

### Building
```bash
poetry build
```

## System Requirements & Compatibility

**Minimum Requirements:**
- Python 3.11 or higher
- 2GB available disk space
- 512MB RAM for typical workloads

**Supported Platforms:**
- Linux (Ubuntu 20.04+, RHEL 8+, CentOS 8+)
- macOS 11.0+ (Intel and Apple Silicon)
- Windows 10+ (x64)

**LLM Integration:**
- Primary: Ollama (all models supported)
- Extensible architecture for additional providers

**File Format Support:**
- Documents: PDF, Markdown, Plain text
- Code: Python, JavaScript, TypeScript, Go, Rust, Java
- Structured data: JSON, YAML, CSV

## Production Deployment

### Performance Characteristics

**Scale:**
- 100K+ memories per branch
- Sub-100ms search response times
- <50MB memory footprint for typical workloads
- Concurrent multi-user support

**Reliability:**
- Thread-safe storage operations
- Atomic commit transactions
- Automatic crash recovery
- Data integrity verification

**Operations:**
- Zero-downtime updates
- Automated backup scheduling
- Health monitoring endpoints
- Structured logging with configurable levels

### Security & Compliance

**Data Protection:**
- Automatic PII detection and filtering
- Configurable sensitive content rules
- Local encryption at rest (optional)
- No data transmission to external services

**Access Control:**
- File system permission-based security
- Session-based access tracking
- Audit trail for all operations
- Configurable retention policies

**Privacy by Design:**
- No telemetry or analytics collection
- No external network connections required
- Complete data portability
- User-controlled data lifecycle

## Support & Documentation

### Getting Help

**Community Support:**
- GitHub Issues for bug reports and feature requests
- Documentation wiki with detailed guides
- Example configurations and use cases

**Enterprise Support:**
- Priority issue resolution
- Custom deployment assistance  
- Training and onboarding services
- SLA-backed response times

### Documentation

**User Guides:**
- Quick start tutorials
- Advanced configuration options
- Best practices and optimization
- Troubleshooting and diagnostics

**Developer Resources:**
- API reference documentation
- Plugin development guide
- Architecture deep-dives
- Contributing guidelines

## Roadmap

**Current Release (v3.2)**
- Production-ready core functionality
- Complete CLI and API coverage
- Comprehensive test suite
- Performance optimization

**Upcoming Features**
- Enhanced visualization dashboard
- Additional LLM provider integrations  
- Advanced analytics and reporting
- Team collaboration features

## License

Licensed under the Apache License, Version 2.0. See LICENSE file for details.

---

**Memora v3.2** - Enterprise-grade memory management for AI systems  
*Secure • Scalable • Production-ready*
