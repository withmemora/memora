# Memora Demo & User Guide

A practical, hands-on guide to getting Memora up and running with real working examples.

---

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Quick Start (5 Minutes)](#quick-start-5-minutes)
3. [Understanding Ollama & The Proxy](#understanding-ollama--the-proxy)
4. [Essential Commands](#essential-commands)
5. [Real-World Workflows](#real-world-workflows)
6. [Troubleshooting](#troubleshooting)
7. [Directory Structure](#directory-structure)
8. [Performance Tips](#performance-tips)

---

## Installation & Setup

### Prerequisites

- **Python 3.11 or higher** (check with `python --version`)
- **Ollama installed** (https://ollama.ai)
  - Ollama doesn't need to be running initially, but will need to start it before using Memora

### Step 1: Install Memora

```bash
# Using pip
pip install memora

# Or if installing from source
git clone https://github.com/memora-ai/memora.git
cd memora
pip install -e .
```

**Verify installation:**
```bash
memora --help
memora version
```

Expected output:
```
Memora 3.1.0
```

### Step 2: Start Memora (One Command)

```bash
memora start
```

This single command does everything:
1. ✓ Initializes memory store at `./memora_data/`
2. ✓ Checks for Ollama on port 11434
3. ✓ Downloads spaCy language model (~12MB, one-time)
4. ✓ Configures OLLAMA_HOST environment variable
5. ✓ Starts the proxy on port 11435
6. ✓ Awaits incoming connections

### Step 3: Configure Ollama

**In a NEW terminal window**, start Ollama:

```bash
ollama serve
```

Expected output:
```
listening on 127.0.0.1:11434
```

### ⚠️ CRITICAL: Restart Your Ollama Apps

After `memora start` configures `OLLAMA_HOST`, **you must restart any Ollama applications** for memory capture to begin.

Already-running apps will NOT automatically pick up the new `OLLAMA_HOST` setting. This is the most common reason people think Memora isn't working.

**What to restart:**
- ✓ Ollama Desktop app (close and reopen)
- ✓ Open WebUI (restart the browser or refresh)
- ✓ Any scripts using `ollama` CLI (restart them)
- ✓ Docker containers running Ollama (restart the container)

**New apps started AFTER `memora start` will work automatically.**

After restarting your Ollama apps, memory capture will begin. Test it:

```bash
# Terminal 3: Verify memory capture started
memora stats
```

If "Total Memories" is increasing, capture is working!

---

## Quick Start (5 Minutes)

### Terminal 1: Run Memora

```bash
cd ~/my_project  # Or your preferred directory
memora start
```

Output:
```
🚀 Starting Memora...
✓ Repository initialized at: ~/my_project/memora_data
✓ spaCy language model available
🔍 Checking port availability...
✓ Ollama detected on port 11434
✓ OLLAMA_HOST set to http://localhost:11435 system-wide
🌐 Starting proxy on port 11435...
✓ Memora is running! Chat with Ollama normally...
Press Ctrl+C to stop
```

### Terminal 2: Start Ollama

```bash
ollama serve
```

### Terminal 3: Use Ollama (Create Memories)

```bash
# Pull a model if you don't have one
ollama pull llama3.2:3b

# Now chat - Memora will capture automatically
ollama run llama3.2:3b "What are the key features of Rust?"
```

Memora is now capturing this conversation!

### Terminal 4: Query Memories

While Memora and Ollama are running, open another terminal:

```bash
# Search your memories
memora search "Rust features"

# Check where data is stored
memora where

# See statistics
memora stats
```

That's the basic workflow. Now let's explore what you can do.

---

## Understanding Ollama & The Proxy

### How Memora Captures Memories

```
Your Client (must be restarted!)
    ↓
Memora Proxy (port 11435)  ← You point clients here
    ↓
Ollama Server (port 11434)  ← Memora talks to this
```

### ⚠️ Why Apps Must Be Restarted

When `memora start` sets `OLLAMA_HOST=http://localhost:11435`, **already-running apps don't see this change**. They're still trying to connect to the old address.

- Apps started BEFORE `memora start` → Won't use the proxy (no capture)
- Apps started AFTER `memora start` → Will use the proxy (capture enabled)
- **Apps restarted AFTER `memora start` → Will use the proxy (capture enabled)**

**This is not a bug — it's how environment variables work in all operating systems.**

### Why This Works

- **Transparent**: Clients don't know there's a proxy
- **Non-blocking**: Memory capture happens asynchronously (doesn't slow down responses)
- **Universal**: Works with any client that talks to Ollama
- **Simple**: Just set `OLLAMA_HOST=http://localhost:11435`

### Setting OLLAMA_HOST

```bash
# Windows (via memora start - automatic)
# Memora sets this using `setx OLLAMA_HOST http://localhost:11435`

# macOS/Linux (manual)
export OLLAMA_HOST=http://localhost:11435
```

Then when you use Ollama clients:
```bash
ollama run llama3.2:3b  # Automatically uses port 11435 via OLLAMA_HOST
```

**Check what's set:**
```bash
echo $OLLAMA_HOST  # macOS/Linux
echo %OLLAMA_HOST%  # Windows
```

---

## Essential Commands

All commands assume your Memora store is in `./memora_data/`. Use `--memory-path` to change this.

### Initialization & Status

#### `memora init`
Create a new memory store in a directory.

```bash
memora init --path ./my_memories
```

Creates:
```
my_memories/
└── .memora/
    ├── config           # Store configuration
    ├── sessions/        # Session tracking
    ├── objects/         # All memories (content-addressable)
    ├── indices/         # Search indices
    └── refs/            # Branch pointers
```

#### `memora start`
Complete setup: init + proxy + Ollama configuration (recommended).

```bash
memora start --port 11435
```

**Options:**
- `--port` - Proxy listen port (default: 11435)
- `--memory-path` - Where to store memories (default: `./memora_data`)
- `--auto-setup` - Auto-configure OLLAMA_HOST (default: true)

#### `memora version`
Show installed Memora version.

```bash
memora version
# Output: Memora 3.1.0
```

#### `memora where`
Show where your memories are stored.

```bash
memora where
# Output: Memory storage: /Users/you/my_project/memora_data
```

#### `memora stats`
Display memory store statistics.

```bash
memora stats
```

Output:
```
Memora Statistics
┌─────────────────────────────────────────┐
│ Metric                    │ Value       │
├─────────────────────────────────────────┤
│ Total Memories            │ 1,247       │
│ Memory Objects            │ 892         │
│ Sessions                  │ 43          │
│ Storage Size              │ 2.3 MB      │
│ Average Memory Size       │ 1.8 KB      │
│ Largest Branch            │ main (892)  │
│ Active Branches           │ 3           │
└─────────────────────────────────────────┘
```

### Search & Discovery

#### `memora search`
Find memories matching a query.

```bash
# Basic search
memora search "Python decorators"

# With time filter
memora search "dark mode preferences" --time "last week"

# Limit results
memora search "API design" --limit 10
```

Output:
```
Search results for 'Python decorators'
┌──────────────────────────────────────────────────────────────┐
│ ID   │ Type         │ Date      │ Content            │ Conf  │
├──────────────────────────────────────────────────────────────┤
│ a1b2c│ conversation │ 12/15 14:32│ When using @cache  │ 0.92  │
│ d3e4f│ code         │ 12/14 09:15│ def decorator(...) │ 0.88  │
│ g5h6i│ conversation │ 12/13 18:20│ Decorator pattern  │ 0.85  │
└──────────────────────────────────────────────────────────────┘
```

#### `memora when`
Find memories from a specific time period.

```bash
# Natural language time expressions
memora when "last week"
memora when "yesterday"
memora when "3 days ago"
memora when "last Monday"
memora when "between 2024-12-01 and 2024-12-15"

# With limit
memora when "this month" --limit 50
```

Output:
```
Searching memories from 2024-12-08 00:00 to 2024-12-15 00:00
🕒 Memories from 'last week' (23 found)
┌──────────────────────────────────────────────────────────────┐
│ Date/Time    │ Type         │ Content            │ Source     │
├──────────────────────────────────────────────────────────────┤
│ 12/14 16:45  │ conversation │ Python asyncio ... │ ollama_chat│
│ 12/13 10:30  │ code         │ async def handle() │ code_file  │
│ 12/12 14:20  │ conversation │ Type hints in ...  │ ollama_chat│
└──────────────────────────────────────────────────────────────┘

📊 Found 23 memories in 'last week'
```

### Document & Code Ingestion

#### `memora ingest`
Add documents or code to your memory.

```bash
# Ingest a document
memora ingest "./project_spec.md"

# Ingest a code file
memora ingest "./src/main.py"

# Ingest a directory of code
memora ingest "./src/"

# Ingest with custom memory path
memora ingest "./notes.txt" --memory-path ./custom_store
```

Output:
```
Ingested 12 memories from ./project_spec.md
  Project uses React 18 with TypeScript for frontend...
  Database schema includes User, Post, Comment tables...
  API endpoints follow RESTful conventions...
  [and more...]
```

The ingestion system automatically:
- Detects file types (code, markdown, PDF, text)
- Extracts code for 10+ languages
- Parses documents and extracts key information
- Creates separate memories for logical chunks
- Applies security filtering for PII

### Session Management

#### `memora session`
View and manage conversation sessions.

```bash
# List all sessions
memora session list

# Show active session
memora session active

# Session details
memora session info <session_id>
```

Output:
```
Sessions
┌────────────────────────────────────────────────────────────┐
│ ID       │ Status   │ Created         │ Last Used          │
├────────────────────────────────────────────────────────────┤
│ sess_abc │ active   │ 2024-12-15 10:00│ 2024-12-15 10:45   │
│ sess_def │ closed   │ 2024-12-14 15:30│ 2024-12-14 16:15   │
│ sess_ghi │ closed   │ 2024-12-13 09:00│ 2024-12-13 09:30   │
└────────────────────────────────────────────────────────────┘
```

### Branch Management

#### `memora branch`
Organize memories across project contexts.

```bash
# List branches
memora branch list

# Create a new branch
memora branch create "work-project"
memora branch create "research"

# Switch branches
memora branch switch work-project

# Check branch status
memora branch status

# View branch info
memora branch info
```

Output:
```
Branches
┌────────────────────────────────────────────────────────────┐
│ Name              │ Commit           │ Current           │
├────────────────────────────────────────────────────────────┤
│ main              │ a1b2c3d4e5f6     │ *                 │
│ work-project      │ f6e5d4c3b2a1     │                   │
│ research          │ none             │                   │
└────────────────────────────────────────────────────────────┘

Current branch: main
```

### Knowledge Graph

#### `memora graph`
Explore entities and relationships discovered in your memories.

```bash
# Show graph summary
memora graph --format summary

# Query for specific entities
memora graph query "Python"

# Show connections
memora graph --show-connections

# Export as JSON
memora graph --format json > graph.json
```

Output:
```
Knowledge Graph Summary
┌────────────────────────────────────────────────────────────┐
│ Metric                       │ Value                      │
├────────────────────────────────────────────────────────────┤
│ Total Entities               │ 487                        │
│ Total Relationships          │ 1,203                      │
│ Most Common Entity Type      │ PERSON (145)               │
│ Average Connections          │ 2.47 per entity            │
└────────────────────────────────────────────────────────────┘

Top Entities (by connection count):
  Python (54 connections)
  React (38 connections)
  PostgreSQL (31 connections)
  TypeScript (29 connections)
  Docker (27 connections)
```

### Chat & Interaction

#### `memora chat`
Interactive AI conversation with memory context.

```bash
# Chat with default model
memora chat

# Chat with specific model
memora chat --model "llama2:70b"

# Chat on specific branch
memora chat --branch "work-project"
```

Example interaction:
```
Memora Chat - Model: llama3.2:3b | Branch: main
Type 'exit' to end

You: What was I discussing about async Python last week?
AI: Based on your memories, you discussed asyncio patterns, specifically:
    - Using async/await for concurrent operations
    - Handling multiple concurrent requests with asyncio.gather()
    - Event loop management in FastAPI applications
    
    You seemed particularly interested in understanding the difference between
    threading and async/await, and how asyncio handles I/O-bound operations...

You: How does that relate to the project we're working on?
AI: In your work-project branch, you mentioned needing to handle multiple
    concurrent requests to external APIs. The async patterns would be
    particularly useful there...

You: exit
```

### Export & Backup

#### `memora export`
Export memories in different formats.

```bash
# Export as Markdown
memora export --format markdown > memories.md

# Export as JSON
memora export --format json > memories.json

# Export as plain text
memora export --format plain > memories.txt

# Export specific branch
memora export --branch work-project --format markdown > work.md
```

Output:
```
memories.md (Markdown format):
---
# Memora Export
Generated: 2024-12-15

## Memory 1: Python Decorators
**Type:** conversation
**Date:** 2024-12-14 09:15
**Confidence:** 0.92

When using @cache decorators, Python memoizes function results...

## Memory 2: Async Patterns
**Type:** code
**Date:** 2024-12-13 18:20

async def fetch_multiple(urls):
    tasks = [fetch(url) for url in urls]
    return await asyncio.gather(*tasks)
```

#### `memora backup`
Create a backup of your memory store.

```bash
# Create backup
memora backup --output ./memora_backup.tar.gz

# List backups
memora backup --list

# Restore from backup
memora restore --backup ./memora_backup.tar.gz
```

### Cleanup & Maintenance

#### `memora gc`
Garbage collection: remove unreferenced objects and optimize storage.

```bash
# Run garbage collection
memora gc

# Show what would be deleted (dry run)
memora gc --dry-run
```

Output:
```
🗑️  Running garbage collection...
✓ Scanned 1,247 objects
✓ Found 142 unreferenced objects
✓ Freed 450 KB
✓ Defragmented indices
✓ GC complete: 1,105 objects remaining
```

#### `memora forget`
Permanently delete specific memories.

```bash
# Forget memories matching a query
memora forget "old project notes"

# Forget all memories from a time period
memora forget --when "before 2024-01-01"

# Forget with confirmation
memora forget --query "test data" --confirm

# Forget entire branch
memora forget --branch research --confirm
```

---

## Real-World Workflows

### Workflow 1: Research Project with Isolated Memories

```bash
# Start Memora (if not already running)
memora start

# Create a research branch
memora branch create "ml-research"
memora branch switch "ml-research"

# Now all memories go to this branch
# Chat with Ollama, ingest papers, etc.

memora chat --branch "ml-research"

# Later: search within this branch
memora search "transformer architecture" --branch "ml-research"

# Export research notes
memora export --branch "ml-research" --format markdown > research_notes.md
```

### Workflow 2: Code Learning & Documentation

```bash
# Create a learning branch
memora branch create "learning"
memora branch switch "learning"

# Ingest important code files
memora ingest "./src/models/"
memora ingest "./src/utils/"

# Ask Memora about the code
memora chat --branch "learning"
# You: "Explain how the transformer model is structured"
# AI: [Uses ingested code to explain with examples]

# Search for specific patterns
memora search "error handling" --branch "learning"
```

### Workflow 3: Team Documentation

```bash
# Main branch for team-wide knowledge
memora branch switch "main"

# Ingest shared documentation
memora ingest "./docs/"
memora ingest "./README.md"
memora ingest "./ARCHITECTURE.md"

# Team members can now search team knowledge
memora search "API authentication"

# Explore the knowledge graph
memora graph query "authentication"
```

### Workflow 4: Conversation Tracking Over Time

```bash
# Track all conversations for a project
memora branch create "project-alpha"
memora branch switch "project-alpha"

# Normal workflow - just chat
ollama run llama3.2:3b "Help me debug this error..."
ollama run llama3.2:3b "What's the best way to structure this?"

# Later, review what you discussed
memora when "this week"
# Shows all conversations from this week on this branch

memora search "error handling" --time "last 3 days"
# Shows relevant discussions from the past 3 days
```

### Workflow 5: Version Control for Memory Changes

```bash
# Make major changes to your memory
memora ingest "./major_update.md"
memora search "old approach" --time "before 2024-12-01"
memora forget "outdated information" --confirm

# Rollback if needed
memora rollback --to <previous_commit_hash>

# List version history
memora log --branch main
```

---

## Troubleshooting

### "No Memora store found"

**Problem:** Running commands without initializing first.

```bash
# This will fail:
memora search "something"
# Error: No Memora store found. Run 'memora init' first.
```

**Solution:**
```bash
# Initialize or start
memora start  # Recommended - does everything
# OR
memora init --path ./memora_data
```

### "Port 11435 is already in use"

**Problem:** Another application is using the proxy port.

```bash
memora start
# Error: ✗ Port 11435 is already in use.
```

**Solution:**
```bash
# Option 1: Use a different port
memora start --port 11436

# Option 2: Find and stop the process using 11435
# Windows:
netstat -ano | findstr :11435
taskkill /PID <PID> /F

# macOS/Linux:
lsof -i :11435
kill -9 <PID>
```

### "Ollama not detected on port 11434"

**Problem:** Ollama isn't running when you start Memora.

```bash
memora start
# Warning: ⚠ Ollama not detected on port 11434.
```

**Solution:**
This is just a warning - Memora will still work. Start Ollama in another terminal:

```bash
# Terminal 2
ollama serve
```

Memora will connect when Ollama starts.

### "Failed to download spaCy model"

**Problem:** Network issues prevent downloading the language model.

```bash
memora start
# Warning: ⚠ Failed to download spaCy model
```

**Solution:**
```bash
# Manual download with pip
python -m spacy download en_core_web_sm

# Then try Memora again
memora start
```

### "Memora is capturing but then stopped"

**Problem:** Memories were being captured but have stopped appearing.

**Most likely cause:** You restarted Ollama but NOT your client applications.

**Solution:**
```bash
# 1. Verify OLLAMA_HOST is still set
echo $OLLAMA_HOST  # macOS/Linux
echo %OLLAMA_HOST%  # Windows

# Should show: http://localhost:11435

# 2. Verify Memora is still running
memora stats

# 3. Restart your Ollama client application (NOT just Ollama daemon)
# Examples:
#   - Ollama Desktop: Close and reopen the app
#   - Open WebUI: Close browser tab and navigate back
#   - Scripts: Stop and restart the script
#   - Docker: docker restart <container_id>

# 4. Try a conversation
ollama run llama3.2:3b "Hello"

# 5. Check again
memora stats  # "Total Memories" should have increased
```

### "Search returns no results"

**Problem:** Queries aren't matching your memories.

**Solutions:**
```bash
# 1. Check if memories exist
memora stats
# If "Total Memories" is 0, no memories have been captured

# 2. Try broader searches
memora search "Python"  # More general
# vs.
memora search "decorator pattern"  # More specific

# 3. Check memories by time
memora when "today"

# 4. Verify Memora is capturing
# Make sure OLLAMA_HOST is set:
echo $OLLAMA_HOST  # Should show http://localhost:11435

# 5. Check on correct branch
memora branch status
# Search results only show memories on current branch
```

### "Chat/Proxy seems slow"

**Problem:** Memory capture is adding latency.

This shouldn't happen - memory capture is asynchronous. However:

```bash
# Check storage size
memora stats

# If very large (>1GB), run garbage collection
memora gc

# Check if indices are too large
ls -lh memora_data/.memora/indices/

# Consider archiving old sessions
memora session archive --older-than 90
```

### spaCy model issues

**Problem:** NER features not working, entity recognition disabled.

```bash
# Manually download and configure
python -m spacy download en_core_web_sm

# Verify it works
python -c "import spacy; spacy.load('en_core_web_sm')"

# Should output: <Language: en>
```

---

## Directory Structure

After running `memora start`, your memory store looks like this:

```
memora_data/
├── .memora/                    # Internal store (don't edit manually)
│   ├── config                  # Store configuration (JSON)
│   ├── objects/                # Content-addressable storage
│   │   ├── a1/                 # Hash prefix directory
│   │   │   └── b2c3d4...gz    # Compressed memory objects
│   │   ├── d4/
│   │   └── ...
│   ├── indices/                # Search indices
│   │   ├── word_index.json    # Full-text search
│   │   ├── temporal_index.json # Time-based search
│   │   ├── session_index.json # Session tracking
│   │   └── type_index.json    # Memory type index
│   ├── refs/                   # Branch pointers
│   │   ├── heads/
│   │   │   ├── main           # Current commit of main branch
│   │   │   ├── work-project   # Current commit of work-project
│   │   │   └── ...
│   │   └── HEAD               # Current active branch
│   └── sessions/               # Session metadata
│       ├── sess_abc123.json   # Session details
│       └── ...
└── [no user-accessible files]

```

### Key Files

| File | Purpose | User Access |
|------|---------|-------------|
| `objects/` | All memory objects | Read-only (internal) |
| `indices/` | Search indices | Read-only (internal) |
| `refs/heads/` | Branch pointers | Read-only (internal) |
| `config` | Store settings | Readable, rarely edited |

**Important:** Don't manually edit files in `.memora/` - use Memora commands instead.

---

## Performance Tips

### 1. Keep Memories Organized with Branches

```bash
# Bad: Everything on main branch (1000+ memories)
memora search "Python"  # Searches through everything

# Good: Organized by context
memora branch create "work"
memora branch create "learning"
memora branch create "research"

# Search is faster on smaller branches
memora branch switch "work"
memora search "API design"  # Only searches work memories
```

### 2. Archive Old Memories

```bash
# Remove memories older than 6 months
memora forget --when "before 2024-06-15" --confirm

# Or archive to separate branch
memora branch create "archive-2024-q1"
# Move old memories there manually
```

### 3. Regular Garbage Collection

```bash
# Run monthly or when storage gets large (>500MB)
memora gc
```

Expected improvement: ~20-30% storage reduction.

### 4. Use Specific Queries

```bash
# Slower: Very general
memora search "code"

# Faster: More specific
memora search "Python error handling"

# Use time filters to narrow results
memora search "API design" --time "last month"
```

### 5. Limit Search Results

```bash
# Gets all results (could be thousands)
memora search "Python"

# Faster: Get just top 10
memora search "Python" --limit 10
```

### 6. Monitor Storage Size

```bash
# Check current usage
du -sh memora_data/

# Watch growth over time
memora stats  # Shows "Storage Size"

# If approaching 500MB+, consider:
memora gc
memora forget --when "before 2024-01-01" --confirm
```

---

## Next Steps

- **Explore the Knowledge Graph**: `memora graph query "your_topic"`
- **Set Up Multiple Branches**: Create branches for different projects
- **Integrate with Your Workflow**: Use `memora ingest` with your documentation
- **Automate Backups**: Run `memora backup` periodically
- **Read Architecture Guide**: See `docs-clean/1-architecture/ARCHITECTURE.md` for technical details
- **See Feature Details**: Check `docs-clean/2-features/FEATURES.md` for in-depth feature information

---

## Command Reference Quick Table

| Command | Purpose | Example |
|---------|---------|---------|
| `memora start` | Start Memora & proxy | `memora start --port 11435` |
| `memora init` | Initialize new store | `memora init --path ./memories` |
| `memora search` | Find memories by keyword | `memora search "Python"` |
| `memora when` | Find memories by time | `memora when "last week"` |
| `memora stats` | Show store statistics | `memora stats` |
| `memora where` | Show storage location | `memora where` |
| `memora ingest` | Add documents/code | `memora ingest "./src/"` |
| `memora chat` | Interactive chat with context | `memora chat --model llama3.2:3b` |
| `memora branch` | Manage branches | `memora branch create work-project` |
| `memora session` | View sessions | `memora session list` |
| `memora graph` | Explore entities | `memora graph query "Python"` |
| `memora export` | Export memories | `memora export --format markdown` |
| `memora backup` | Create backup | `memora backup --output backup.tar.gz` |
| `memora gc` | Clean up storage | `memora gc` |
| `memora forget` | Delete memories | `memora forget "old notes"` |
| `memora rollback` | Restore previous state | `memora rollback --to <commit>` |
| `memora version` | Show version | `memora version` |

---

## Getting Help

- **Inside Memora**: `memora --help` or `memora <command> --help`
- **Online**: https://github.com/memora-ai/memora
- **Report Issues**: https://github.com/memora-ai/memora/issues
- **Full Docs**: See `docs-clean/` folder
