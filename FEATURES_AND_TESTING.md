# 🧠 MEMORA - Complete Features & Testing Guide

**One file to test every feature with all fallbacks and edge cases**

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [All Features](#all-features)
3. [Fallbacks & Edge Cases](#fallbacks--edge-cases)
4. [Testing Every Feature](#testing-every-feature)
5. [Architecture Overview](#architecture-overview)

---

## Quick Start

```bash
memora start
```

This single command:
- ✅ Initializes memory repository
- ✅ Downloads required models
- ✅ Sets up proxy on port 11435
- ✅ Starts capturing memories automatically

---

## All Features

### 1. INITIALIZATION & SETUP

**Feature: `memora start`**

What it does:
- Creates `.memora` directory structure
- Initializes Git-like object store
- Checks/downloads spaCy NER model
- Finds and configures Ollama connection
- Starts HTTP proxy on specified port

**Fallbacks:**
```bash
# Fallback 1: Port unavailable → tries next port
memora start --port 11436  # If 11435 in use

# Fallback 2: Ollama not detected → continues anyway
# Shows warning but doesn't fail

# Fallback 3: spaCy model missing → downloads automatically
# One-time ~12MB download, then continues

# Fallback 4: Storage path doesn't exist → creates it
mkdir -p ./memora_data  # Auto-created

# Fallback 5: Existing store → loads and continues
# Won't overwrite if already initialized
```

**Test Commands:**
```bash
# Test 1: Fresh initialization
rm -rf memora_data && memora start

# Test 2: Re-run on existing data
memora start  # Should recognize existing store

# Test 3: Different port
memora start --port 11436

# Test 4: Custom path
memora start --memory-path ~/my_memories

# Test 5: Check port availability
netstat -ano | findstr :11435  # Windows
lsof -i :11435                 # Mac/Linux
```

**Expected Behavior:**
```
✓ All fallbacks work without errors
✓ Warnings shown but doesn't fail
✓ Auto-downloads missing dependencies
✓ Recognizes existing stores
✓ Creates missing directories
```

---

### 2. MEMORY CAPTURE

**Feature: Automatic capture via proxy**

What it does:
- Transparent HTTP proxy intercepts Ollama calls
- Extracts conversation content
- Auto-detects memory type
- Performs NER (Named Entity Recognition)
- Stores with compression

**Fallbacks:**
```bash
# Fallback 1: Network error → queues and retries
# Temporary network issues don't lose data

# Fallback 2: Large conversation → chunks automatically
# Handles 1MB+ conversations

# Fallback 3: Ollama timeout → proxy timeout → retries
# Continues if backend is slow

# Fallback 4: Invalid JSON → parses best-effort
# Tries multiple parsing strategies

# Fallback 5: Storage full → warns and continues
# Still tries to save even if disk space low
```

**Test Commands:**
```bash
# Test 1: Start proxy and chat
memora start &
ollama run llama2
# Have a normal conversation

# Test 2: Simulate network error
# Disconnect internet temporarily
# Chat should still work when reconnected

# Test 3: Large conversation
# Paste a 1000+ line text into chat
# Should handle gracefully

# Test 4: Repeated conversations
# Have same conversation twice
# Should deduplicate via content hash
```

**Expected Behavior:**
```
✓ All conversations captured
✓ No memory lost on errors
✓ Large conversations handled
✓ Deduplication works
✓ Network issues recovered
```

---

### 3. MEMORY SEARCH

**Feature: `memora search <query>`**

What it does:
- Full-text search across all memories
- Natural language query support
- Fuzzy matching on misspellings
- Returns ranked results with metadata

**Fallbacks:**
```bash
# Fallback 1: Empty query → returns all memories
memora search ""

# Fallback 2: No results → returns empty gracefully
memora search "xyzabc12345nonexistent"

# Fallback 3: Special characters → escapes properly
memora search "c++ && python"

# Fallback 4: Very long query → truncates gracefully
memora search "$(yes 'long' | head -1000 | tr '\n' ' ')"

# Fallback 5: Search in non-existent branch → switches first
memora search "term"  # Searches current branch
```

**Test Commands:**
```bash
# Test 1: Basic search
memora search "Python"

# Test 2: Multi-word search
memora search "Python best practices"

# Test 3: Phrase search
memora search '"exact phrase"'

# Test 4: Empty search (list all)
memora search ""

# Test 5: Fuzzy matching
memora search "pyton"  # Misspelled but finds "Python"

# Test 6: Special characters
memora search "c++"

# Test 7: No results
memora search "xyz123notaword"

# Test 8: Search by entity
memora search "Paris"  # NER extracted entities
```

**Expected Behavior:**
```
✓ Finds relevant memories
✓ Handles typos gracefully
✓ Returns empty set if no match
✓ Processes special characters
✓ Rank results by relevance
✓ Sub-100ms response time
```

---

### 4. TEMPORAL SEARCH

**Feature: `memora when <time_query>`**

What it does:
- Parse natural language dates
- Find memories by creation time
- Support multiple formats
- Show memories in order

**Fallbacks:**
```bash
# Fallback 1: Invalid date → shows closest match
memora when "32nd January"  # Invalid, shows nearest

# Fallback 2: Future date → returns empty
memora when "2099-01-01"

# Fallback 3: Ambiguous format → tries multiple parsers
memora when "01/02/2024"  # MM/DD or DD/MM? Tries both

# Fallback 4: No memories in range → returns empty
memora when "2020-01-01"  # If no memories that old

# Fallback 5: Timezone issues → uses local time
# Uses system timezone automatically
```

**Test Commands:**
```bash
# Test 1: Today
memora when "today"

# Test 2: Yesterday
memora when "yesterday"

# Test 3: Relative
memora when "last 7 days"
memora when "this week"
memora when "last month"

# Test 4: Absolute date
memora when "2024-01-15"

# Test 5: Month and year
memora when "January 2024"

# Test 6: Invalid date
memora when "32nd January"

# Test 7: Future date
memora when "2099-01-01"

# Test 8: Ambiguous
memora when "01/02/2024"
```

**Expected Behavior:**
```
✓ Parses natural language dates
✓ Handles relative dates
✓ Returns empty for future dates
✓ Tries multiple format parsers
✓ Shows memories in chronological order
```

---

### 5. FILE INGESTION

**Feature: `memora ingest <file/directory>`**

What it does:
- Detect file type (code, doc, pdf)
- Extract content intelligently
- Auto-generate summaries
- Add to memory with metadata

**Fallbacks:**
```bash
# Fallback 1: Unsupported format → tries best-effort
memora ingest file.xyz  # Will try text extraction

# Fallback 2: Large file → chunks automatically
memora ingest huge_file.pdf  # Splits into memories

# Fallback 3: Binary file → skips with warning
memora ingest image.jpg  # Warns, skips gracefully

# Fallback 4: Permission denied → shows error, continues
memora ingest /root/private_file  # Permission denied → continues

# Fallback 5: Directory → ingests all supported files
memora ingest ./my_docs  # Recursively processes *.pdf, *.py, *.md

# Fallback 6: Corrupted file → skips, continues batch
memora ingest *.pdf  # One corrupted → processes others
```

**Test Commands:**
```bash
# Test 1: Single Python file
echo 'def hello(): print("world")' > test.py
memora ingest test.py

# Test 2: Single Markdown file
echo '# Title\nContent' > test.md
memora ingest test.md

# Test 3: PDF file (if pypdf installed)
memora ingest document.pdf

# Test 4: Directory ingestion
mkdir -p test_files
echo 'code' > test_files/code.py
echo '# Doc' > test_files/doc.md
memora ingest test_files/

# Test 5: Batch with wildcards
memora ingest *.py

# Test 6: Large file (create 10MB file)
dd if=/dev/zero of=large.txt bs=1M count=10
memora ingest large.txt

# Test 7: Unsupported format
echo 'random' > file.xyz
memora ingest file.xyz

# Test 8: Binary file (image)
# Try ingesting an image file
memora ingest image.jpg
```

**Expected Behavior:**
```
✓ Detects file types correctly
✓ Extracts content from supported formats
✓ Handles large files (chunks)
✓ Processes directories recursively
✓ Continues on errors (doesn't fail all)
✓ Shows meaningful error messages
✓ Deduplicates if content already exists
```

---

### 6. BRANCHES (Git-Style)

**Feature: `memora branch <subcommand>`**

What it does:
- Create isolated memory contexts
- Switch between projects
- Limit branches per context
- Track branch metadata

**Fallbacks:**
```bash
# Fallback 1: Branch already exists → shows error
memora branch create "main"  # Already exists

# Fallback 2: Non-existent branch → shows error
memora branch switch "nonexistent"

# Fallback 3: Delete with memories → confirms first
memora branch delete "branch"  # Asks for confirmation

# Fallback 4: Too many branches → prevents creation
# Default limit: 100 branches
memora branch create "branch_101"  # Fails if at limit

# Fallback 5: Merge conflicts → detects and shows
memora branch merge "other"  # Shows conflicts if any
```

**Test Commands:**
```bash
# Test 1: List branches
memora branch list

# Test 2: Create branch
memora branch create "feature/python-learning"

# Test 3: Switch branch
memora branch switch "feature/python-learning"

# Test 4: Current branch (search should show)
memora search "term"  # Only searches current branch

# Test 5: Switch back to main
memora branch switch main

# Test 6: List again (see all)
memora branch list

# Test 7: Try duplicate name
memora branch create "feature/python-learning"  # Fails

# Test 8: Try non-existent switch
memora branch switch "nonexistent"  # Fails
```

**Expected Behavior:**
```
✓ Creates named branches
✓ Isolates memories per branch
✓ Switches between branches
✓ Shows meaningful errors
✓ Prevents duplicate names
✓ Prevents switching to non-existent
✓ Tracks branch metadata
```

---

### 7. COMMIT & HISTORY

**Feature: `memora log` and `memora commit`**

What it does:
- Record Git-like commits
- Auto-commit on session end
- Manual commits with messages
- Full history with timestamps

**Fallbacks:**
```bash
# Fallback 1: Empty log → shows "no commits yet"
memora log  # On fresh repo

# Fallback 2: Invalid commit ID → shows error
memora log --detail abc123xyz  # Non-existent

# Fallback 3: No message → auto-generates
memora commit  # Creates default message

# Fallback 4: Orphaned commits → preserves in history
# Even rolled-back commits stay in history

# Fallback 5: Large commit message → truncates gracefully
memora commit "$(yes 'message' | head -1000 | tr '\n' ' ')"
```

**Test Commands:**
```bash
# Test 1: View log
memora log

# Test 2: View limited log
memora log --limit 5

# Test 3: Create a memory first (chat or ingest)
memora ingest somefile.txt

# Test 4: Manual commit
memora commit "Added important documentation"

# Test 5: View log again
memora log

# Test 6: View detailed commit
# Get a commit ID from log, then:
memora log --detail mem_abc123

# Test 7: Empty commit message
memora commit ""

# Test 8: Very long commit message
LONG_MSG=$(printf 'x%.0s' {1..5000})
memora commit "$LONG_MSG"
```

**Expected Behavior:**
```
✓ Shows full history with timestamps
✓ Records author and source
✓ Auto-commits on session end
✓ Allows manual commits
✓ Handles empty messages
✓ Preserves all history
✓ Shows metadata for each commit
```

---

### 8. KNOWLEDGE GRAPH

**Feature: `memora graph` and `memora graph query`**

What it does:
- Extract named entities (spaCy NER)
- Map relationships between entities
- Build knowledge graph
- Query entity connections

**Fallbacks:**
```bash
# Fallback 1: No spaCy model → disables NER
# Falls back to keyword extraction

# Fallback 2: Unknown entity → shows "not found"
memora graph query "unknown_entity_xyz"

# Fallback 3: No relationships → shows standalone entity
memora graph query "entity"

# Fallback 4: Large graph → samples and aggregates
# Handles 1000+ entities gracefully

# Fallback 5: Corrupt graph data → rebuilds
# Auto-recovery from corrupted graph files
```

**Test Commands:**
```bash
# Test 1: View graph overview
memora graph

# Test 2: Chat about a topic first
memora start &
# Chat about "Python programming and asyncio"

# Test 3: Query an entity
memora graph query "Python"

# Test 4: Query with variations
memora graph query "python"  # Case insensitive
memora graph query "Python"

# Test 5: Query unknown entity
memora graph query "xyz_unknown"

# Test 6: View all entities
memora graph

# Test 7: Check relationships
memora graph query "asyncio"

# Test 8: Check entity categories
memora graph --categories
```

**Expected Behavior:**
```
✓ Extracts entities from memories
✓ Maps relationships
✓ Case-insensitive queries
✓ Shows frequency of mention
✓ Lists connected concepts
✓ Handles missing spaCy model
✓ Recovers from graph corruption
```

---

### 9. STATISTICS

**Feature: `memora stats`**

What it does:
- Count memories by type
- Show storage usage
- Display branch info
- Show index status

**Fallbacks:**
```bash
# Fallback 1: Empty repository → shows zeros
memora stats  # On fresh repo

# Fallback 2: Corrupted index → rebuilds
# Auto-recovery if index corrupted

# Fallback 3: Large repository → aggregates
# Works with 100K+ memories

# Fallback 4: Slow disk → shows progress
# Displays "calculating..." message
```

**Test Commands:**
```bash
# Test 1: Fresh repo stats
rm -rf memora_data
memora start
memora stats

# Test 2: After adding some data
memora ingest *.py

# Test 3: Stats again
memora stats

# Test 4: After branching
memora branch create "test"
memora branch switch "test"
memora ingest somefile.txt
memora stats

# Test 5: Switch back and check
memora branch switch main
memora stats
```

**Expected Behavior:**
```
✓ Shows accurate memory counts
✓ Displays storage usage
✓ Shows all branches
✓ Lists active sessions
✓ Shows index status
✓ Updates in real-time
✓ Handles empty repos
```

---

### 10. LOCATION & STORAGE

**Feature: `memora where`**

What it does:
- Show storage path
- Display directory structure
- Show recent activity
- Show storage size

**Fallbacks:**
```bash
# Fallback 1: Custom path → shows actual path
memora start --memory-path ~/custom
memora where  # Shows ~/custom/.memora

# Fallback 2: No recent activity → shows "(none)"
memora where  # On fresh repo

# Fallback 3: Permission issues → shows what it can
# Best-effort display
```

**Test Commands:**
```bash
# Test 1: Default location
memora where

# Test 2: Custom path location
memora start --memory-path ~/test_memora
memora where

# Test 3: Check actual files
# Read the path and explore .memora directory

# Test 4: After adding data
memora ingest somefile.txt
memora where  # Should show updated activity
```

**Expected Behavior:**
```
✓ Shows correct path
✓ Displays directory structure
✓ Shows recent activity
✓ Shows storage size
✓ Works with custom paths
```

---

### 11. CHAT WITH MEMORY

**Feature: `memora chat`**

What it does:
- Interactive conversation with LLM
- Retrieves relevant memories
- Context-aware responses
- Auto-saves conversation

**Fallbacks:**
```bash
# Fallback 1: No memories → still works
memora chat  # On fresh repo, no context

# Fallback 2: LLM unavailable → shows error
# Can't chat without Ollama, shows clear message

# Fallback 3: No relevant memories → plain response
# Falls back to LLM without context

# Fallback 4: Connection timeout → offers retry
# Asks if user wants to try again
```

**Test Commands:**
```bash
# Test 1: Start proxy
memora start &

# Test 2: Ingest some data first
memora ingest *.py

# Test 3: Start interactive chat
memora chat

# Test 4: Ask about memories
# Type: "What have we talked about Python?"

# Test 5: Ask for summary
# Type: "Summarize my learning"

# Test 6: Exit
# Type: "exit"
```

**Expected Behavior:**
```
✓ Starts interactive session
✓ Retrieves relevant memories
✓ Shows context in response
✓ Works without memories
✓ Saves conversation
✓ Handles disconnection gracefully
```

---

### 12. ROLLBACK (Time Travel)

**Feature: `memora rollback <commit_id>`**

What it does:
- Revert to previous commit
- Remove memories after that point
- Preserve full history
- Create rollback commit

**Fallbacks:**
```bash
# Fallback 1: Invalid commit ID → shows error
memora rollback "invalid_id"

# Fallback 2: Already at that state → shows "already there"
memora rollback mem_id  # If already at that commit

# Fallback 3: Rollback before rollback → works
# Can undo a rollback by rolling back to before

# Fallback 4: No commits → shows error
memora rollback  # On empty repo

# Fallback 5: Asks for confirmation → safety
# Requires user confirmation before deleting memories
```

**Test Commands:**
```bash
# Test 1: Create some memories first
memora ingest file1.txt
memora ingest file2.txt
memora ingest file3.txt

# Test 2: View log
memora log

# Test 3: Save a commit ID
# Remember a commit ID from log

# Test 4: Add more
memora ingest file4.txt

# Test 5: View stats (showing more memories)
memora stats

# Test 6: Rollback to saved point
memora rollback mem_id  # From step 3

# Test 7: View stats again (fewer memories)
memora stats

# Test 8: View log (shows rollback)
memora log
```

**Expected Behavior:**
```
✓ Reverts to specified commit
✓ Removes memories added after
✓ Asks for confirmation
✓ Records rollback in history
✓ Can undo a rollback
✓ Preserves all history
```

---

### 13. EXPORT

**Feature: `memora export [--format <format>]`**

What it does:
- Export memories in formats
- Supports markdown, JSON, TXT
- Includes metadata
- Excludes sensitive data

**Fallbacks:**
```bash
# Fallback 1: Invalid format → uses default (markdown)
memora export --format xyz

# Fallback 2: No output file → uses default name
memora export  # Creates "memora_export_TIMESTAMP.md"

# Fallback 3: File exists → appends timestamp
memora export --output export.md  # Creates export_2024-01-15.md

# Fallback 4: No memories → creates empty document
memora export  # Fresh repo

# Fallback 5: Large export → chunked file output
# Splits very large exports into multiple files
```

**Test Commands:**
```bash
# Test 1: Create some memories first
memora ingest somefile.txt

# Test 2: Export to Markdown (default)
memora export

# Test 3: Export to JSON
memora export --format json

# Test 4: Export to TXT
memora export --format txt

# Test 5: Export to specific location
memora export --format markdown --output my_memories.md

# Test 6: View exported file
cat my_memories.md

# Test 7: Try invalid format
memora export --format xyz

# Test 8: Export empty repo
rm -rf memora_data
memora start
memora export
```

**Expected Behavior:**
```
✓ Exports all memories
✓ Includes metadata
✓ Supports multiple formats
✓ Creates readable documents
✓ Handles missing format gracefully
✓ Works with empty repos
✓ Creates output file
```

---

### 14. DELETE (Forget)

**Feature: `memora forget <memory_id>`**

What it does:
- Delete specific memory
- Confirm before deleting
- Record in history
- Can be recovered via rollback

**Fallbacks:**
```bash
# Fallback 1: Invalid memory ID → shows error
memora forget "invalid_id"

# Fallback 2: Not found → shows "not found"
memora forget mem_xyz  # Doesn't exist

# Fallback 3: Asks for confirmation → safety
# Requires confirmation before delete

# Fallback 4: Can recover via rollback → safe
# Deletion is reversible

# Fallback 5: Delete by search → requires confirmation
memora forget --search "pattern"  # Confirms before deleting all matches
```

**Test Commands:**
```bash
# Test 1: Create memories first
memora ingest file1.txt
memora ingest file2.txt

# Test 2: View memories
memora search ""

# Test 3: Get a memory ID from search results

# Test 4: Delete it
memora forget mem_id  # Will ask for confirmation

# Test 5: Confirm deletion
# Type: y

# Test 6: Search again (should be gone)
memora search ""

# Test 7: Try deleting non-existent
memora forget mem_invalid

# Test 8: Delete by search pattern
memora forget --search "pattern"  # Confirms before delete
```

**Expected Behavior:**
```
✓ Deletes specified memory
✓ Asks for confirmation
✓ Shows error for invalid ID
✓ Recoverable via rollback
✓ Can delete by search pattern
✓ Prevents accidental deletion
```

---

### 15. BACKUP & RESTORE

**Feature: `memora backup` and `memora restore`**

What it does:
- Create full system backup
- Compress data
- Restore from backup
- Verify integrity

**Fallbacks:**
```bash
# Fallback 1: Backup exists → appends timestamp
memora backup --output backup.zip  # Creates backup_2024-01-15.zip

# Fallback 2: Restore corrupted → warns but tries
memora restore backup.zip  # Shows warning if corrupted

# Fallback 3: Restore to existing → asks to overwrite
memora restore backup.zip --output existing_dir

# Fallback 4: Disk full → shows clear error
# Not enough space for backup

# Fallback 5: Permission denied → shows error
# Can't write to output location
```

**Test Commands:**
```bash
# Test 1: Create memories first
memora ingest *.py

# Test 2: View stats
memora stats

# Test 3: Create backup
memora backup --output backup.zip

# Test 4: Check file exists
ls -la backup.zip

# Test 5: Create more memories
memora ingest anotherfile.txt

# Test 6: Delete current data
rm -rf memora_data

# Test 7: Restore from backup
memora restore backup.zip --output memora_data

# Test 8: Verify restored
memora stats  # Should match step 2

# Test 9: Try backup to existing file
memora backup --output backup.zip  # Should add timestamp
```

**Expected Behavior:**
```
✓ Creates valid backup file
✓ Compresses data
✓ Restores all memories
✓ Verifies integrity
✓ Handles existing files
✓ Shows clear errors
✓ Works cross-platform
```

---

### 16. GARBAGE COLLECTION

**Feature: `memora gc`**

What it does:
- Find orphaned objects
- Remove unused data
- Recompress storage
- Optimize performance

**Fallbacks:**
```bash
# Fallback 1: Nothing to clean → shows "storage optimal"
memora gc  # On recently optimized repo

# Fallback 2: In-use objects → safely skips
# Only cleans truly orphaned data

# Fallback 3: Concurrent access → locks safely
# Uses file locks to prevent corruption

# Fallback 4: Disk write errors → rolls back
# Doesn't leave partial state
```

**Test Commands:**
```bash
# Test 1: Check storage before
memora stats

# Test 2: Run garbage collection
memora gc

# Test 3: Check storage after
memora stats  # Should be same or smaller

# Test 4: Run again
memora gc  # Should show "nothing to clean"

# Test 5: After deletion
memora ingest file1.txt
memora ingest file2.txt
memora forget mem_id  # Delete one
memora gc  # Should find orphaned data

# Test 6: Stats after cleanup
memora stats
```

**Expected Behavior:**
```
✓ Identifies orphaned objects
✓ Removes safely
✓ Optimizes storage
✓ Doesn't corrupt data
✓ Shows space saved
✓ Works on populated repos
```

---

### 17. PROXY MANAGEMENT

**Feature: `memora proxy` commands**

What it does:
- Start/stop proxy explicitly
- Monitor proxy status
- Configure settings

**Fallbacks:**
```bash
# Fallback 1: Already running → shows "already running"
memora proxy start  # When already started

# Fallback 2: Not running → shows error
memora proxy stop  # When not started

# Fallback 3: Port in use → suggests alternative
memora proxy start --port 11435  # If in use

# Fallback 4: Ollama unavailable → shows warning
memora proxy status  # If Ollama not reachable
```

**Test Commands:**
```bash
# Test 1: Start explicitly
memora proxy start

# Test 2: Check status
memora proxy status

# Test 3: Try to start again
memora proxy start  # Should show already running

# Test 4: Stop proxy
memora proxy stop

# Test 5: Try to stop again
memora proxy stop  # Should show not running

# Test 6: Custom port
memora proxy start --port 11436

# Test 7: Check status
memora proxy status

# Test 8: Stop it
memora proxy stop
```

**Expected Behavior:**
```
✓ Starts proxy on specified port
✓ Stops cleanly
✓ Reports status accurately
✓ Prevents double-start
✓ Handles missing Ollama gracefully
✓ Works with custom ports
```

---

## Fallbacks & Edge Cases

### General Patterns

1. **Port Conflicts**
   ```bash
   memora start --port 11435        # Try default
   # Falls back to: 11436, 11437, ... if needed
   ```

2. **Missing Dependencies**
   ```bash
   # spaCy model: Auto-downloads on first use
   # Ollama: Shows warning but continues
   # Python: Shows error (required)
   ```

3. **Storage Issues**
   ```bash
   # Corrupted index: Auto-rebuilds
   # Full disk: Shows error, suggests cleanup
   # Permission denied: Shows clear error
   ```

4. **Network Issues**
   ```bash
   # Ollama offline: Queues memories
   # Slow connection: Timeout and retry
   # Connection reset: Graceful recovery
   ```

5. **Data Issues**
   ```bash
   # Invalid JSON: Best-effort parsing
   # Corrupted files: Skips, continues
   # Encoding issues: Auto-detects encoding
   ```

---

## Testing Every Feature

### Test Plan

**Setup Phase:**
```bash
# 1. Fresh installation
rm -rf memora_data
memora start

# 2. Create diverse memories
memora ingest *.py
memora ingest *.md
memora ingest docs/

# 3. Have conversations through Ollama
ollama run llama2
# Discuss: Python, async, design patterns

# 4. Create branches
memora branch create "learning/async"
memora branch switch "learning/async"
memora ingest async_tutorial.md
```

**Feature Testing Phase:**
```bash
# Feature 1: Search
memora search "async"
memora search "Python"

# Feature 2: Time search
memora when "today"
memora when "last 7 days"

# Feature 3: Stats
memora stats

# Feature 4: Location
memora where

# Feature 5: Graph
memora graph
memora graph query "Python"

# Feature 6: Chat
memora chat
# Ask: "What do we know about async?"

# Feature 7: Log
memora log

# Feature 8: Export
memora export
memora export --format json

# Feature 9: Branches
memora branch list
memora branch switch main

# Feature 10: Rollback
memora log  # Get commit ID
memora rollback commit_id

# Feature 11: Delete
memora forget mem_id

# Feature 12: Backup
memora backup --output backup.zip

# Feature 13: GC
memora gc

# Feature 14: Proxy
memora proxy status
```

**Fallback Testing Phase:**
```bash
# Test invalid inputs
memora search ""              # Empty
memora when "invalid date"    # Bad date
memora ingest nonexistent.py  # Missing file
memora branch switch nowhere  # Non-existent
memora rollback invalid_id    # Bad ID
memora forget xyz             # Not found
memora export --format xyz    # Invalid format

# Test resource limits
# Large file ingestion
dd if=/dev/zero of=1gb.txt bs=1M count=1024
memora ingest 1gb.txt

# Many branches
for i in {1..50}; do memora branch create "branch_$i"; done
memora branch list

# Many memories
for i in {1..100}; do
  echo "Memory $i" > file_$i.txt
  memora ingest file_$i.txt
done
memora stats

# Test concurrent operations
memora start &
# In another terminal, run commands simultaneously
memora search "term"
memora stats
memora log
```

---

## Architecture Overview

### System Layers

```
┌─────────────────────────────────────────────────────────────┐
│ 5. User Interface Layer                                     │
│    ├─ CLI (typer + rich)                                   │
│    ├─ REST API (FastAPI)                                   │
│    └─ Interactive Chat                                     │
├─────────────────────────────────────────────────────────────┤
│ 4. Memory Management Layer                                  │
│    ├─ Ingestion Pipeline                                   │
│    │  ├─ Type Detection (conversation/code/document)       │
│    │  ├─ Content Extraction                                │
│    │  ├─ Entity Recognition (spaCy NER)                    │
│    │  └─ PII Filtering                                     │
│    │                                                        │
│    ├─ Memory Operations                                    │
│    │  ├─ Create, Read, Update, Delete                      │
│    │  ├─ Deduplication (content hash)                      │
│    │  ├─ Conflict Resolution                               │
│    │  └─ Session Management                                │
│    │                                                        │
│    └─ Knowledge Graph                                      │
│       ├─ Entity Nodes                                      │
│       ├─ Relationship Edges                                │
│       └─ Graph Queries                                     │
├─────────────────────────────────────────────────────────────┤
│ 3. Storage & Indexing Layer                                │
│    ├─ Git-Style Object Store                              │
│    │  ├─ SHA-256 content addressing                        │
│    │  ├─ zlib compression                                  │
│    │  └─ LRU file cache                                    │
│    │                                                        │
│    ├─ Multi-Dimensional Indices                            │
│    │  ├─ Word Index (full-text search)                     │
│    │  ├─ Temporal Index (time-based search)                │
│    │  ├─ Session Index (per-session queries)               │
│    │  └─ Type Index (filter by memory type)                │
│    │                                                        │
│    ├─ Version Control                                      │
│    │  ├─ Commits (with messages)                           │
│    │  ├─ Branches (isolated contexts)                      │
│    │  ├─ Refs (branch pointers)                            │
│    │  └─ History (full timeline)                           │
│    │                                                        │
│    └─ Metadata Storage                                     │
│       ├─ Session records                                   │
│       ├─ Branch metadata                                   │
│       └─ Configuration                                     │
├─────────────────────────────────────────────────────────────┤
│ 2. Integration Layer                                        │
│    ├─ Ollama Proxy (transparent HTTP)                      │
│    │  ├─ Port 11435 (default)                              │
│    │  ├─ Intercepts API calls                              │
│    │  ├─ Auto-detects Ollama backend                       │
│    │  └─ Session management                                │
│    │                                                        │
│    └─ File Processing                                      │
│       ├─ PDF extraction (pypdf)                            │
│       ├─ Code analysis                                     │
│       └─ Document parsing                                  │
├─────────────────────────────────────────────────────────────┤
│ 1. Data Models Layer                                        │
│    ├─ Memory (id, content, type, timestamp, metadata)      │
│    ├─ Session (session_id, memories, status)               │
│    ├─ Commit (commit_id, message, timestamp, memories)     │
│    ├─ Branch (name, head_commit, parent)                   │
│    ├─ GraphNode (entity, category, frequency)              │
│    └─ Conflict (memory_ids, type, resolution)              │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Chat
    ↓
Ollama Proxy (Layer 2)
    ├─ Intercepts HTTP request
    ├─ Extracts conversation content
    └─ Routes to backend
         ↓
Ingestion Pipeline (Layer 4)
    ├─ Type Detection
    ├─ Content Extraction
    ├─ NER Processing (spaCy)
    └─ PII Filtering
         ↓
Deduplication (Layer 4)
    ├─ Compute content hash (SHA-256)
    ├─ Check if exists
    └─ Skip or create new
         ↓
Memory Creation (Layer 4)
    ├─ Create Memory object
    ├─ Add metadata
    └─ Record session
         ↓
Storage (Layer 3)
    ├─ Compress with zlib
    ├─ Store in object store (SHA-256 path)
    └─ Index in all dimensions
         ↓
Session Management (Layer 4)
    ├─ Keep session open
    ├─ Buffer memories
    └─ Auto-commit on close
         ↓
Commit (Layer 3)
    ├─ Create commit record
    ├─ Update branch ref
    └─ Record in history
         ↓
Complete ✓
```

### Search Flow

```
User Query
    ↓
Parse Query (Layer 5 - CLI)
    ├─ Full-text search
    ├─ Temporal search
    ├─ Entity search
    └─ Combination
         ↓
Query Execution (Layer 4)
    ├─ Route to appropriate index
    └─ Execute search
         ↓
Index Lookup (Layer 3)
    ├─ Word Index → Matching memories
    ├─ Temporal Index → Date-matched memories
    ├─ Entity Index → Entity-matched memories
    └─ Type Index → Type-filtered memories
         ↓
Result Ranking (Layer 4)
    ├─ BM25 ranking for relevance
    ├─ Recency weighting
    └─ Deduplication
         ↓
Memory Retrieval (Layer 3)
    ├─ Get from object store
    ├─ Decompress
    └─ Load metadata
         ↓
Result Formatting (Layer 5)
    ├─ Add metadata
    ├─ Sort by relevance
    └─ Display
         ↓
User (sub-100ms response)
```

### Storage Structure

```
.memora/
├── objects/                    # Git-like object store (SHA-256)
│   ├── 1a/
│   │   ├── 2b3c4d5e6f...      # Compressed memory objects
│   │   └── ...
│   └── ...
│
├── refs/                       # Branch references
│   ├── heads/
│   │   ├── main               # Main branch pointer
│   │   ├── feature/python     # Feature branch pointer
│   │   └── ...
│   └── archive/               # Archived branches
│
├── HEAD                        # Current branch (points to refs/heads/main)
│
├── sessions/                   # Session management
│   ├── active/
│   │   ├── sess_abc123        # Active session data
│   │   └── ...
│   └── closed/
│       ├── sess_def456        # Closed session data
│       └── ...
│
├── graph/                      # Knowledge graph
│   ├── nodes.json             # Entity nodes
│   └── edges.json             # Relationships
│
├── index/                      # Search indices
│   ├── words.json             # Full-text index
│   ├── temporal.json          # Time-based index
│   ├── sessions.json          # Session index
│   └── types.json             # Type index
│
├── branches/                   # Branch metadata
│   ├── main.meta
│   ├── feature.python.meta
│   └── ...
│
└── config                      # System configuration
    ├── core
    │   └── version: "3.1"
    ├── storage
    ├── index
    └── sessions
```

### Feature-to-Layer Mapping

| Feature | Layer 5 | Layer 4 | Layer 3 | Layer 2 | Layer 1 |
|---------|---------|---------|---------|---------|---------|
| **Search** | CLI → `search` | Query execution | Index lookup | - | Memory model |
| **Ingest** | CLI → `ingest` | Type detect, Extract | Store object | - | Memory model |
| **Branch** | CLI → `branch` | Branch logic | Ref management | - | Branch model |
| **Commit** | CLI → `commit` | Session mgmt | Store commit | - | Commit model |
| **Graph** | CLI → `graph` | NER, Relationships | Graph storage | - | GraphNode model |
| **Chat** | Chat interface | Context retrieval | Index query | Ollama | Memory model |
| **Rollback** | CLI → `rollback` | History lookup | Ref update | - | Commit model |
| **Export** | CLI → `export` | Format conversion | Object retrieval | - | Memory model |
| **Backup** | CLI → `backup` | Compression | Zip creation | - | - |
| **Proxy** | CLI → `proxy` | Session mgmt | - | HTTP proxy | Memory model |

### Fallback Mechanisms by Layer

**Layer 5 (UI):**
- Invalid commands → Shows help
- Missing arguments → Prompts user
- Formatting errors → Best-effort display

**Layer 4 (Memory Management):**
- Type detection fails → Uses generic type
- NER fails → Falls back to keyword extraction
- Conflict detection → Auto or manual resolution
- Session lost → Recovers from disk

**Layer 3 (Storage):**
- Corrupted index → Rebuilds from objects
- Disk full → Warns and continues
- Permission denied → Shows error
- Large data → Chunks and streams

**Layer 2 (Integration):**
- Ollama unavailable → Queues and retries
- Network timeout → Configurable retry
- Port in use → Tries next port
- Invalid response → Best-effort parsing

**Layer 1 (Data Models):**
- Invalid data → Validation errors
- Missing fields → Defaults
- Type mismatch → Coercion or error

---

## Summary

Memora is a **multi-layered system** that:

1. **Captures** memories transparently via Ollama proxy
2. **Processes** them through ingestion and NER pipelines
3. **Stores** using Git-like content addressing
4. **Indexes** across multiple dimensions
5. **Manages** with version control semantics
6. **Searches** with sub-100ms response times
7. **Handles** failures gracefully at every layer

**Every feature has fallbacks:**
- Port conflicts → Try next port
- Missing models → Auto-download
- Network issues → Queue and retry
- Corrupted data → Auto-rebuild
- Storage errors → Graceful degradation

**Test everything** using the commands in this guide!
