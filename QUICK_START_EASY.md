# 🧠 MEMORA - Quick Start for Everyone
## No Coding Knowledge Needed!

---

## What is Memora?

Think of Memora as a **smart notebook for your AI conversations**. 

Just like you might jot down important things you learn in a notebook, Memora automatically captures and organizes everything you discuss with AI tools like Ollama.

**Key difference**: Unlike a regular notebook, Memora lets you:
- ✅ Search through everything instantly
- ✅ Find memories by time ("what did we talk about yesterday?")
- ✅ Organize into projects with branches
- ✅ Go back in time if you change your mind
- ✅ Keep everything private on your computer

---

## Installation (5 minutes)

### What You Need
- A computer (Windows, Mac, or Linux)
- Python installed
- Ollama installed

### Step 1: Install Python (if you don't have it)

**Windows:**
1. Go to https://www.python.org/downloads/
2. Click the big blue button "Download Python"
3. Run the installer
4. **IMPORTANT:** Check the box "Add Python to PATH"
5. Click Install

**Mac:**
1. Install Homebrew first: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
2. Then: `brew install python3`

**Linux:**
```bash
sudo apt-get install python3 python3-pip
```

### Step 2: Install Ollama

1. Go to https://ollama.ai
2. Download and install for your OS
3. Run `ollama serve` to make sure it works

### Step 3: Install Memora

Open your terminal/PowerShell and run:

```bash
pip install memora
```

**Done!** You're ready to go.

---

## Your First Memory (3 minutes)

### Step 1: Start Memora

Open a terminal and run:

```bash
memora start
```

You'll see something like:

```
🚀 Starting Memora...
✓ Repository initialized at: ./memora_data
✓ Ollama detected on port 11434
✓ OLLAMA_HOST set
🌐 Starting proxy on port 11435...
✓ Memora is running!
Press Ctrl+C to stop
```

**Leave this terminal running!**

### Step 2: Use Ollama Normally

Open **another terminal** and chat with Ollama:

```bash
ollama run llama2
```

Then start a conversation:

```
>>> Hello! What's the capital of France?
The capital of France is Paris...

>>> Tell me about Python programming
Python is a powerful programming language...
```

Just use it like normal - **Memora is capturing everything automatically!**

### Step 3: Stop When Done

When you're done chatting, press Ctrl+C in both terminals.

**Your memories are now saved!**

---

## Finding Your Memories (Next 5 minutes)

### See Everything You Talked About

Open a terminal and run:

```bash
memora search "Python"
```

You'll see all memories that mention Python:

```
Found 3 memories:

1. Python is a programming language...
2. Python best practices include...
3. Using Python for data analysis...
```

### Find by Time

Ask "when did we talk about X?"

```bash
memora search "France"
```

Or find everything from a specific time:

```bash
memora when "today"
memora when "yesterday"
memora when "last week"
```

### View Your Statistics

See an overview:

```bash
memora stats
```

Output:
```
📊 MEMORA STATISTICS

Total Memories: 15
├─ Conversations: 12
├─ Documents: 2
└─ Code: 1

Storage Used: 120 KB
```

---

## Organizing with Projects (Optional)

Want to organize your learning into different projects?

### Create a Project Branch

```bash
memora branch create "learning/python"
```

Now start Memora again and all new memories go to this project.

### Switch Between Projects

```bash
memora branch switch "learning/python"
memora search "loops"  # Only searches this project
```

### See All Projects

```bash
memora branch list
```

---

## Common Tasks

### Export Memories as a Document

Want to share or save your memories as a nice document?

```bash
memora export --format markdown --output my_memories.md
```

This creates a file `my_memories.md` that you can open in any text editor or Word.

### Delete a Memory

```bash
memora forget mem_12345
```

(You'll need the memory ID from search results)

### Backup Everything

```bash
memora backup --output backup_2024.zip
```

Creates a backup file you can save safely.

### Go Back in Time

Made a mistake? Go back:

```bash
memora rollback
```

### Chat About Your Memories

Have an interactive conversation:

```bash
memora chat
```

Then ask:
- "What did we talk about Python?"
- "Summarize my learning"
- "What's the next thing I should learn?"

---

## Troubleshooting

### Q: "Port 11435 already in use"
**A:** Use a different port:
```bash
memora start --port 11436
```

### Q: "Ollama not found"
**A:** Make sure Ollama is running in another terminal:
```bash
ollama serve
```

### Q: "Python command not found"
**A:** You need to install Python. See Installation step 1.

### Q: "Where are my memories stored?"
**A:** Find them with:
```bash
memora where
```

### Q: "I want to start fresh"
**A:** Delete everything and restart:
```bash
memora init --reset
memora start
```

---

## Quick Command Reference

### Start & Stop
```bash
memora start              # Start capturing (leave running)
memora start --port 9999  # Use different port
```

### Search & Find
```bash
memora search "topic"     # Search by content
memora when "today"       # Search by date
memora stats              # See overview
```

### Organize
```bash
memora branch list        # See projects
memora branch create "name"  # New project
memora branch switch "name"  # Change project
```

### Save & Backup
```bash
memora export             # Download memories
memora backup             # Create backup
memora restore backup.zip # Restore from backup
```

### Advanced
```bash
memora chat               # Interactive chat
memora log                # See history
memora graph              # See concepts
memora forget mem_id      # Delete memory
memora rollback           # Go back in time
```

---

## Example Workflows

### Workflow 1: Learning Something New

1. Start Memora: `memora start`
2. Chat with Ollama about the topic
3. Later, search what you learned: `memora search "topic"`
4. Export as notes: `memora export`

### Workflow 2: Working on a Project

1. Create a project branch: `memora branch create "project/website"`
2. Chat about architecture, design, code
3. Switch to branch: `memora branch switch "project/website"`
4. Search for decisions: `memora search "database design"`
5. View history: `memora log`

### Workflow 3: Daily Learning

1. Start Memora each day: `memora start`
2. Chat about different topics
3. At end of day, review: `memora when "today"`
4. Weekly: `memora stats` to see progress

---

## Pro Tips

1. **Use natural language**: You don't need to remember exact phrasing
   ```bash
   memora search "how do I use loops in Python?"  # This works!
   ```

2. **Search regularly**: Don't just remember in your head
   ```bash
   memora search "that thing I learned"
   ```

3. **Use projects for big topics**: Keeps things organized
   ```bash
   memora branch create "learning/react"
   memora branch create "learning/python"
   ```

4. **Backup weekly**: Better safe than sorry
   ```bash
   memora backup --output backup_week1.zip
   ```

5. **Export when done**: Have a readable document
   ```bash
   memora export --format markdown
   ```

---

## Privacy & Security

Good news: **Your memories are completely private!**

- ✅ Everything stays on your computer
- ✅ No cloud uploads
- ✅ No tracking or telemetry
- ✅ You have 100% control

Your `.memora` folder contains everything. You can:
- Back it up to an external drive
- Share with others (whole folder)
- Keep it synced with Dropbox/Google Drive if you want

---

## Next Steps

1. **Right now**: Run `memora start`
2. **In another terminal**: Start chatting with `ollama run llama2`
3. **After 5 minutes**: Open another terminal and try:
   ```bash
   memora search "something you talked about"
   memora stats
   ```
4. **Later**: Explore more commands:
   ```bash
   memora --help
   ```

---

## FAQ

**Q: Will Memora slow down Ollama?**
A: No, it runs in the background and is very fast.

**Q: Can I use multiple projects?**
A: Yes! Create as many branches as you want.

**Q: What if I have old memories?**
A: You can import them with `memora ingest file.txt`

**Q: Can I use this on my phone?**
A: Not yet, but desktop only for now.

**Q: Is it free?**
A: Yes! Memora is open source and completely free.

**Q: Can I share my memories?**
A: Yes, export and share the file: `memora export`

---

## Getting Help

If you get stuck:

1. **Check the help**: `memora --help`
2. **See this guide**: COMPLETE_DEMO_GUIDE.md
3. **GitHub issues**: Report bugs at https://github.com/memora-ai/memora/issues

---

## You're All Set! 🎉

You now have a personal AI memory system that:
- Automatically captures conversations
- Lets you search like Google
- Organizes with projects
- Keeps everything private
- Never forgets

**Start exploring!**

```bash
memora start
```

Happy learning! 🚀

---

*Memora v3.1.0 - Your personal AI memory system*
