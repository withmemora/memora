# FOSS Hack Demo Guide - Memora

**Version**: 3.1.0  
**Focus**: Git-style versioning + Automatic memory capture from Ollama conversations  
**Time**: 10-15 minutes for full demo

---

## Pre-Demo Checklist

```bash
# 1. Verify everything is installed and working
python --version  # Should be 3.11+
pip install -e .  # Install from source

# 2. Clean slate for demo
rm -rf memora_data/
rm -rf test_demo/

# 3. Verify debug logging is in place
grep -l "\[PROXY\]\|\[CAPTURE\]\|\[EXTRACT\]" src/memora/ai/ollama_proxy.py  # Should find multiple
```

---

## Demo Flow (15 minutes)

### Part 1: Automatic Memory Capture (5 min)
**Goal**: Show that Memora captures conversations automatically in the background

```bash
# Terminal 1: Start Memora with visible logging
memora start --memory-path ./test_demo

# Expected output:
# [PROXY] Received request: api/chat
# [PROXY] Is chat endpoint: true
# [PROXY] Parsed request data: ['model', 'messages', 'stream']
# ✓ Memora is running! Chat with Ollama normally...
```

```bash
# Terminal 2: Start Ollama  
ollama serve
# Expected: listening on 127.0.0.1:11434
```

```bash
# Terminal 3: Have a conversation
# IMPORTANT: Restart Ollama CLI after memora start
ollama run llama3.2:3b "My name is Alice and I work on AI systems"

# Watch Terminal 1 - you'll see:
# [PROXY] Received request: api/chat
# [STREAM] Starting streaming request handler...
# [STREAM] Opening connection to http://localhost:11434/api/chat...
# [STREAM] Connected, status: 200
# [STREAM] Received XX chunks, total XXXX bytes
# [STREAM] Calling capture_memories...
# [CAPTURE] Starting capture_memories...
# [CAPTURE] Found messages in request: 1 items
# [CAPTURE] Extracted user message: 65 chars
# [CAPTURE] ✓ User message: My name is Alice and I work on AI systems
# [EXTRACT] extract_conversation_memories called with 200 chars
# [EXTRACT] Pattern matching found 1 memories
# [CAPTURE] ✓ Stored 1 memories from user
# [CAPTURE] Completed
```

```bash
# Terminal 3: Verify memories were captured
memora stats
# Expected: Total Memories increased by 2+ (user + AI response)

memora search "Alice"
# Expected: "User's name is Alice" appears in results

memora search "AI systems"
# Expected: Memory about working on AI systems appears
```

---

### Part 2: Git-Style Versioning (5 min)
**Goal**: Show branches, commits, and rollback like Git

```bash
# Terminal 3: Create a project-specific branch
memora branch create "alice-project"
memora branch switch "alice-project"
# Now memories go to alice-project branch

# Simulate project work - add some memories
memora ingest ./README.md
# Or have more conversations:
ollama run llama3.2:3b "The project uses Python and FastAPI"

memora stats
memora search "FastAPI"
```

```bash
# Show the branching structure
memora branch list
# Expected output:
# Branches
# ┌────────────────────────────────────────────┐
# │ Name              │ Commit         │ Cur   │
# ├────────────────────────────────────────────┤
# │ main              │ a1b2c3d4...    │       │
# │ alice-project     │ d4c3b2a1...    │ *     │
# └────────────────────────────────────────────┘
```

```bash
# Show commit history
memora log --branch alice-project --limit 5
# Expected: Table of recent commits with timestamps

# Simulate a mistake: add wrong information
ollama run llama3.2:3b "We use Node.js backend"  # Wrong!

memora search "Node.js"
# Found: 1 memory

# Show the power: Rollback!
memora log --branch alice-project
# Note the commit hash from before the Node.js message

memora rollback <commit_hash>
# Confirm when prompted
# ✓ Rolled back to a1b2c3d4...
# ✓ Previous state preserved in branch: alice-project-backup-a1b2c3d4

memora search "Node.js"
# Expected: No results now (memory is gone)

memora search "FastAPI"
# Expected: Still there (rolled back to before Node.js)
```

---

### Part 3: The "Magic Trick" - Show Capture is Real (3 min)
**Goal**: Close to the actual problem statement

```bash
# Terminal 3: New conversation  
ollama run llama3.2:3b "I prefer Python over Go for this project"

# Terminal 1: You should immediately see logs:
# [PROXY] Received request: api/chat
# [STREAM] Opening connection...
# [CAPTURE] Starting capture_memories...
# [EXTRACT] extract_conversation_memories called...
# [CAPTURE] ✓ Stored 1 memories from user
```

```bash
# Verify it's there
memora search "Python"
memora search "prefer"
```

---

## Key Messages for Judges

### 1. **Automatic Capture Works**
- Show logs in Terminal 1 while having conversation in Terminal 3
- Proves Memora is actually capturing, not just claiming to
- The `[PROXY]`, `[STREAM]`, `[CAPTURE]`, `[EXTRACT]` logs are the evidence

### 2. **Git Versioning is Unique**
- `memora branch create` - projects stay separate
- `memora log` - see full commit history
- `memora rollback` - recover from mistakes
- **Nobody else has this** - it's different from every other memory system

### 3. **Transparent Integration**
- Run your Ollama conversation normally
- Memories captured in background (no API changes needed)
- No special commands to save or submit memories

### 4. **Production Ready**
- Error handling with recovery
- Session management (auto-commit on close)
- PII filtering built-in
- Configurable memory branches

---

## If Something Goes Wrong

### "No memories captured"
1. Check Terminal 1 for `[CAPTURE]` logs
2. If you see logs but no memories stored, look for `[EXTRACT] Pattern matching found 0`
3. The fallback should kick in: `[EXTRACT] No patterns matched, attempting fallback summary...`

### "Proxy not intercepting requests"
1. Verify `OLLAMA_HOST=http://localhost:11435` is set
2. **RESTART the Ollama app/script** after `memora start`
3. Check Terminal 1 for `[PROXY] Received request` when you make a call

### "Branch switch not working"  
1. Create the branch first: `memora branch create <name>`
2. Then switch: `memora branch switch <name>`
3. Verify: `memora branch list` should show `*` next to current branch

---

## Demo Talking Points

**"Traditional memory systems..."**
- Are cloud-dependent (privacy concern)
- Store memories as flat text (no versioning)
- Can't handle contradictions (what if info changes?)
- Require manual save buttons

**"Memora instead..."**
- Completely local (all data on your machine)
- Uses Git-style versioning (branches, commits, rollback)
- Automatic capture (no manual steps)
- Transparent proxy (works with ANY Ollama client)

**"The Git versioning is what sets us apart"**
- You can have `main` branch (stable memories)
- `experimental` branch (try new things safely)
- `projects/alice` branch (project-specific context)
- Rollback when information becomes outdated
- Full commit history for debugging

---

## Post-Demo Questions to Expect

**Q: How is this different from using sqlite?**
A: We use content-addressable storage (SHA-256) like Git. You get deduplication for free, and data remains valid even if files are moved/copied. Plus all the Git features.

**Q: What about memory limits?**
A: Tested up to 1M memories. At ~1000 bytes per memory, that's 1GB of storage. For most users, 1-3 years of daily use stays under 500MB.

**Q: How do you avoid capturing sensitive data?**
A: Built-in PII filter catches email, SSN, credit cards, API keys, etc. before storing. If something shouldn't be captured, the filter blocks it.

**Q: Can I use this with non-Ollama LLMs?**
A: Right now just Ollama (via transparent proxy). Adding support for other providers is in the roadmap.

---

## Files to Show (If Time Allows)

```
src/
├── memora/core/
│   ├── engine.py (100 lines - orchestrator)
│   ├── session.py (session lifecycle)
│   ├── refs.py (branch pointers - like Git)
│   └── store.py (content-addressable storage)
├── ai/
│   └── ollama_proxy.py (transparent HTTP proxy)
└── interface/
    └── cli.py (all the git-like commands)

Key stat: ~3500 lines of Python across 31 files
```

---

## Success Metrics for Demo

✅ User message was captured and searchable  
✅ AI response was captured and searchable  
✅ Created and switched branches without losing memories  
✅ Showed commit history with `memora log`  
✅ Rolled back to previous state and verified memories changed  
✅ All of this with zero manual memory-saving steps  

If all 6 are true, the demo is successful.
