# 🧠 MEMORA - Demo & Learning Resources Index

This document helps you navigate all the guides and resources for Memora.

---

## 🎯 Choose Your Path

### I'm Not Technical - I Just Want to Use It
**Start here:** [QUICK_START_EASY.md](QUICK_START_EASY.md)
- No coding knowledge needed
- Simple step-by-step instructions
- Works like mem0, Pieces, or Memoria
- 5-minute setup

**Then:** Just run one of these:
- **Windows (PowerShell):** `.\memora_start.ps1`
- **Windows (Batch):** `memora_start.bat`
- **Mac/Linux:** `./memora_start.sh`

---

### I Want to See All Features
**Start here:** [COMPLETE_DEMO_GUIDE.md](COMPLETE_DEMO_GUIDE.md)
- 15+ feature demonstrations
- Every command with examples
- Expected outputs
- Learning scenarios
- Troubleshooting

**Includes:**
- Basic search
- Time-based search
- Statistics
- Branches (Git-style)
- Commits & history
- Knowledge graph
- Chat with memory
- Rollback (undo)
- Export
- Backup/restore
- ...and more!

---

### I'm Presenting to Others
**Use:** [FOSS_HACK_DEMO.md](FOSS_HACK_DEMO.md)
- Competition demo script
- Timed demonstrations
- Talking points
- Impressive features to show

**Or:** [COMPLETE_DEMO_GUIDE.md](COMPLETE_DEMO_GUIDE.md) + live demo

---

### I Want Technical Details
**Read:** [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)
- System design
- Data models
- Storage format
- API details

---

## 📋 All Documentation

| File | Purpose | For Whom |
|------|---------|----------|
| [QUICK_START_EASY.md](QUICK_START_EASY.md) | Simple, non-technical intro | Everyone new to Memora |
| [COMPLETE_DEMO_GUIDE.md](COMPLETE_DEMO_GUIDE.md) | Full feature walkthrough | Power users, developers |
| [Readme.md](Readme.md) | Main project overview | Everyone |
| [FOSS_HACK_DEMO.md](FOSS_HACK_DEMO.md) | Competition demo script | Presenters |
| [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) | Technical deep-dive | Developers |
| [VIDEO_QUICK_REFERENCE.md](VIDEO_QUICK_REFERENCE.md) | Quick command reference | Video viewers |

---

## 🚀 Startup Scripts

All scripts do the same thing: initialize Memora and start capturing memories.

### Option 1: PowerShell (Windows, Modern)
```powershell
.\memora_start.ps1
```
**Features:** Colors, better error messages, modern approach

**If you get "execution policy" error:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Option 2: Batch (Windows, Legacy)
```batch
memora_start.bat
```
**Features:** Works on older Windows, no PowerShell needed

### Option 3: Bash (macOS/Linux)
```bash
./memora_start.sh
```
**Features:** Colors, cross-platform, built-in help

### Option 4: Direct Command (All Platforms)
```bash
memora start
```
**Features:** Simple, no script needed, but less helpful output

---

## 📖 Reading Guide

### First Time? Read in This Order:

1. **[QUICK_START_EASY.md](QUICK_START_EASY.md)** (5 min)
   - Understand what Memora is
   - Install requirements
   - First memory in 3 minutes

2. **[COMPLETE_DEMO_GUIDE.md](COMPLETE_DEMO_GUIDE.md)** (30 min)
   - See every feature in action
   - Learn all commands
   - Understand capabilities

3. **Try the startup script** (1 min)
   - Choose: PowerShell, Batch, or Bash
   - Run the script
   - Start chatting!

4. **Explore on your own** (ongoing)
   - Use commands as you discover them
   - Refer back to guides when needed

---

## 🎓 Feature Index

Find what you want to do:

| Want to... | Command | Read This |
|-----------|---------|-----------|
| Start Memora | `memora start` | QUICK_START_EASY.md |
| Search memories | `memora search "topic"` | COMPLETE_DEMO_GUIDE.md - Demo 1 |
| Find by time | `memora when "today"` | COMPLETE_DEMO_GUIDE.md - Demo 2 |
| See statistics | `memora stats` | COMPLETE_DEMO_GUIDE.md - Demo 3 |
| Create projects | `memora branch create` | COMPLETE_DEMO_GUIDE.md - Demo 6 |
| View history | `memora log` | COMPLETE_DEMO_GUIDE.md - Demo 7 |
| See concepts | `memora graph` | COMPLETE_DEMO_GUIDE.md - Demo 8 |
| Chat with memory | `memora chat` | COMPLETE_DEMO_GUIDE.md - Demo 9 |
| Go back in time | `memora rollback` | COMPLETE_DEMO_GUIDE.md - Demo 10 |
| Save as document | `memora export` | COMPLETE_DEMO_GUIDE.md - Demo 11 |
| Delete memory | `memora forget` | COMPLETE_DEMO_GUIDE.md - Demo 12 |
| Backup data | `memora backup` | COMPLETE_DEMO_GUIDE.md - Demo 13 |

---

## 🎬 Demo Progression

If you want to see features in a logical order:

1. **Start** - `memora start`
2. **Create memories** - Chat through Ollama
3. **Find them** - `memora search` (Demo 1)
4. **Search by time** - `memora when` (Demo 2)
5. **View overview** - `memora stats` (Demo 3)
6. **Check storage** - `memora where` (Demo 4)
7. **Add files** - `memora ingest` (Demo 5)
8. **Organize** - `memora branch` (Demo 6)
9. **See history** - `memora log` (Demo 7)
10. **Graph** - `memora graph` (Demo 8)
11. **Chat** - `memora chat` (Demo 9)
12. **Go back** - `memora rollback` (Demo 10)
13. **Export** - `memora export` (Demo 11)
14. **Clean up** - `memora forget` (Demo 12)
15. **Backup** - `memora backup` (Demo 13)
16. **Save** - `memora gc` (Demo 14)
17. **Manage** - `memora proxy` (Demo 15)

---

## ❓ FAQ

**Q: What should I read first?**
A: Read [QUICK_START_EASY.md](QUICK_START_EASY.md) - it's designed for first-time users.

**Q: Can I see all features at once?**
A: Yes! [COMPLETE_DEMO_GUIDE.md](COMPLETE_DEMO_GUIDE.md) has all 15 demos.

**Q: What's the difference between the scripts?**
A: They all do the same thing, just different operating systems.
- PowerShell: Modern Windows (prettier)
- Batch: Older Windows (more compatible)
- Bash: Mac/Linux

**Q: Is there technical documentation?**
A: Yes, [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) for developers.

**Q: Can I use Memora without reading all this?**
A: Yes! Just run `memora start` and figure it out. These docs are for reference.

---

## 🎯 Common Use Cases

### Use Case 1: Learning a New Language
1. Read: QUICK_START_EASY.md (5 min)
2. Run: `memora start`
3. Chat about the language
4. Search: `memora search "how do I..."`
5. See: COMPLETE_DEMO_GUIDE.md - Demo 6 (branches) to organize

### Use Case 2: Project Development
1. Start: `memora start`
2. Create branch: `memora branch create "project/name"`
3. Chat about architecture, design, code
4. Search: `memora search "decision we made"`
5. See: COMPLETE_DEMO_GUIDE.md - Demo 7 (history) to review

### Use Case 3: Research
1. Start: `memora start`
2. Ingest papers: `memora ingest papers/`
3. Chat about findings
4. Graph: `memora graph query "concept"`
5. Export: `memora export --format markdown`

---

## 📞 Getting Help

**Issue with installation?**
- Read QUICK_START_EASY.md - Troubleshooting section

**Can't find a feature?**
- Read COMPLETE_DEMO_GUIDE.md - Command Reference (bottom)

**Need technical help?**
- Read ARCHITECTURE.md for system design

**Something broken?**
- Report at: https://github.com/memora-ai/memora/issues

---

## ✨ What You Get

After reading these guides, you'll know:
- ✅ How to use Memora like mem0 or Pieces
- ✅ How to search your memories
- ✅ How to organize with branches
- ✅ How to manage history with git-like version control
- ✅ How to export and backup
- ✅ How to troubleshoot problems
- ✅ All 20+ commands
- ✅ Advanced features and power user tips

---

## 🚀 Next Steps

1. **Choose a guide** based on your needs (above)
2. **Run a startup script** (PowerShell, Batch, or Bash)
3. **Start chatting** with Ollama
4. **Search your memories**
5. **Explore features** as you discover them

That's it! You're on your way to having a personal AI memory system.

---

## 📊 Files Created for You

- ✅ `QUICK_START_EASY.md` - Non-technical intro
- ✅ `COMPLETE_DEMO_GUIDE.md` - Full feature guide with 15 demos
- ✅ `memora_start.ps1` - Windows PowerShell startup
- ✅ `memora_start.bat` - Windows Batch startup
- ✅ `memora_start.sh` - macOS/Linux startup
- ✅ This file - Navigation guide

**All created to make Memora as easy to use as mem0, Pieces, or Memoria!**

---

Happy learning! 🧠

*Memora v3.1.0 - Your personal AI memory system*
