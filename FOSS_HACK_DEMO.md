# FOSS Hack Video Recording Script - Memora

**Version**: 3.1.0  
**Focus**: Automatic memory capture + Git-style versioning  
**Duration**: 10-15 minutes  
**Requirements**: Poetry, Python 3.11+, Ollama

---

## BEFORE YOU START RECORDING

### Clean Slate Setup
```bash
# Delete all memora data
rm -rf memora_data/
rm -rf test_demo/

# Verify deletion
ls memora_data  # Should show "file not found" or similar
```

### Have These Ready in Separate Terminals

**Terminal 1** (Ollama Server):
```bash
ollama serve
# Should show: Listening on 127.0.0.1:11434
```

**Terminal 2** (Memora Proxy - for auto-capture):
```bash
cd "Z:\Open Source\FOSS HACK 26\Memora"
poetry run memora proxy start
# Should show: Starting Memora proxy on port 11435...
```

**Terminal 3** (Main Demo - where you'll run commands):
```bash
cd "Z:\Open Source\FOSS HACK 26\Memora"
# Stay in this terminal for the rest
```

---

## VIDEO SCRIPT - EXACT COMMANDS

### INTRO (30 seconds)
```
"Hi, I'm demonstrating Memora - a Git-style memory system for AI.
Unlike traditional memory systems, Memora automatically captures 
conversations AND lets you version them like Git with branches, 
commits, and rollback.

Let me show you how it works."
```

---

### PART 1: INITIALIZE & CAPTURE (3 minutes)

**[In Terminal 3]**

Initialize memora:
```bash
poetry run memora init
# Output: ✓ Memora repository initialized at: memora_data
```

Check initial stats:
```bash
poetry run memora stats
# Output should show:
# Memory Count: 0
# Commit Count: 0
# Branch Count: 1
# Session Count: 0
```

Start a chat session:
```bash
poetry run memora chat --model llama3.2:1b
```

**[When chat opens, type this]:**
```
My name is Alice and I work on AI systems. I'm currently building a memory system for large language models. We use Python and FastAPI for the backend.
```

**[Chat will wait for response - let it process]**

Exit the chat:
```
exit
```

**[Back in Terminal 3, check if memories were captured]**

```bash
poetry run memora stats
# Output should now show:
# Memory Count: 2 or more
# Commit Count: 1
# Session Count: 1
```

Verify the memories are searchable:
```bash
poetry run memora search "Alice"
# Output: Should find "User's name is Alice"
```

```bash
poetry run memora search "FastAPI"
# Output: Should find memory about FastAPI backend
```

**[Say to camera]:**
"Notice - I didn't manually save anything. The memory was captured 
automatically when the chat ended. Memora used a transparent proxy 
to intercept the conversation."

---

### PART 2: GIT-STYLE BRANCHING (3 minutes)

Show current branch:
```bash
poetry run memora branch list
# Output:
# Branches
# ┌─────────────────────────┐
# │ Name | Commit    | Current │
# ├─────────────────────────┤
# │ main | a1b2c3... │ *       │
# └─────────────────────────┘
```

Create a new branch for a project:
```bash
poetry run memora branch create "alice-project"
```

Switch to it:
```bash
poetry run memora branch switch "alice-project"
```

List branches again to show switch:
```bash
poetry run memora branch list
# Now alice-project has the *
```

**[Say to camera]:**
"Now I'm on a project-specific branch. Any new memories will go 
to this branch, keeping it separate from main. This is like Git 
branches but for AI memory."

---

### PART 3: COMMIT HISTORY (2 minutes)

Show commit log:
```bash
poetry run memora log
# Output shows commits with:
# commit a1b2c3d4...
# Author: system
# Date: 2026-04-09T...
#     Memory about Alice and FastAPI
```

Create another memory by chatting again:
```bash
poetry run memora chat --model llama3.2:1b
```

Type:
```
I prefer Python over Go for backend development.
```

Exit:
```
exit
```

Show updated log:
```bash
poetry run memora log --limit 5
# Should show 2 commits now
```

---

### PART 4: ROLLBACK - THE POWERFUL PART (2 minutes)

**[Say to camera]:**
"Now here's the powerful part - let's say we capture something 
we don't want anymore. We can rollback like Git!"

Add a wrong memory:
```bash
poetry run memora chat --model llama3.2:1b
```

Type something wrong on purpose:
```
We use Node.js for backend. Alice is working on Node.js systems.
```

Exit:
```
exit
```

Search for it:
```bash
poetry run memora search "Node.js"
# Output: Found 1 memory
```

Get the log to find the commit BEFORE this mistake:
```bash
poetry run memora log
# Note the commit hash from 2 commits ago
```

Rollback to the correct state:
```bash
poetry run memora rollback <COMMIT_HASH> --force --no-create-backup-branch
# Replace <COMMIT_HASH> with the hash from 2 commits ago
# Output: [OK] Rolled back to a1b2c3d4...
```

Verify the wrong memory is gone:
```bash
poetry run memora search "Node.js"
# Output: No results found
```

Verify correct memories still exist:
```bash
poetry run memora search "Python"
# Output: Still finds "I prefer Python over Go..."
```

**[Say to camera]:**
"The memory about Node.js is completely gone - rolled back. 
But we kept the correct memories. This is what sets Memora apart - 
Git-style version control for AI memory."

---

### OUTRO (30 seconds)

```bash
poetry run memora stats
# Show final stats
```

**[Say to camera]:**
"That's Memora. Key features:
1. Automatic capture - no manual save buttons
2. Git-style branches - separate projects or experiments  
3. Full commit history - see what was captured when
4. Rollback capability - undo mistakes instantly
5. Completely local - your data never leaves your machine

All of this works with ANY Ollama client. It's transparent, 
automatic, and powerful."
```

---

## TROUBLESHOOTING DURING VIDEO

### If chat hangs or doesn't capture:
```bash
# Press Ctrl+C to exit chat
# Check that Ollama server in Terminal 1 is running
# Restart: poetry run memora proxy start in Terminal 2
# Try again
```

### If search returns no results:
```bash
# The memories might still be processing
# Wait a moment and try search again
# Check stats to verify memories were added
```

### If rollback says "Already at target commit":
```bash
# You're trying to rollback to the current commit
# Get a different commit hash from the log
# Use one that's a few commits earlier
```

### If branch switch doesn't work:
```bash
# Make sure branch exists first
poetry run memora branch list  # Check it's there
poetry run memora branch create <name>  # If not, create it
poetry run memora branch switch <name>  # Then switch
```

---

## QUICK REFERENCE - ALL COMMANDS

```bash
# Initialization
poetry run memora init

# Chat (captures automatically)
poetry run memora chat --model llama3.2:1b

# Stats
poetry run memora stats

# Search
poetry run memora search "keyword"

# Branches
poetry run memora branch list
poetry run memora branch create <name>
poetry run memora branch switch <name>

# History
poetry run memora log
poetry run memora log --limit 5
poetry run memora log --branch <name>

# Rollback
poetry run memora rollback <commit_hash> --force --no-create-backup-branch

# Proxy (start before chatting)
poetry run memora proxy start
```

---

## SUCCESS CHECKLIST FOR VIDEO

After recording, verify you got:

- [ ] Initialization (memora init)
- [ ] Auto-capture shown (stats before/after chat)
- [ ] Search working (found Alice, FastAPI, Python)
- [ ] Branch creation and switch (memora branch list shows current branch with *)
- [ ] Commit history (memora log shows multiple commits with dates/authors)
- [ ] Rollback working (removed Node.js memory, kept Python memory)
- [ ] Final stats showing all the data

If all checkboxes are ✓, your demo is complete!

---

## NOTES FOR RECORDING

- **Do NOT pause the Ollama server** (Terminal 1)
- **Do NOT close the proxy** (Terminal 2) - it captures in background
- **Keep Terminal 3 visible** - this is where the action happens
- **Show the stats before/after** - proves memories are being stored
- **Emphasize the search feature** - shows memories are real and searchable
- **Highlight the rollback** - this is what makes Memora unique
- **Keep it under 15 minutes** - judges have limited time
