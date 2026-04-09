# 🧠 MEMORA - COMPLETE FEATURE DEMO GUIDE
## One-Command Setup + Full Feature Walkthrough

**Memora v3.1.0** - Git-style versioned memory for LLMs  
A local-first, privacy-focused memory system that captures and manages all your LLM conversations.

---

## ⚡ QUICK START (30 seconds)

### For Users (No Coding Knowledge Needed)

```bash
# One command to start everything
memora start
```

That's it! Memora will:
- ✅ Initialize the memory repository
- ✅ Download required AI models
- ✅ Start the memory capture system
- ✅ Tell you exactly what to do next

Your LLM conversations will be automatically captured and managed - just like using mem0 or Pieces.

---

## 📋 TABLE OF CONTENTS

1. [Installation](#installation)
2. [First Run - Basic Setup](#first-run---basic-setup)
3. [Core Features](#core-features-explained)
4. [Feature Demonstrations](#feature-demonstrations)
5. [Advanced Features](#advanced-features)
6. [Troubleshooting](#troubleshooting)

---

## 🔧 Installation

### Windows, macOS, or Linux

```bash
# Clone the repository
git clone https://github.com/memora-ai/memora.git
cd memora

# Install with Poetry (Python package manager)
poetry install

# That's it! You can now run:
memora start
```

**Don't have Poetry?** [Install it here](https://python-poetry.org/docs/#installation)

---

## 🚀 First Run - Basic Setup

### Step 1: Start Memora (One Command!)

```bash
memora start
```

**What you'll see:**
```
🚀 Starting Memora...
✓ Repository initialized at: ./memora_data
✓ spaCy language model available
✓ Ollama detected on port 11434
✓ OLLAMA_HOST set to http://localhost:11435 system-wide
🌐 Starting proxy on port 11435...
✓ Memora is running! Chat with Ollama normally - memories will be captured automatically.
Press Ctrl+C to stop
```

### Step 2: Use Ollama Normally

In another terminal, use Ollama like you normally would:

```bash
# Talk to your favorite LLM through Memora's proxy
ollama run llama2
# or
curl http://localhost:11435/api/generate -d '{"model": "llama2", "prompt": "Hello!"}'
```

**Magic:** All your conversations are automatically captured and stored!

### Step 3: Stop Memora

```bash
# Press Ctrl+C in the terminal running `memora start`
# or in another terminal:
memora proxy stop
```

---

## 🎯 Core Features Explained

### What is Memora?

Imagine Git for your LLM conversations. Just like Git tracks code changes with commits, branches, and history - **Memora tracks your LLM conversations** with:

- **Automatic Capture**: Every conversation is saved automatically
- **Versions & Branches**: Create branches to explore different conversation paths
- **Full History**: See everything you discussed and when
- **Search**: Find memories by content, time, or entities mentioned
- **Rollback**: Go back to any previous state
- **Privacy**: Everything stays on your computer

---

## 🎬 Feature Demonstrations

### DEMO 1: Basic Search
**What it shows:** Finding stored memories

#### Step 1: Create some memories
```bash
# Start a chat session and have a conversation
memora start  # In terminal 1

# In terminal 2, add memories
memora ingest ./sample_conversation.txt
# or start chatting through Ollama:
curl http://localhost:11435/api/generate \
  -d '{"model": "llama2", "prompt": "What are the best practices for Python?"}'
```

#### Step 2: Search your memories
```bash
memora search "Python best practices"
```

**Expected Output:**
```
🔍 Searching: "Python best practices"

Found 3 memories:

1. [CONVERSATION] Python best practices overview
   Source: OLLAMA_CHAT | Session: sess_abc123
   Created: 2024-01-15 14:32:00
   Content: "In Python, best practices include using type hints, following PEP 8..."

2. [DOCUMENT] Python PEP Style Guide
   Source: FILE_INGESTION | Session: sess_def456
   Created: 2024-01-14 10:15:00

3. [CODE] Python function example
   Source: FILE_INGESTION | Session: sess_ghi789
   Created: 2024-01-13 09:45:00
```

**What it demonstrates:**
- ✅ Automatic memory capture
- ✅ Natural language search
- ✅ Multiple memory types (CONVERSATION, DOCUMENT, CODE)
- ✅ Metadata about memories

---

### DEMO 2: Time-Based Search
**What it shows:** Finding memories by when they were created

```bash
# Find all memories from today
memora when "today"
```

**Supported time formats:**
```bash
memora when "last 7 days"
memora when "2024-01-15"
memora when "yesterday"
memora when "this week"
memora when "January 2024"
```

**Expected Output:**
```
📅 Memories from: today

Found 12 memories created today:

Created: 2024-01-15 14:32:00 | Python best practices
Created: 2024-01-15 13:15:00 | Machine Learning intro
Created: 2024-01-15 11:20:00 | React hooks explanation
...
```

**What it demonstrates:**
- ✅ Temporal search (time-based queries)
- ✅ Natural language date parsing
- ✅ Multiple time formats

---

### DEMO 3: View Statistics
**What it shows:** Overview of your memory system

```bash
memora stats
```

**Expected Output:**
```
📊 MEMORA STATISTICS

Repository: ./memora_data
Current Branch: main

📈 Memory Overview:
   Total Memories: 247
   ├─ Conversations: 156
   ├─ Documents: 67
   └─ Code Snippets: 24

📁 Storage:
   Used Space: 2.3 MB
   Compressed: 1.1 MB (48% compression)
   Objects: 312

🔀 Branches:
   Total Branches: 4
   ├─ main (active)
   ├─ feature/nlp-research
   ├─ feature/react-learning
   └─ archived/old-project

📅 Sessions:
   Active Sessions: 2
   Closed Sessions: 18
   Last Update: 2024-01-15 14:32:00

🔍 Index Status:
   Words Indexed: 3,421
   Entities: 156
   Graph Nodes: 89
```

**What it demonstrates:**
- ✅ Complete system overview
- ✅ Memory breakdown by type
- ✅ Storage efficiency metrics
- ✅ Branch and session management

---

### DEMO 4: Store Location
**What it shows:** Where memories are physically stored

```bash
memora where
```

**Expected Output:**
```
📍 MEMORA REPOSITORY LOCATION

Storage Path: /Users/yourname/memora_data/.memora

Directory Structure:
├── objects/          - Compressed memory objects (Git-like)
├── refs/
│   └── heads/       - Branch pointers
├── sessions/        - Chat session records
├── graph/           - Knowledge graph (entities & relationships)
├── index/           - Search indices
├── branches/        - Branch metadata
└── config           - Settings

Total Size: 2.3 MB
Compressed Size: 1.1 MB

Recent Activity:
 - 2024-01-15 14:32:00 → 5 new memories
 - 2024-01-15 13:15:00 → 3 memories
 - 2024-01-15 11:20:00 → 2 memories
```

**What it demonstrates:**
- ✅ Git-like storage structure
- ✅ Transparency about data location
- ✅ Storage breakdown
- ✅ Privacy: Everything is local!

---

### DEMO 5: Ingest Files
**What it shows:** Adding documents, code, and files to memory

#### Create a sample file first:
```bash
# Create a Python code file
cat > sample_code.py << 'EOF'
# Best practices for async programming
import asyncio

async def fetch_data(url):
    """Fetch data from a URL asynchronously."""
    print(f"Fetching from {url}")
    await asyncio.sleep(2)  # Simulate network delay
    return {"status": "success", "data": "sample"}

async def main():
    tasks = [
        fetch_data("https://api.example.com/1"),
        fetch_data("https://api.example.com/2"),
    ]
    results = await asyncio.gather(*tasks)
    return results

if __name__ == "__main__":
    asyncio.run(main())
EOF
```

#### Ingest the file:
```bash
memora ingest sample_code.py
```

**Expected Output:**
```
📥 INGESTING FILE: sample_code.py

✓ File processed: Python source code (312 bytes)
✓ Type detected: CODE
✓ Entities extracted: asyncio, fetch_data, async, await
✓ Stored with ID: mem_xyz789

Memory Created:
├── ID: mem_xyz789
├── Type: CODE
├── Source: FILE_INGESTION
├── Confidence: 0.95
├── Lines: 25
└── Language: Python

To search this memory later, try:
  memora search "async programming"
  memora search "fetch_data"
```

#### Ingest multiple files at once:
```bash
memora ingest ./documents/
memora ingest *.py
memora ingest *.pdf
```

**What it demonstrates:**
- ✅ Multi-format ingestion (code, documents, PDFs)
- ✅ Automatic type detection
- ✅ Entity extraction from code
- ✅ Batch processing

---

### DEMO 6: Branches (Git-Style Versioning)
**What it shows:** Exploring different paths in conversations

#### View all branches:
```bash
memora branch list
```

**Expected Output:**
```
🔀 BRANCHES

Current Branch: main ← You are here

Branches in Repository (4):
1. main (10 memories)
   └─ Latest: Python best practices [2024-01-15 14:32:00]

2. feature/nlp-research (34 memories)
   └─ Latest: NLP pipeline architecture [2024-01-15 10:20:00]

3. feature/react-learning (15 memories)
   └─ Latest: React hooks patterns [2024-01-14 16:45:00]

4. archived/old-project (42 memories)
   └─ Latest: Legacy API docs [2024-01-10 09:30:00]

Total Memories: 101 across all branches
Storage Used: 2.3 MB
```

#### Create a new branch:
```bash
memora branch create "feature/llm-fine-tuning"
```

**Expected Output:**
```
✓ Branch created: feature/llm-fine-tuning
  From: main (at memory mem_latest123)
  
You can now:
  memora branch switch feature/llm-fine-tuning
  memora search "your query"        # Works in this branch
  memora ingest files               # Memories added to this branch
  
To merge back later:
  memora branch merge feature/llm-fine-tuning
```

#### Switch between branches:
```bash
memora branch switch feature/nlp-research
memora search "transformers"  # Only searches this branch
```

**Expected Output:**
```
✓ Switched to branch: feature/nlp-research

Memories in this branch: 34
Latest memory: 2024-01-15 10:20:00

Your session is now isolated to this branch.
All new memories will be added here.
```

#### Merge branches:
```bash
memora branch merge feature/nlp-research
```

**What it demonstrates:**
- ✅ Git-style branches for different topics
- ✅ Branch isolation (each branch has separate memories)
- ✅ Branch switching
- ✅ Create, list, and manage branches

---

### DEMO 7: Commits & History
**What it shows:** Git-like versioning with full history

#### View commit history:
```bash
memora log
```

**Expected Output:**
```
📜 COMMIT HISTORY (Latest 10)

1. mem_abc123456789 [2024-01-15 14:32:00]
   Author: User via OLLAMA_CHAT
   Message: "Auto-commit: 3 new memories from chat session"
   Branch: main
   Memories Added: 3
   └─ Python best practices
   └─ Async/await patterns
   └─ Type hints best practices

2. mem_def234567890 [2024-01-15 13:15:00]
   Author: User via FILE_INGESTION
   Message: "Ingested documentation: react-hooks.pdf"
   Branch: main
   Memories Added: 5
   Entities: React, hooks, useState, useEffect

3. mem_ghi345678901 [2024-01-14 16:45:00]
   Author: User via OLLAMA_CHAT
   Message: "Auto-commit: Chat session completed"
   Branch: feature/react-learning
   Memories Added: 8

...show more with: memora log --limit 50
```

#### View detailed commit:
```bash
memora log --detail mem_abc123456789
```

#### Create manual commit:
```bash
memora commit "Completed Python learning module - ready to merge"
```

**What it demonstrates:**
- ✅ Full commit history with timestamps
- ✅ Automatic commits on session end
- ✅ Manual commits for milestones
- ✅ Commit messages and metadata

---

### DEMO 8: Knowledge Graph (Entity Recognition)
**What it shows:** Automatic understanding of entities and relationships

#### View the knowledge graph:
```bash
memora graph
```

**Expected Output:**
```
🕸️ KNOWLEDGE GRAPH

Total Entities: 156
Total Relationships: 284

TOP ENTITIES (by frequency):

1. Python (mentioned in 42 memories)
   Related to: asyncio, pandas, Django, FastAPI
   First seen: 2024-01-10
   Last seen: 2024-01-15

2. Machine Learning (mentioned in 28 memories)
   Related to: transformers, PyTorch, TensorFlow, NLP
   First seen: 2024-01-11
   Last seen: 2024-01-15

3. React (mentioned in 19 memories)
   Related to: hooks, JSX, Redux, Next.js
   First seen: 2024-01-12
   Last seen: 2024-01-14

4. Database (mentioned in 15 memories)
   Related to: PostgreSQL, MongoDB, Redis, SQL
   First seen: 2024-01-13
   Last seen: 2024-01-15

5. API Design (mentioned in 12 memories)
   Related to: REST, GraphQL, FastAPI, Swagger
   First seen: 2024-01-14
   Last seen: 2024-01-15

Entity Categories:
├─ Technologies: Python, JavaScript, React, PostgreSQL... (52)
├─ Concepts: Machine Learning, NLP, API Design... (43)
├─ Libraries: asyncio, pandas, PyTorch, Django... (38)
├─ People: (if mentioned) (12)
└─ Other: (11)
```

#### Query the graph:
```bash
memora graph query "Python"
```

**Expected Output:**
```
🔍 GRAPH QUERY: Python

Direct Entity: Python
Mentioned in: 42 memories

Connected Concepts:
├─ asyncio (18 memories) - async programming library
├─ pandas (15 memories) - data analysis library
├─ Django (12 memories) - web framework
├─ FastAPI (11 memories) - modern web framework
├─ PyTorch (9 memories) - ML library
└─ Type hints (8 memories) - static typing

Timeline:
├─ 2024-01-10: First mention (Python intro)
├─ 2024-01-11: asyncio deep dive
├─ 2024-01-12: pandas for data analysis
├─ 2024-01-13: Django REST framework
├─ 2024-01-14: FastAPI best practices
└─ 2024-01-15: Type hints in modern Python

Learning Path Suggested:
1. Python basics
2. asyncio patterns
3. pandas data analysis
4. FastAPI framework
5. Type hints best practices
```

**What it demonstrates:**
- ✅ Automatic entity extraction
- ✅ Relationship mapping
- ✅ Concept connections
- ✅ Learning path suggestions

---

### DEMO 9: Chat with Memory
**What it shows:** Interactive chat that uses your memories

```bash
memora chat
```

**Expected Interaction:**
```
🤖 MEMORA CHAT WITH MEMORY

You: What did we talk about yesterday?
Memora: Based on your memories, yesterday (2024-01-14) you discussed:
  - React hooks and state management
  - Python async/await patterns
  - REST API design principles
  
Would you like me to summarize any of these topics?

You: Tell me about React hooks
Memora: From your memories on React hooks:
  [Retrieves relevant memories and creates a summary]
  
Here's what you learned:
  - useState for managing component state
  - useEffect for side effects
  - useContext for global state
  - Custom hooks for code reuse
  
Your key notes:
  - "Hooks must be called at the top level"
  - "Dependencies array controls when effect runs"
  
Would you like to explore any specific hook in more detail?

You: exit
👋 Chat session ended. 3 new memories saved.
```

**What it demonstrates:**
- ✅ Interactive chat interface
- ✅ Memory-aware responses
- ✅ Historical context
- ✅ Automatic memory capture

---

### DEMO 10: Rollback (Undo Changes)
**What it shows:** Go back to any previous state

#### View rollback options:
```bash
memora log
```

#### Rollback to a specific commit:
```bash
memora rollback mem_abc123456789
```

**Expected Output:**
```
⚠️  ROLLBACK CONFIRMATION

Current State: 247 memories
Target State: 234 memories (from 2024-01-14 16:45:00)
Branch: main

This will:
✓ Remove 13 memories added after that point
✓ Keep all previous memories intact
✓ Create a new commit recording this rollback
✓ You can always roll forward again

Continue? [y/n]: y

✓ Rollback complete!
  Branch: main
  Total memories: 234 (was 247)
  New commit: mem_rollback123
  
Your previous state is still accessible:
  memora log --all  # Shows even rolled-back commits
```

#### Rollback to a time:
```bash
memora rollback --date "2024-01-12"
```

**What it demonstrates:**
- ✅ Time-based rollback
- ✅ Commit-based rollback
- ✅ Safe operations (confirmation required)
- ✅ Full history preservation

---

### DEMO 11: Export Memories
**What it shows:** Download your memories in different formats

#### Export to Markdown (human-readable):
```bash
memora export --format markdown --output memories.md
```

**Output (memories.md):**
```markdown
# My Memora Memories

Generated: 2024-01-15

## Python Best Practices (mem_xyz123)
- Source: OLLAMA_CHAT
- Created: 2024-01-15 14:32:00
- Type: CONVERSATION

In Python, best practices include using type hints, following PEP 8 guidelines...

### Entities
- Python, type hints, PEP 8, style guide

---

## React Hooks Patterns (mem_abc456)
- Source: FILE_INGESTION  
- Created: 2024-01-15 10:20:00
- Type: DOCUMENT

React hooks allow you to use state and other features without writing a class...

---
```

#### Export to JSON (structured):
```bash
memora export --format json --output memories.json
```

**Output (memories.json):**
```json
{
  "export_date": "2024-01-15T14:32:00Z",
  "format_version": "1.0",
  "branch": "main",
  "total_memories": 247,
  "memories": [
    {
      "id": "mem_xyz123",
      "content": "In Python, best practices include...",
      "type": "CONVERSATION",
      "source": "OLLAMA_CHAT",
      "created_at": "2024-01-15T14:32:00Z",
      "entities": ["Python", "type hints", "PEP 8"],
      "confidence": 0.95
    },
    ...
  ]
}
```

#### Export to TXT (plain text):
```bash
memora export --format txt --output memories.txt
```

#### Export specific branch:
```bash
memora export --branch feature/nlp-research --format markdown
```

**What it demonstrates:**
- ✅ Multi-format export
- ✅ Portable memories
- ✅ Backup capabilities
- ✅ Integration with other tools

---

### DEMO 12: Forget (Delete Memories)
**What it shows:** Selective memory deletion with safety checks

#### Delete a single memory:
```bash
memora forget mem_xyz789
```

**Expected Output:**
```
⚠️  DELETE CONFIRMATION

Memory: mem_xyz789
Content: "Python async/await patterns"
Created: 2024-01-15 10:20:00
Type: CONVERSATION

This will permanently delete this memory.
It cannot be recovered (but can be restored with rollback).

Continue? [y/n]: y

✓ Memory deleted: mem_xyz789
```

#### Delete by search query:
```bash
memora forget --search "outdated"
```

**Expected Output:**
```
🔍 Found 5 memories matching "outdated":

1. mem_old123 - "Old project info"
2. mem_old456 - "Deprecated API"
3. mem_old789 - "Legacy code"
4. mem_old321 - "Obsolete library"
5. mem_old654 - "Outdated best practices"

Delete all? [y/n]: y

✓ Deleted 5 memories
```

**What it demonstrates:**
- ✅ Safe deletion with confirmation
- ✅ Selective deletion
- ✅ Search-based deletion
- ✅ Fallback with rollback

---

### DEMO 13: Backup & Restore
**What it shows:** Safe data backups

#### Create a backup:
```bash
memora backup --output memora_backup_2024-01-15.zip
```

**Expected Output:**
```
📦 CREATING BACKUP

Source: ./memora_data
Output: memora_backup_2024-01-15.zip

Backing up:
  ✓ 247 memories
  ✓ 4 branches
  ✓ 18 sessions
  ✓ Knowledge graph
  ✓ All indices
  ✓ Configuration

Size:
  Uncompressed: 2.3 MB
  Compressed: 1.1 MB

✓ Backup complete: memora_backup_2024-01-15.zip
```

#### Restore from backup:
```bash
memora restore memora_backup_2024-01-15.zip --output ./restored_memora
```

**Expected Output:**
```
📥 RESTORING BACKUP

Source: memora_backup_2024-01-15.zip
Target: ./restored_memora

Verifying backup integrity... ✓
Extracting...
Validating data... ✓

✓ Restore complete!
  Location: ./restored_memora
  Memories: 247
  Branches: 4
  
You can now:
  memora start --memory-path ./restored_memora
```

**What it demonstrates:**
- ✅ Full system backups
- ✅ Compression
- ✅ Restoration
- ✅ Data integrity verification

---

### DEMO 14: Garbage Collection (Cleanup)
**What it shows:** Optimize storage

```bash
memora gc
```

**Expected Output:**
```
🧹 GARBAGE COLLECTION

Analyzing repository...
├─ Total objects: 312
├─ Referenced objects: 298
├─ Orphaned objects: 14
└─ Wasted space: 156 KB

Cleaning up...
  ✓ Removed 14 orphaned objects
  ✓ Freed 156 KB
  ✓ Recompressed indices

Results:
  Before: 2.3 MB
  After: 2.14 MB
  Saved: 156 KB (6.8%)

✓ Cleanup complete!
```

**What it demonstrates:**
- ✅ Storage optimization
- ✅ Orphaned object removal
- ✅ Space reclamation

---

### DEMO 15: Proxy Management
**What it shows:** Control how Memora captures memories

#### Start proxy:
```bash
memora proxy start --port 11435
```

#### Stop proxy:
```bash
memora proxy stop
```

#### View proxy status:
```bash
memora proxy status
```

**Expected Output:**
```
🌐 PROXY STATUS

Port: 11435
Status: Running ✓
Ollama Backend: http://localhost:11434 ✓

Active Sessions: 2
Total Conversations Captured: 247
Last Activity: 2024-01-15 14:32:00

Configuration:
  ├─ Auto-commit: Enabled
  ├─ PII Filtering: Enabled
  ├─ Entity Extraction: Enabled
  └─ Compression: Enabled

Memory Capture Rate: 42 memories/hour
```

#### Proxy setup for Ollama integration:
```bash
memora proxy-setup enable
```

**What it demonstrates:**
- ✅ Proxy lifecycle management
- ✅ Status monitoring
- ✅ Configuration

---

## 🔬 Advanced Features

### A. Conflict Resolution

When the same topic appears in multiple forms, Memora detects and resolves conflicts:

```bash
memora search "Python version" --show-conflicts
```

**Output:**
```
⚠️ CONFLICTS DETECTED

Query: "Python version"

Potential Conflict:
Memory 1: "Use Python 3.11 or later for type hints"
Memory 2: "Python 3.8+ supports all features"

Conflict Type: TEMPORAL_SUPERSESSION
Memory 2 is newer, likely supersedes Memory 1

Resolution:
✓ Auto-resolved (newer memory takes precedence)
✓ To use older version: memora search --date "before 2024-01-10"
```

### B. Entity Relationships

Understanding how concepts connect:

```bash
memora graph query "Python" --depth 3
```

Shows how Python connects to other concepts through 3 levels of relationships.

### C. Session Management

```bash
memora session list
memora session active
memora session close <session_id>
```

### D. Watch Directory for Auto-Ingestion

```bash
memora watch ./documents --pattern "*.pdf"
```

Auto-ingest files as they're added to a directory.

---

## 🎓 Learning Scenarios

### Scenario 1: Learning a New Language
1. Create a branch: `memora branch create "learning/rust"`
2. Ingest tutorials: `memora ingest rust_guide.pdf`
3. Chat with memories: `memora chat` → "What are Rust's ownership rules?"
4. Track progress: `memora stats`
5. Keep separate from other learning: memories isolated in this branch

### Scenario 2: Project Development
1. Create a branch: `memora branch create "project/ecommerce"`
2. Ingest requirements: `memora ingest requirements.txt`
3. Capture design decisions: use normal chat through proxy
4. Search architecture: `memora search "database design"`
5. Export for documentation: `memora export --format markdown`

### Scenario 3: Research
1. Create a branch: `memora branch create "research/ai-alignment"`
2. Ingest papers: `memora ingest papers/`
3. Query relationships: `memora graph query "alignment"`
4. Timeline of learning: `memora log`
5. Create branches for sub-topics

---

## 🐛 Troubleshooting

### Problem: "Port 11435 already in use"
```bash
# Use a different port
memora start --port 11436
```

### Problem: "Ollama not detected"
```bash
# Make sure Ollama is running
ollama serve

# In another terminal:
memora start
```

### Problem: "spaCy model not found"
```bash
# Download manually
python -m spacy download en_core_web_sm

# Then try again
memora start
```

### Problem: "Can't find memories"
```bash
# Check where memories are stored
memora where

# Make sure you're on the right branch
memora branch list

# View all memories
memora search ""
```

### Problem: "Want to reset everything"
```bash
# Delete all memories and start fresh
memora init --reset

# Confirm when prompted
# Then run memora start again
```

---

## 📚 Command Reference

### Setup & Management
| Command | What It Does |
|---------|-------------|
| `memora start` | One-command setup + start capturing |
| `memora init` | Initialize memory repository |
| `memora version` | Show version |
| `memora where` | Show storage location |
| `memora stats` | Show statistics |

### Search & Discovery
| Command | What It Does |
|---------|-------------|
| `memora search <query>` | Search by content |
| `memora when <time>` | Search by time |
| `memora graph` | View knowledge graph |
| `memora graph query <entity>` | Search by entity |

### Memory Management
| Command | What It Does |
|---------|-------------|
| `memora ingest <file>` | Add files to memory |
| `memora forget <id>` | Delete a memory |
| `memora chat` | Interactive chat with memory |

### Versioning
| Command | What It Does |
|---------|-------------|
| `memora branch list` | Show all branches |
| `memora branch create <name>` | Create a branch |
| `memora branch switch <name>` | Switch branch |
| `memora branch merge <name>` | Merge branch |
| `memora log` | Show commit history |
| `memora rollback <commit>` | Go back in time |

### Data Management
| Command | What It Does |
|---------|-------------|
| `memora export --format markdown` | Export memories |
| `memora backup` | Create backup |
| `memora restore <backup>` | Restore backup |
| `memora gc` | Cleanup storage |
| `memora proxy start` | Start memory capture |
| `memora proxy stop` | Stop capture |

---

## 💡 Pro Tips

1. **Use meaningful branch names**: `memora branch create "project/website-redesign"` instead of `branch1`

2. **Commit milestones**: `memora commit "Completed learning module on async programming"`

3. **Regular exports**: `memora export --format markdown` to have readable backups

4. **Search like a native speaker**: `memora search "how do I use async in Python?"` (natural language!)

5. **Graph queries for learning**: `memora graph query "React"` to see all connected concepts

6. **Session organization**: Keep sessions short (one topic per chat), they auto-commit when closed

7. **Backup before major changes**: `memora backup` before deleting or reorganizing

---

## 🚀 Next Steps

### For Users
1. Run `memora start`
2. Use Ollama normally - everything is captured!
3. Explore memories: `memora search "topic"`
4. Enjoy! 🎉

### For Power Users
1. Organize with branches: `memora branch create "project/name"`
2. Track learning: `memora log`, `memora stats`
3. Export for documentation: `memora export`
4. Build a personal knowledge base!

### For Developers
1. Extend with custom extractors
2. Add plugins via `memora.shared.interfaces`
3. Integrate into your tools
4. Contribute improvements!

---

## 📖 Additional Resources

- **GitHub**: https://github.com/memora-ai/memora
- **Issues**: Report bugs or suggest features
- **Architecture Docs**: See ARCHITECTURE.md for technical details

---

## 🎉 That's All!

You now know every feature of Memora. Each feature is designed to make your LLM interactions:

- **Searchable**: Find anything instantly
- **Organized**: Branches for different projects
- **Versioned**: Full history with rollback
- **Private**: Everything stays on your computer
- **Easy**: Single command to start

Start exploring! 🚀

```bash
memora start
```

---

**Happy learning! 🧠**

*Memora v3.1.0 - Your personal AI memory system*
