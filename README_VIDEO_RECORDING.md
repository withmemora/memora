# MEMORA VIDEO RECORDING - COMPLETE GUIDE

## STATUS: ✅ READY TO RECORD

All systems tested and ready. Follow these three documents in order:

---

## STEP 1: WATCH THIS FIRST
📄 **VIDEO_QUICK_REFERENCE.md** 
- Print-friendly single page
- All commands you need (copy/paste ready)
- Takes 1 minute to read

---

## STEP 2: SETUP (2 minutes before recording)

**Windows**:
```bash
cd "Z:\Open Source\FOSS HACK 26\Memora"
setup_for_video.bat
```

**Linux/Mac**:
```bash
cd "Z:\Open Source\FOSS HACK 26\Memora"
bash setup_for_video.sh
```

This will:
- ✓ Delete all old memora_data
- ✓ Verify project structure
- ✓ Check Poetry installation
- ✓ Confirm you're ready

---

## STEP 3: OPEN THREE TERMINALS

**Terminal 1** (Ollama):
```bash
ollama serve
```
Keep this running (background server)

**Terminal 2** (Memora Proxy):
```bash
cd "Z:\Open Source\FOSS HACK 26\Memora"
poetry run memora proxy start
```
Keep this running (auto-capture proxy)

**Terminal 3** (Demo Commands):
```bash
cd "Z:\Open Source\FOSS HACK 26\Memora"
# Ready for step 4
```

---

## STEP 4: FOLLOW THE SCRIPT

📄 **FOSS_HACK_DEMO.md**
- Detailed explanation of each section
- Expected outputs
- Troubleshooting tips
- What to say to judges

Follow this step-by-step. It's written to guide you through exactly 
what to do at each point in the video.

---

## STEP 5: RECORD VIDEO (13 minutes)

All commands are in VIDEO_QUICK_REFERENCE.md

### Quick timeline:
- 0:00-1:00 - Initialize (poetry run memora init)
- 1:00-4:00 - Auto-capture (chat and verify)
- 4:00-7:00 - Branching (create and switch branches)
- 7:00-10:00 - Commit history (poetry run memora log)
- 10:00-13:00 - Rollback magic (show undo capability)

---

## IMPORTANT REMINDERS

✓ **No old data** - All memora_data deleted before recording
✓ **Poetry run** - Always use `poetry run memora <command>`
✓ **Three terminals visible** - Audience needs to see activity
✓ **Clear narration** - Explain what you're doing as you do it
✓ **Show the search** - Proves memories are real and searchable
✓ **Emphasize rollback** - This is what makes Memora unique
✓ **Keep under 15 min** - Judges have limited time

---

## ALL COMMANDS USE THIS FORMAT

```bash
poetry run memora <command>
```

Examples:
```bash
poetry run memora init
poetry run memora stats
poetry run memora chat --model llama3.2:1b
poetry run memora branch list
poetry run memora log
poetry run memora search "keyword"
poetry run memora rollback <hash> --force --no-create-backup-branch
```

---

## TESTING BEFORE RECORD (OPTIONAL)

If you want to do a dry run first:

```bash
# Test everything works
poetry run memora init                    # Should work
poetry run memora stats                   # Should show 0 memories
poetry run memora chat --model llama3.2:1b
# Type: Hello world
# Exit with: exit
poetry run memora stats                   # Should show 1+ memories
poetry run memora search "world"          # Should find it
```

Then clean up and start the real recording:
```bash
setup_for_video.bat  # Clean slate again
```

---

## FILES YOU'LL USE

1. **VIDEO_QUICK_REFERENCE.md** ← Start here (print it!)
2. **FOSS_HACK_DEMO.md** ← Full script with explanations
3. **setup_for_video.bat/sh** ← Auto cleanup script
4. **pyproject.toml** ← Project config (don't touch)
5. **src/memora/** ← The actual code (don't touch)

---

## IF SOMETHING BREAKS

### "Command not found: poetry"
```bash
pip install poetry
poetry install
```

### "No memories captured"
Check Terminal 2 (proxy) is running and showing logs
Make sure you `exit` the chat properly to save it

### "Rollback says 'Already at target commit'"
You're using the wrong commit hash
Run `poetry run memora log` to see all commits
Use a hash from further back

### "Branch switch doesn't work"
Must create before switching:
```bash
poetry run memora branch create <name>
poetry run memora branch switch <name>
```

---

## SUCCESS CRITERIA

After recording, verify you captured:

✓ Initialization (clean slate)
✓ Auto-capture (chat + verify with search)
✓ Branch creation and switch
✓ Commit history (memora log)
✓ Rollback demo (add bad memory, rollback, verify)
✓ Final stats showing everything

If all 6 are complete, your demo is perfect!

---

## READY? 

1. Read: VIDEO_QUICK_REFERENCE.md (1 min)
2. Run: setup_for_video.bat (2 min)
3. Setup: Three terminals (2 min)
4. Record: Follow FOSS_HACK_DEMO.md (13 min)

**Total prep time: ~18 minutes**

Good luck! 🎥✨

Questions? Check FOSS_HACK_DEMO.md for detailed explanations of each section.
