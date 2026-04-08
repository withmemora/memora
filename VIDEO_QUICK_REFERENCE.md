# MEMORA VIDEO RECORDING - QUICK REFERENCE CARD

Print this out and keep it next to you while recording!

---

## THREE TERMINALS SETUP

```
┌─────────────────────────────────────────────────────────────┐
│ Terminal 1: ollama serve                                    │
│ (Keep running - background server)                          │
│                                                             │
│ Listens on: 127.0.0.1:11434                                │
│ Keep running throughout entire demo                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Terminal 2: poetry run memora proxy start                   │
│ (Auto-capture proxy - background)                           │
│                                                             │
│ Listens on: 127.0.0.1:11435                                │
│ Intercepts requests and captures memories                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Terminal 3: [YOUR DEMO COMMANDS]                           │
│ (Visible to camera - do all commands here)                 │
│                                                             │
│ This is what viewers will see                              │
└─────────────────────────────────────────────────────────────┘
```

---

## BEFORE YOU PRESS RECORD

- [ ] Run: `setup_for_video.bat` (Windows) or `setup_for_video.sh` (Linux/Mac)
- [ ] Terminal 1 running: `ollama serve`
- [ ] Terminal 2 running: `poetry run memora proxy start`
- [ ] Terminal 3 ready: `cd "Z:\Open Source\FOSS HACK 26\Memora"`
- [ ] All three terminals visible on screen

---

## VIDEO SCRIPT - COPY/PASTE COMMANDS

### PART 1: Initialize (1 min)
```
poetry run memora init
poetry run memora stats
```
**Say**: "Starting fresh - zero memories."

---

### PART 2: Auto-Capture (3 min)
```
poetry run memora chat --model llama3.2:1b
```

**Type in chat**:
```
My name is Alice and I work on AI systems. I'm currently building 
a memory system for large language models. We use Python and FastAPI 
for the backend.
```

**Exit chat**: `exit`

```
poetry run memora stats
poetry run memora search "Alice"
poetry run memora search "FastAPI"
```

**Say**: "All captured automatically - zero manual steps!"

---

### PART 3: Branching (3 min)
```
poetry run memora branch list
poetry run memora branch create "alice-project"
poetry run memora branch switch "alice-project"
poetry run memora branch list
```

**Say**: "Now on a separate branch - like Git for memory!"

---

### PART 4: More Memories (2 min)
```
poetry run memora chat --model llama3.2:1b
```

**Type**:
```
I prefer Python over Go for backend development.
```

**Exit**: `exit`

```
poetry run memora log
```

**Say**: "See the commit history - timestamps, authors, everything!"

---

### PART 5: Rollback Demo (3 min)
```
poetry run memora chat --model llama3.2:1b
```

**Type wrong thing**:
```
We use Node.js for backend. Alice works on Node.js systems.
```

**Exit**: `exit`

```
poetry run memora search "Node.js"
```

**Say**: "Found the wrong memory. Now watch me rollback..."

```
poetry run memora log
```

**Note the commit hash from 2-3 commits ago, then**:
```
poetry run memora rollback <HASH> --force --no-create-backup-branch
```

**Verify**:
```
poetry run memora search "Node.js"
poetry run memora search "Python"
```

**Say**: "Node.js is gone, Python still there. Git-style control!"

---

### PART 6: Final Stats (1 min)
```
poetry run memora stats
```

**Say**: "That's Memora - automatic capture + Git versioning."

---

## TOTAL TIME: ~13 minutes

---

## EMERGENCY COMMANDS (If something breaks)

```bash
# Reset everything
setup_for_video.bat

# Check if Ollama is running
poetry run memora stats

# Check if proxy is capturing
# (Look for logs in Terminal 2)

# If chat hangs
# Press: Ctrl+C

# Start over with a clean branch
poetry run memora branch create "attempt-2"
poetry run memora branch switch "attempt-2"
```

---

## KEY TALKING POINTS

1. **"Automatic"** - No save buttons, proxy captures in background
2. **"Versioned"** - Like Git, with branches, commits, rollback
3. **"Local"** - All data stays on your machine
4. **"Transparent"** - Works with ANY Ollama client
5. **"Unique"** - No other memory system has Git versioning

---

## GOOD LUCK! 🎥

You've got this. All commands use `poetry run memora` and the system 
is tested and working. Just follow the script step by step.

Remember:
- Keep all three terminals visible
- Talk while running commands (narrate what you're doing)
- Show the stats before/after (proves memories are being stored)
- Emphasize the rollback (that's the magic trick)

Questions? Check FOSS_HACK_DEMO.md for detailed explanations.
