# Memora Documentation Overview

Welcome to Memora's clean, focused documentation structure. This guide will help you understand what Memora is, how it works, and how to use it effectively.

---

## 📚 Documentation Structure

### **1. [Complete Architecture](./1-architecture/ARCHITECTURE.md)** (~14 KB)
**For:** Developers, system designers, and those curious about how Memora works internally

Deep dive into Memora's technical design:
- System architecture diagram and component overview
- How each component works (Engine, Store, Index, Graph, Session, etc.)
- Memory object structure and data flow
- Design decisions and why they were made
- Concurrency & safety mechanisms
- Performance characteristics with benchmarks
- Scalability limits and practical maximums
- Extension points for developers

**Start here if you want to understand:** How does Memora actually capture, store, and search memories? What's happening under the hood?

---

### **2. [Features & Implementation Details](./2-features/FEATURES.md)** (~26 KB)
**For:** Users wanting to understand what features exist and how they work

Comprehensive feature reference with real technical details:
- **Automatic Memory Capture** - How conversations are intercepted and captured
- **Code Extraction & Storage** - Support for 11+ languages with extraction examples
- **Knowledge Graph with NER** - Entity recognition and relationship building
- **Multi-Dimensional Search** - 4 types of search indices and how they work
- **Session Management** - Session lifecycle and auto-commit behavior
- **Security Filtering** - PII detection and filtering patterns
- **Git-Style Versioning** - Branches, commits, and rollback capabilities

Each feature includes:
- **What it does** (user-facing description)
- **How it works** (technical implementation with code locations)
- **Storage** (where data is stored, size limits, examples)
- **Performance** (speed, scale characteristics)

**Start here if you want to know:** What can Memora do? What are the limits? How does feature X actually work?

---

### **3. [Demo & User Guide](./3-demo-guide/DEMO_AND_USAGE_GUIDE.md)** (~26 KB)
**For:** New users and those wanting practical, hands-on examples

Complete walkthrough with real working commands:
- Installation & setup (with prerequisites)
- Quick start guide (5 minutes from zero to working)
- Understanding Ollama and the transparent proxy
- Essential commands with examples and output
- Real-world workflows for different use cases
- Troubleshooting guide for common issues
- Directory structure explanation
- Performance optimization tips

Each command includes:
- How to run it
- What options are available
- Example output
- Real use cases

**Start here if you want to:** Get Memora running, learn commands, and see practical examples.

---

## 🚀 Quick Navigation

**I want to...**

| Goal | Start Here |
|------|-----------|
| Get Memora running quickly | [Demo & User Guide - Quick Start](./3-demo-guide/DEMO_AND_USAGE_GUIDE.md#quick-start-5-minutes) |
| Understand how Memora works internally | [Complete Architecture](./1-architecture/ARCHITECTURE.md) |
| Learn what features exist | [Features & Implementation](./2-features/FEATURES.md) |
| Find commands to use | [Demo & User Guide - Essential Commands](./3-demo-guide/DEMO_AND_USAGE_GUIDE.md#essential-commands) |
| Understand a specific feature | [Features & Implementation](./2-features/FEATURES.md) |
| Troubleshoot an issue | [Demo & User Guide - Troubleshooting](./3-demo-guide/DEMO_AND_USAGE_GUIDE.md#troubleshooting) |
| See real-world examples | [Demo & User Guide - Real-World Workflows](./3-demo-guide/DEMO_AND_USAGE_GUIDE.md#real-world-workflows) |
| Understand storage & performance | [Architecture - Performance & Scalability](./1-architecture/ARCHITECTURE.md#performance--scalability) or [Features - Storage](./2-features/FEATURES.md) |
| Understand the memory object format | [Architecture - Memory Object Structure](./1-architecture/ARCHITECTURE.md#memory-object-structure) |

---

## 📖 Reading Recommendations

### For First-Time Users
1. **Start:** [Demo & User Guide - Quick Start](./3-demo-guide/DEMO_AND_USAGE_GUIDE.md#quick-start-5-minutes) (5 minutes)
2. **Install & run:** [Demo & User Guide - Installation](./3-demo-guide/DEMO_AND_USAGE_GUIDE.md#installation--setup)
3. **Learn commands:** [Demo & User Guide - Essential Commands](./3-demo-guide/DEMO_AND_USAGE_GUIDE.md#essential-commands)
4. **Try workflows:** [Demo & User Guide - Real-World Workflows](./3-demo-guide/DEMO_AND_USAGE_GUIDE.md#real-world-workflows)

### For Developers
1. **Understand design:** [Complete Architecture](./1-architecture/ARCHITECTURE.md)
2. **Know the limits:** [Features - Performance & Scalability](./2-features/FEATURES.md) section in each feature
3. **See extension points:** [Architecture - Design Rationale & Extension Points](./1-architecture/ARCHITECTURE.md#design-rationale--extension-points)
4. **Understand data format:** [Architecture - Memory Object Structure](./1-architecture/ARCHITECTURE.md#memory-object-structure)

### For System Administrators / DevOps
1. **Installation:** [Demo & User Guide - Installation](./3-demo-guide/DEMO_AND_USAGE_GUIDE.md#installation--setup)
2. **Storage & performance:** [Architecture - Performance & Scalability](./1-architecture/ARCHITECTURE.md#performance--scalability)
3. **Troubleshooting:** [Demo & User Guide - Troubleshooting](./3-demo-guide/DEMO_AND_USAGE_GUIDE.md#troubleshooting)
4. **Backup & recovery:** [Demo & User Guide - Export & Backup](./3-demo-guide/DEMO_AND_USAGE_GUIDE.md#export--backup)

---

## 📊 Documentation Statistics

| Document | Size | Sections | Purpose |
|----------|------|----------|---------|
| [ARCHITECTURE.md](./1-architecture/ARCHITECTURE.md) | ~14 KB | 10+ sections | System design & technical deep-dive |
| [FEATURES.md](./2-features/FEATURES.md) | ~26 KB | 7 features + reference | What features exist & how they work |
| [DEMO_AND_USAGE_GUIDE.md](./3-demo-guide/DEMO_AND_USAGE_GUIDE.md) | ~26 KB | 8 major sections | Hands-on practical guide with examples |

**Total:** ~66 KB of focused, organized documentation

---

## 🔍 Key Concepts

### Memory Object
The fundamental unit in Memora. Contains:
- **Content**: The actual data (conversation text, code, etc.)
- **Type**: conversation, code, or document
- **Created at**: Timestamp
- **Confidence**: Relevance score (0-1)
- **Hash**: SHA-256 content hash (for deduplication)

See: [Architecture - Memory Object Structure](./1-architecture/ARCHITECTURE.md#memory-object-structure)

### Content-Addressable Storage
Memories are stored by their SHA-256 hash, not by location. This means:
- Identical content is never duplicated
- Corruption is easily detected
- Data can be reorganized without breaking references

See: [Architecture - Storage Layer](./1-architecture/ARCHITECTURE.md#storage-layer-store)

### Transparent Proxy
Memora sits between your client and Ollama:
```
Client → Memora Proxy (11435) → Ollama (11434)
```
Clients don't know memories are being captured.

See: [Architecture - Network Layer](./1-architecture/ARCHITECTURE.md#network-layer-ollama_proxy) or [Demo & User Guide - Understanding Ollama & The Proxy](./3-demo-guide/DEMO_AND_USAGE_GUIDE.md#understanding-ollama--the-proxy)

### Branches
Git-style memory organization. Create branches for projects, contexts, or experiments:
```bash
memora branch create "work-project"
memora branch switch "work-project"
```

See: [Features - Git-Style Versioning](./2-features/FEATURES.md#feature-7-git-style-versioning)

### Sessions
Auto-grouped conversations. When you chat for 15 minutes, it's one session. When you stop, it closes.

See: [Features - Session Management](./2-features/FEATURES.md#feature-5-session-management)

---

## ❓ FAQ

**Q: Where's the main README?**
A: That's in the root of the repo (`/README.md`). This documentation folder (`/docs-clean/`) is specifically focused and organized documentation.

**Q: Can I edit these files?**
A: These are reference documentation. The source code in `/src/` is where actual features are implemented. If you find errors or want to suggest improvements, please report them on GitHub.

**Q: Where's information about the REST API?**
A: API endpoints are documented in the Architecture guide under the Server component. The API is simple and mirrors CLI commands.

**Q: How do I contribute documentation?**
A: These files are generated from the codebase analysis. If you see errors or omissions, please report them on GitHub: https://github.com/memora-ai/memora/issues

---

## 📞 Support & Feedback

- **Issues & Bug Reports**: https://github.com/memora-ai/memora/issues
- **Discussions**: https://github.com/memora-ai/memora/discussions
- **Documentation Feedback**: Please report doc issues on GitHub

---

**Last Updated:** December 2024  
**Memora Version:** 3.1.0  
**Python Version Required:** 3.11+
