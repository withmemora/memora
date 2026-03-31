<p align="center">
  <img src="Assets/logo.svg" alt="memora" width="300" />
</p>

<p align="center">
  Git-style versioned memory for any LLM.
</p>

---

## What is Memora?

Memora gives LLMs persistent, versioned memory that automatically captures and stores facts from your conversations. Every fact is stored with a SHA-256 hash. Every session creates a commit. Contradictions are detected and resolved. Nothing leaves your machine.

**Key Features:**
- 🔄 **Transparent Integration**: Works with existing Ollama installations (GUI & CLI)
- 🧠 **Automatic Memory Capture**: Extracts facts from conversations using NLP
- 📚 **Git-Style Versioning**: Version-controlled memory with conflict detection
- 🔍 **Smart Search**: Search and retrieve relevant memories
- 📄 **Document Ingestion**: Process text, Markdown, and PDF files
- 🌐 **HTTP Proxy**: Transparent capture from any Ollama client

## Quick Start

```bash
# Install dependencies
poetry install

# Option 1: Interactive setup wizard
poetry run memora setup

# Option 2: Manual setup
poetry run memora proxy start --background
export OLLAMA_HOST=http://localhost:11435
ollama run llama3.2:3b  # Chat normally - memories captured automatically!

# Check captured memories
poetry run memora search ""
```

## Project Structure

```
Memora/
├── src/memora/           # Core source code
├── tests/               # Test suite
├── docs/                # Documentation
├── Assets/              # Project assets (logos, etc.)
├── dev/                 # Development files and examples
├── QUICK_START.md       # Quick start guide
└── README.md           # This file
```

## Built With

- Python 3.11+
- spaCy (NLP processing)
- Ollama (LLM interface)
- FastAPI (HTTP proxy)
- Typer (CLI interface)

## Documentation

- [Quick Start Guide](QUICK_START.md) - Get up and running in 5 minutes
- [Development Files](dev/) - Development documentation and examples

## License

MIT
