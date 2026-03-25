# 🌐 Memora Project Website & Documentation Structure

## 🏗️ **COMPLETE WEBSITE ARCHITECTURE**

### **Website File Structure**
```
memora-website/
├── index.html                 # Landing page with hero section
├── demo.html                  # Live interactive demo
├── download.html              # Installation & download page
├── docs/                      # Documentation site
│   ├── index.html            # Documentation home
│   ├── getting-started/      # Quick start guides
│   │   ├── installation.html
│   │   ├── first-chat.html
│   │   └── basic-concepts.html
│   ├── guides/               # Detailed tutorials
│   │   ├── conversation-ai.html
│   │   ├── code-intelligence.html
│   │   ├── document-ingestion.html
│   │   └── memory-management.html
│   ├── api-reference/        # Complete API docs
│   │   ├── python-api.html
│   │   ├── rest-api.html
│   │   ├── cli-reference.html
│   │   └── websocket-api.html
│   ├── architecture/         # Technical documentation
│   │   ├── system-design.html
│   │   ├── memory-engine.html
│   │   ├── conflict-system.html
│   │   └── performance.html
│   └── community/            # Open source resources
│       ├── contributing.html
│       ├── roadmap.html
│       ├── changelog.html
│       └── support.html
├── assets/                   # Static resources
│   ├── css/
│   │   ├── main.css         # Main stylesheet
│   │   ├── docs.css         # Documentation styling
│   │   └── demo.css         # Demo page styling
│   ├── js/
│   │   ├── main.js          # Site functionality
│   │   ├── demo-terminal.js # Interactive demo
│   │   └── docs-search.js   # Documentation search
│   ├── images/              # Logos, screenshots, diagrams
│   └── videos/              # Demo videos, tutorials
└── legal/                   # Legal documents
    ├── license.html         # MIT license display
    ├── privacy.html         # Privacy policy
    └── terms.html           # Terms of service
```

### **Landing Page Design**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Memora - Git-Style Memory for AI</title>
    <meta name="description" content="The first memory system that treats conflicts as evolution, not errors. Git-style versioned memory for Large Language Models.">
    <link rel="stylesheet" href="assets/css/main.css">
    <link rel="icon" href="assets/images/favicon.ico">
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar">
        <div class="nav-container">
            <div class="nav-logo">
                <img src="assets/images/memora-logo.svg" alt="Memora">
                <span>Memora</span>
            </div>
            <ul class="nav-menu">
                <li><a href="#features">Features</a></li>
                <li><a href="#demo">Demo</a></li>
                <li><a href="docs/">Docs</a></li>
                <li><a href="https://github.com/withmemora/memora">GitHub</a></li>
                <li><a href="download.html" class="btn-primary">Download</a></li>
            </ul>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero">
        <div class="hero-content">
            <h1>Git-Style Memory for AI</h1>
            <p class="hero-subtitle">The first memory system that treats conflicts as evolution, not errors</p>
            <div class="hero-features">
                <span class="feature-badge">🧠 Automatic Memory</span>
                <span class="feature-badge">🌿 Git-Style Versioning</span>
                <span class="feature-badge">🔍 Human-Readable</span>
                <span class="feature-badge">⚡ Production Ready</span>
            </div>
            <div class="hero-actions">
                <a href="#demo" class="btn btn-primary">Try Live Demo</a>
                <a href="docs/getting-started/" class="btn btn-secondary">Get Started</a>
                <a href="https://github.com/withmemora/memora" class="btn btn-outline">
                    <i class="github-icon"></i> View on GitHub
                </a>
            </div>
        </div>
        <div class="hero-visual">
            <div class="terminal-demo">
                <!-- Animated terminal showing Memora in action -->
            </div>
        </div>
    </section>

    <!-- Problem & Solution -->
    <section class="problem-solution">
        <div class="container">
            <div class="problem">
                <h2>The AI Memory Problem</h2>
                <ul>
                    <li>❌ AI systems forget context between conversations</li>
                    <li>❌ Memory conflicts are treated as errors to resolve</li>
                    <li>❌ Users can't see what their AI remembers</li>
                    <li>❌ No versioning when preferences change</li>
                </ul>
            </div>
            <div class="solution">
                <h2>Memora's Innovation</h2>
                <ul>
                    <li>✅ Persistent memory across all conversations</li>
                    <li>✅ Conflicts preserved as memory evolution</li>
                    <li>✅ Human-readable memory interface</li>
                    <li>✅ Git-style branching and versioning</li>
                </ul>
            </div>
        </div>
    </section>

    <!-- Key Features -->
    <section id="features" class="features">
        <div class="container">
            <h2>Revolutionary AI Memory Features</h2>
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">🧠</div>
                    <h3>Automatic Memory Extraction</h3>
                    <p>Extracts facts from conversations in real-time using advanced NLP. No manual memory management needed.</p>
                    <ul>
                        <li>Real-time fact extraction</li>
                        <li>Context-aware processing</li>
                        <li>Multi-language support</li>
                    </ul>
                </div>
                
                <div class="feature-card">
                    <h3>🌿 Git-Style Versioning</h3>
                    <p>Branch, commit, and merge memory timelines like code. Perfect for different conversation contexts.</p>
                    <ul>
                        <li>Memory branches for different topics</li>
                        <li>Commit snapshots of memory state</li>
                        <li>Merge different conversation threads</li>
                    </ul>
                </div>
                
                <div class="feature-card">
                    <h3>🔍 Human-Readable Interface</h3>
                    <p>See and search your memories in plain English. No more black box AI memory.</p>
                    <ul>
                        <li>Natural language memory display</li>
                        <li>Advanced search and filtering</li>
                        <li>Memory timeline visualization</li>
                    </ul>
                </div>
                
                <div class="feature-card">
                    <h3>⚡ Production Performance</h3>
                    <p>Sub-millisecond memory retrieval with intelligent caching and optimization.</p>
                    <ul>
                        <li>&lt; 1ms memory retrieval</li>
                        <li>52% storage compression</li>
                        <li>Scales to 50K+ facts per branch</li>
                    </ul>
                </div>
                
                <div class="feature-card">
                    <h3>🤖 AI Integration</h3>
                    <p>Works with Ollama, OpenAI, Anthropic, and any LLM. Drop-in memory layer for existing AI systems.</p>
                    <ul>
                        <li>Ollama + Llama3.2 integration</li>
                        <li>Context injection for LLM prompts</li>
                        <li>Framework adapters (LangChain, etc.)</li>
                    </ul>
                </div>
                
                <div class="feature-card">
                    <h3>📄 Code & Document Intelligence</h3>
                    <p>Automatically extract context from codebases and documents. Perfect for development teams.</p>
                    <ul>
                        <li>Repository analysis</li>
                        <li>PDF/DOCX processing</li>
                        <li>Meeting notes extraction</li>
                    </ul>
                </div>
            </div>
        </div>
    </section>

    <!-- Live Demo Section -->
    <section id="demo" class="demo-section">
        <div class="container">
            <h2>Try Memora Live</h2>
            <p>Experience Memora's memory system in action. Type commands and see how it remembers and evolves.</p>
            
            <div class="demo-interface">
                <div class="demo-tabs">
                    <button class="tab-button active" data-tab="chat">AI Chat</button>
                    <button class="tab-button" data-tab="memory">Memory View</button>
                    <button class="tab-button" data-tab="cli">CLI Demo</button>
                </div>
                
                <div class="demo-content">
                    <div class="tab-panel active" id="chat-panel">
                        <div class="chat-interface">
                            <div class="chat-messages" id="chat-messages">
                                <div class="message ai">
                                    <span class="message-author">Memora AI</span>
                                    <div class="message-content">
                                        Hello! I'm an AI with persistent memory. Tell me about yourself and I'll remember for future conversations.
                                    </div>
                                </div>
                            </div>
                            <div class="chat-input">
                                <input type="text" id="chat-input" placeholder="Type your message... (e.g., 'My name is Alex and I love Python programming')">
                                <button id="send-button">Send</button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="tab-panel" id="memory-panel">
                        <div class="memory-interface">
                            <div class="memory-search">
                                <input type="text" placeholder="Search memories...">
                                <div class="memory-filters">
                                    <button class="filter-tag">All</button>
                                    <button class="filter-tag">Personal</button>
                                    <button class="filter-tag">Work</button>
                                    <button class="filter-tag">Technical</button>
                                </div>
                            </div>
                            <div class="memory-list" id="memory-list">
                                <!-- Memories will be populated here -->
                            </div>
                        </div>
                    </div>
                    
                    <div class="tab-panel" id="cli-panel">
                        <div class="terminal" id="demo-terminal">
                            <div class="terminal-header">
                                <span class="terminal-title">Memora CLI Demo</span>
                            </div>
                            <div class="terminal-body" id="terminal-output">
                                <div class="terminal-line">
                                    <span class="prompt">$ </span>
                                    <span class="command">memora add "I work at TechCorp as a software engineer"</span>
                                </div>
                                <div class="terminal-line output">
                                    ✅ Added 2 memories: work location, job title
                                </div>
                                <div class="terminal-line">
                                    <span class="prompt">$ </span>
                                    <span class="cursor">|</span>
                                </div>
                            </div>
                            <input type="text" class="terminal-input" id="cli-input" placeholder="Try: memora search 'TechCorp'">
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Use Cases -->
    <section class="use-cases">
        <div class="container">
            <h2>Real-World Applications</h2>
            <div class="use-cases-grid">
                <div class="use-case">
                    <h3>👤 Personal AI Assistant</h3>
                    <p>Build AI assistants that remember user preferences, history, and context across sessions.</p>
                    <div class="code-example">
                        <code>
chat = MemoraChat(model="llama3.2")
chat.message("What's my favorite cuisine?")
# Uses stored preferences automatically
                        </code>
                    </div>
                </div>
                
                <div class="use-case">
                    <h3>👥 Development Teams</h3>
                    <p>Share development context, decisions, and knowledge across team members.</p>
                    <div class="code-example">
                        <code>
memora ingest repo ./project
memora search "authentication"
# Finds all auth-related decisions
                        </code>
                    </div>
                </div>
                
                <div class="use-case">
                    <h3>📞 Customer Support</h3>
                    <p>Maintain context across support interactions for personalized customer service.</p>
                    <div class="code-example">
                        <code>
support = MemoraChat(branch=f"customer_{id}")
# Remembers previous issues and solutions
                        </code>
                    </div>
                </div>
                
                <div class="use-case">
                    <h3>🔬 Research & Learning</h3>
                    <p>Accumulate knowledge from documents, papers, and conversations over time.</p>
                    <div class="code-example">
                        <code>
memora ingest doc ./research_papers/
memora search "machine learning ethics"
# Searches across all ingested documents
                        </code>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Quick Start -->
    <section class="quick-start">
        <div class="container">
            <h2>Get Started in 5 Minutes</h2>
            <div class="installation-steps">
                <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-content">
                        <h3>Install Memora</h3>
                        <div class="code-block">
                            <code>pip install memora[ai]</code>
                            <button class="copy-button">Copy</button>
                        </div>
                    </div>
                </div>
                
                <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-content">
                        <h3>Start Chatting</h3>
                        <div class="code-block">
                            <code>memora chat</code>
                            <button class="copy-button">Copy</button>
                        </div>
                    </div>
                </div>
                
                <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-content">
                        <h3>Explore Memories</h3>
                        <div class="code-block">
                            <code>memora dashboard</code>
                            <button class="copy-button">Copy</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="quick-start-actions">
                <a href="docs/getting-started/" class="btn btn-primary">Full Installation Guide</a>
                <a href="docs/api-reference/" class="btn btn-secondary">API Documentation</a>
            </div>
        </div>
    </section>

    <!-- Open Source -->
    <section class="open-source">
        <div class="container">
            <h2>Open Source & Community</h2>
            <div class="open-source-grid">
                <div class="os-card">
                    <h3>📜 MIT Licensed</h3>
                    <p>Free to use, modify, and distribute for any purpose.</p>
                    <a href="legal/license.html">View License</a>
                </div>
                
                <div class="os-card">
                    <h3>🤝 Contributing</h3>
                    <p>Join our community of developers building the future of AI memory.</p>
                    <a href="docs/community/contributing.html">Contribution Guide</a>
                </div>
                
                <div class="os-card">
                    <h3>🚀 Roadmap</h3>
                    <p>See what's coming next and influence the development direction.</p>
                    <a href="docs/community/roadmap.html">View Roadmap</a>
                </div>
                
                <div class="os-card">
                    <h3>💬 Community</h3>
                    <p>Get help, share ideas, and connect with other users.</p>
                    <a href="https://discord.gg/memora">Join Discord</a>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-section">
                    <img src="assets/images/memora-logo.svg" alt="Memora" class="footer-logo">
                    <p>Git-style versioned memory for Large Language Models</p>
                    <div class="social-links">
                        <a href="https://github.com/withmemora/memora">GitHub</a>
                        <a href="https://discord.gg/memora">Discord</a>
                        <a href="https://twitter.com/memoraai">Twitter</a>
                    </div>
                </div>
                
                <div class="footer-section">
                    <h4>Documentation</h4>
                    <ul>
                        <li><a href="docs/getting-started/">Getting Started</a></li>
                        <li><a href="docs/api-reference/">API Reference</a></li>
                        <li><a href="docs/guides/">Guides</a></li>
                        <li><a href="docs/architecture/">Architecture</a></li>
                    </ul>
                </div>
                
                <div class="footer-section">
                    <h4>Community</h4>
                    <ul>
                        <li><a href="docs/community/contributing.html">Contributing</a></li>
                        <li><a href="docs/community/roadmap.html">Roadmap</a></li>
                        <li><a href="docs/community/changelog.html">Changelog</a></li>
                        <li><a href="docs/community/support.html">Support</a></li>
                    </ul>
                </div>
                
                <div class="footer-section">
                    <h4>Legal</h4>
                    <ul>
                        <li><a href="legal/license.html">License</a></li>
                        <li><a href="legal/privacy.html">Privacy</a></li>
                        <li><a href="legal/terms.html">Terms</a></li>
                    </ul>
                </div>
            </div>
            
            <div class="footer-bottom">
                <p>&copy; 2024 Memora Project Contributors. Released under MIT License.</p>
                <p>Built for <strong>FOSS HACK 2026</strong> - Revolutionizing AI Memory</p>
            </div>
        </div>
    </footer>

    <script src="assets/js/main.js"></script>
</body>
</html>
```

---

## 📜 **OPEN SOURCE LICENSING STRUCTURE**

### **MIT License Implementation**
```text
# LICENSE file content

MIT License

Copyright (c) 2024 Memora Project Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### **Contributing Guidelines**
```markdown
# Contributing to Memora

Welcome to the Memora community! We're excited to have you contribute to the future of AI memory systems.

## 🚀 Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork**: `git clone https://github.com/yourusername/memora.git`
3. **Create a branch**: `git checkout -b feature/amazing-feature`
4. **Make your changes** and add tests
5. **Run the test suite**: `pytest tests/ --cov=src/memora`
6. **Submit a pull request**

## 📋 Contribution Types

### 🐛 Bug Fixes
- Report bugs using GitHub issues
- Include reproduction steps and system info
- Write tests that expose the bug
- Fix the bug with minimal changes

### ✨ New Features
- Discuss new features in GitHub discussions first
- Follow the existing architecture patterns
- Add comprehensive tests and documentation
- Update the changelog and API docs

### 📚 Documentation
- Fix typos, improve clarity
- Add examples and use cases
- Update API documentation
- Create tutorials and guides

### 🔧 Performance & Optimization
- Include benchmarks showing improvement
- Ensure no regression in existing performance
- Document the optimization approach

## 🏗️ Development Setup

### Prerequisites
- Python 3.11+
- Git
- Ollama (for AI features)

### Installation
```bash
# Clone repository
git clone https://github.com/withmemora/memora.git
cd memora

# Install in development mode
pip install -e .[dev,ai]

# Install pre-commit hooks
pre-commit install

# Download required models
python -m spacy download en_core_web_sm
ollama pull llama3.2
```

### Running Tests
```bash
# Run full test suite
pytest tests/ --cov=src/memora

# Run specific test categories
pytest tests/core/          # Core engine tests
pytest tests/interface/     # Interface tests
pytest tests/integration/   # Integration tests

# Run performance benchmarks
pytest tests/performance/ --benchmark-only
```

## 📝 Code Standards

### Python Code Style
- Follow PEP 8 formatting
- Use type hints for all functions
- Docstrings for all public APIs
- Maximum line length: 100 characters

### Testing Requirements
- Write tests for all new features
- Maintain 85%+ code coverage
- Include both unit and integration tests
- Test edge cases and error conditions

### Documentation Standards
- Update API docs for any interface changes
- Include docstring examples for complex functions
- Update changelog for user-visible changes
- Add tutorials for new features

## 🔄 Development Workflow

### Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `perf/description` - Performance improvements

### Commit Messages
Follow conventional commits format:
```
type(scope): description

feat(core): add memory compression algorithm
fix(api): resolve race condition in concurrent access
docs(readme): update installation instructions
perf(index): optimize memory retrieval performance
```

### Pull Request Process
1. **Update your branch** with latest main
2. **Run full test suite** locally
3. **Write descriptive PR title** and description
4. **Link related issues** using keywords
5. **Request review** from maintainers

## 🏛️ Architecture Guidelines

### Core Principles
- **Clean Architecture**: Separation of concerns
- **Git-Style Operations**: Consistent with Git semantics
- **Performance First**: Sub-millisecond memory operations
- **Type Safety**: Full mypy compliance
- **Testability**: Easy to test and mock

### Adding New Features
- Follow the 3-layer architecture (Core/Interface/Shared)
- Add appropriate abstractions in shared/interfaces.py
- Implement core logic in core/ modules
- Expose through interface/ layer
- Write comprehensive tests

### Memory Operations
- All memory operations must be atomic
- Preserve conflict information, don't resolve
- Maintain Git-style object integrity
- Optimize for read performance

## 🌟 Recognition

Contributors are recognized in:
- **CONTRIBUTORS.md** - All contributors listed
- **Release notes** - Significant contributions highlighted
- **Documentation** - Authors credited in relevant sections

## 🆘 Getting Help

- **Documentation**: Check docs/ for guides and API reference
- **GitHub Discussions**: Ask questions and discuss ideas
- **Discord Community**: Real-time help and community chat
- **GitHub Issues**: Report bugs and request features

## 📄 License Agreement

By contributing to Memora, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You

Every contribution, no matter how small, helps make Memora better for everyone. Thank you for being part of the future of AI memory!
```

### **Code of Conduct**
```markdown
# Code of Conduct

## Our Commitment

We are committed to providing a welcoming and inclusive experience for all contributors, regardless of:
- Age, disability, ethnicity, gender identity and expression
- Level of experience, nationality, race, religion
- Sexual orientation, socioeconomic status

## Expected Behavior

- Use welcoming and inclusive language
- Respect different viewpoints and experiences
- Accept constructive feedback gracefully
- Focus on what's best for the community
- Show empathy towards other community members

## Unacceptable Behavior

- Harassment, discrimination, or derogatory comments
- Personal attacks or trolling
- Sharing private information without permission
- Other conduct that could reasonably be considered inappropriate

## Enforcement

Community leaders will enforce this code fairly and consistently. Violations may result in temporary or permanent bans from the community.

## Reporting

Report violations to: conduct@memora.ai

All reports will be kept confidential and investigated promptly.

## Attribution

This Code of Conduct is adapted from the Contributor Covenant, version 2.1.
```

### **Security Policy**
```markdown
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | ✅ Active support  |
| 0.9.x   | ⚠️ Security fixes only |
| < 0.9   | ❌ No support      |

## Reporting Security Vulnerabilities

**DO NOT** report security vulnerabilities through public GitHub issues.

Instead, please report them to: **security@memora.ai**

Include the following information:
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact and attack scenarios
- Any suggested fixes (if available)

## Response Timeline

- **24 hours**: Initial response acknowledging receipt
- **72 hours**: Initial assessment and severity rating
- **7 days**: Detailed investigation and fix timeline
- **30 days**: Public disclosure (after fix is released)

## Security Features

### Local-First Architecture
- All memory storage is local by default
- No data transmitted to external services without explicit consent
- Optional encryption for sensitive memories

### Access Controls
- File-system level access controls
- Optional API authentication
- Configurable memory access permissions

### Data Privacy
- Memory data never leaves your machine by default
- Optional secure export features
- Clear data retention policies

## Security Best Practices

### For Users
- Keep Memora updated to latest version
- Use strong passwords for encrypted memories
- Regularly backup your memory data
- Review memory permissions for integrations

### For Developers
- Validate all input data
- Use parameterized queries for any database operations
- Implement proper error handling
- Follow secure coding practices

## Acknowledgments

We appreciate security researchers who responsibly disclose vulnerabilities. Contributors will be acknowledged in our security advisories (with their permission).
```

---

## 🎨 **WEBSITE STYLING & ASSETS**

### **Main CSS Framework**
```css
/* assets/css/main.css */

:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --accent-color: #f093fb;
    --text-dark: #2d3748;
    --text-light: #718096;
    --background-light: #f7fafc;
    --background-dark: #1a202c;
    --border-light: #e2e8f0;
    --success-color: #48bb78;
    --warning-color: #ed8936;
    --error-color: #f56565;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: var(--text-dark);
}

/* Navigation */
.navbar {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--border-light);
    position: fixed;
    width: 100%;
    top: 0;
    z-index: 1000;
}

.nav-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-logo {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary-color);
}

/* Hero Section */
.hero {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    color: white;
    padding: 8rem 2rem 4rem;
    min-height: 100vh;
    display: flex;
    align-items: center;
}

.hero-content {
    max-width: 1200px;
    margin: 0 auto;
    text-align: center;
}

.hero h1 {
    font-size: 3.5rem;
    font-weight: 800;
    margin-bottom: 1rem;
    background: linear-gradient(45deg, #fff, #f0f8ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-subtitle {
    font-size: 1.5rem;
    margin-bottom: 2rem;
    opacity: 0.9;
}

.feature-badge {
    display: inline-block;
    background: rgba(255, 255, 255, 0.2);
    padding: 0.5rem 1rem;
    border-radius: 2rem;
    margin: 0.5rem;
    font-weight: 500;
}

/* Buttons */
.btn {
    display: inline-block;
    padding: 1rem 2rem;
    border-radius: 0.5rem;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.3s ease;
    border: 2px solid transparent;
    cursor: pointer;
}

.btn-primary {
    background: var(--accent-color);
    color: white;
    border-color: var(--accent-color);
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(240, 147, 251, 0.3);
}

/* Features Grid */
.features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 2rem;
    max-width: 1200px;
    margin: 0 auto;
}

.feature-card {
    background: white;
    padding: 2rem;
    border-radius: 1rem;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease;
}

.feature-card:hover {
    transform: translateY(-5px);
}

/* Demo Interface */
.demo-interface {
    background: var(--background-dark);
    border-radius: 1rem;
    overflow: hidden;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.demo-tabs {
    display: flex;
    background: #2d3748;
    border-bottom: 1px solid #4a5568;
}

.tab-button {
    background: none;
    border: none;
    padding: 1rem 2rem;
    color: #a0aec0;
    cursor: pointer;
    transition: all 0.3s ease;
}

.tab-button.active,
.tab-button:hover {
    color: white;
    background: var(--primary-color);
}

/* Chat Interface */
.chat-interface {
    height: 400px;
    display: flex;
    flex-direction: column;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    background: #1a202c;
}

.message {
    margin-bottom: 1rem;
    padding: 1rem;
    border-radius: 0.5rem;
}

.message.ai {
    background: #2d3748;
    color: #e2e8f0;
}

.message.user {
    background: var(--primary-color);
    color: white;
    margin-left: 2rem;
}

/* Terminal */
.terminal {
    background: #000;
    color: #00ff00;
    font-family: 'Monaco', 'Menlo', monospace;
    padding: 1rem;
    height: 300px;
    overflow-y: auto;
}

.terminal-line {
    margin-bottom: 0.5rem;
}

.prompt {
    color: #00ff00;
}

.command {
    color: #ffffff;
}

.output {
    color: #ffff00;
    margin-left: 1rem;
}

/* Memory Cards */
.memory-card {
    background: white;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 1rem;
    border-left: 4px solid var(--primary-color);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.memory-text {
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
    color: var(--text-dark);
}

.memory-meta {
    display: flex;
    gap: 0.5rem;
    align-items: center;
}

.tag {
    background: var(--background-light);
    color: var(--text-light);
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.8rem;
}

/* Responsive Design */
@media (max-width: 768px) {
    .hero h1 {
        font-size: 2.5rem;
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
    }
    
    .features-grid {
        grid-template-columns: 1fr;
    }
    
    .nav-menu {
        display: none; /* Mobile menu toggle needed */
    }
}
```

### **Interactive Demo JavaScript**
```javascript
// assets/js/demo-terminal.js

class MemoraDemo {
    constructor() {
        this.memories = [];
        this.currentBranch = 'main';
        this.chatHistory = [];
        this.initializeDemo();
    }

    initializeDemo() {
        // Initialize chat interface
        this.initChat();
        
        // Initialize CLI terminal
        this.initTerminal();
        
        // Initialize memory view
        this.initMemoryView();
        
        // Tab switching
        this.initTabs();
    }

    initChat() {
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-button');
        const chatMessages = document.getElementById('chat-messages');

        const sendMessage = () => {
            const message = chatInput.value.trim();
            if (!message) return;

            // Add user message
            this.addChatMessage('user', 'You', message);
            
            // Extract memories from user message
            this.extractMemories(message);
            
            // Generate AI response
            setTimeout(() => {
                const response = this.generateAIResponse(message);
                this.addChatMessage('ai', 'Memora AI', response);
            }, 1000);

            chatInput.value = '';
        };

        sendButton.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }

    addChatMessage(type, author, content) {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.innerHTML = `
            <span class="message-author">${author}</span>
            <div class="message-content">${content}</div>
        `;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    extractMemories(text) {
        // Simple demo extraction patterns
        const patterns = [
            {
                regex: /my name is (\w+)/i,
                extract: (match) => ({
                    memory: `User's name is ${match[1]}`,
                    category: 'personal',
                    confidence: 0.95
                })
            },
            {
                regex: /i work at (\w+)/i,
                extract: (match) => ({
                    memory: `User works at ${match[1]}`,
                    category: 'work',
                    confidence: 0.90
                })
            },
            {
                regex: /i (like|love|prefer) (\w+)/i,
                extract: (match) => ({
                    memory: `User ${match[1]}s ${match[2]}`,
                    category: 'preference',
                    confidence: 0.85
                })
            }
        ];

        patterns.forEach(pattern => {
            const match = text.match(pattern.regex);
            if (match) {
                const memory = pattern.extract(match);
                this.addMemory(memory);
            }
        });
    }

    addMemory(memory) {
        memory.id = `mem_${Math.random().toString(36).substr(2, 8)}`;
        memory.created_at = new Date().toISOString();
        memory.branch = this.currentBranch;
        
        this.memories.push(memory);
        this.updateMemoryView();
    }

    generateAIResponse(userMessage) {
        // Find relevant memories
        const relevantMemories = this.memories.filter(mem => 
            userMessage.toLowerCase().includes(mem.memory.toLowerCase().split(' ')[2]) ||
            userMessage.toLowerCase().includes(mem.category)
        );

        if (relevantMemories.length > 0) {
            const context = relevantMemories.map(m => m.memory).join(', ');
            return `Based on what I know about you (${context}), I can help you with that! What specifically would you like to know?`;
        }

        return "I'd be happy to help! Tell me more about yourself so I can provide personalized assistance.";
    }

    initTerminal() {
        const terminalInput = document.getElementById('cli-input');
        const terminalOutput = document.getElementById('terminal-output');

        terminalInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const command = terminalInput.value.trim();
                this.executeCommand(command);
                terminalInput.value = '';
            }
        });
    }

    executeCommand(command) {
        const output = document.getElementById('terminal-output');
        
        // Add command to terminal
        const commandLine = document.createElement('div');
        commandLine.className = 'terminal-line';
        commandLine.innerHTML = `<span class="prompt">$ </span><span class="command">${command}</span>`;
        output.appendChild(commandLine);

        // Process command
        let result = '';
        if (command.startsWith('memora search')) {
            const query = command.split(' ').slice(2).join(' ').replace(/['"]/g, '');
            const matches = this.memories.filter(m => 
                m.memory.toLowerCase().includes(query.toLowerCase())
            );
            result = matches.length > 0 
                ? matches.map(m => `📝 ${m.memory}`).join('\n')
                : 'No memories found';
        } else if (command.startsWith('memora add')) {
            const text = command.split(' ').slice(2).join(' ').replace(/['"]/g, '');
            this.extractMemories(text);
            result = `✅ Memory added: "${text}"`;
        } else if (command === 'memora list') {
            result = this.memories.map(m => `📝 ${m.memory} (${m.category})`).join('\n');
        } else {
            result = `Command not found: ${command}`;
        }

        // Add result to terminal
        const resultLine = document.createElement('div');
        resultLine.className = 'terminal-line output';
        resultLine.textContent = result;
        output.appendChild(resultLine);

        // Add new prompt
        const promptLine = document.createElement('div');
        promptLine.className = 'terminal-line';
        promptLine.innerHTML = '<span class="prompt">$ </span><span class="cursor">|</span>';
        output.appendChild(promptLine);

        output.scrollTop = output.scrollHeight;
    }

    updateMemoryView() {
        const memoryList = document.getElementById('memory-list');
        memoryList.innerHTML = '';

        this.memories.forEach(memory => {
            const memoryCard = document.createElement('div');
            memoryCard.className = 'memory-card';
            memoryCard.innerHTML = `
                <div class="memory-text">${memory.memory}</div>
                <div class="memory-meta">
                    <span class="tag">${memory.category}</span>
                    <span class="tag confidence">${Math.round(memory.confidence * 100)}% confident</span>
                    <span class="timestamp">${new Date(memory.created_at).toLocaleDateString()}</span>
                </div>
            `;
            memoryList.appendChild(memoryCard);
        });
    }

    initTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabPanels = document.querySelectorAll('.tab-panel');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.dataset.tab;

                // Update active tab button
                tabButtons.forEach(b => b.classList.remove('active'));
                button.classList.add('active');

                // Update active tab panel
                tabPanels.forEach(panel => {
                    panel.classList.remove('active');
                    if (panel.id === `${targetTab}-panel`) {
                        panel.classList.add('active');
                    }
                });
            });
        });
    }

    initMemoryView() {
        // Initialize with some demo memories
        this.addMemory({
            memory: "User is interested in AI and machine learning",
            category: "interest",
            confidence: 0.8
        });
        
        this.addMemory({
            memory: "User is exploring Memora's capabilities",
            category: "activity",
            confidence: 0.9
        });
    }
}

// Initialize demo when page loads
document.addEventListener('DOMContentLoaded', () => {
    new MemoraDemo();
});
```

---

## 🎯 **FOSS HACK PRESENTATION STRATEGY**

### **5-Minute Demo Script**
```markdown
# Memora FOSS HACK Demo Script

## Opening Hook (30 seconds)
"Imagine an AI that never forgets your preferences, learns from your conversations, and evolves its understanding over time. Today I'm presenting Memora - the world's first Git-style versioned memory system for Large Language Models."

## Problem Statement (30 seconds)
"Current AI systems have three critical problems:
1. They forget everything between conversations
2. Memory conflicts are treated as errors to resolve
3. Users can't see what their AI remembers

Memora solves all three with a revolutionary approach."

## Core Innovation Demo (2 minutes)
### Live Terminal Demo:
```bash
# Show automatic memory extraction
$ memora add "My name is Alex and I work at TechCorp as a Python developer"
✅ Added 3 memories: name, workplace, programming language

# Show memory search
$ memora search "Python" 
📝 User works with Python programming

# Show conversational AI with memory
$ memora chat
> "What programming language do I prefer?"
< "Based on our previous conversations, you prefer Python programming"

# Show conflict preservation (not resolution)
$ memora add "I actually prefer JavaScript now"
⚠️ Conflict detected - preserving both preferences with timestamps
```

## Advanced Features (1.5 minutes)
### Code Intelligence:
```bash
$ memora ingest repo ./my-project
📊 Analyzed 47 files, extracted 23 development insights
$ memora search "authentication"
📝 Project uses JWT tokens for API authentication
📝 Auth middleware implemented in middleware/auth.py
```

### Web Dashboard:
- Show beautiful memory visualization
- Real-time search across all memories
- Memory timeline showing evolution

## Impact & Open Source (30 seconds)
"Memora is production-ready with 85% test coverage, sub-millisecond performance, and MIT license. It's the memory layer every AI application needs."

## Call to Action (30 seconds)
"Visit memora.ai to try the live demo, star us on GitHub, and join the revolution in AI memory. Thank you!"
```

### **Visual Assets Needed**
```markdown
# Required Visual Assets

## Logos & Branding
- memora-logo.svg (primary logo)
- memora-symbol.svg (icon only)
- memora-wordmark.svg (text only)
- favicon.ico (16x16, 32x32, 48x48)

## Screenshots
- dashboard-screenshot.png (web interface)
- terminal-demo.gif (animated CLI demo)
- memory-timeline.png (memory evolution view)
- conflict-visualization.png (conflict preservation)

## Architecture Diagrams
- system-architecture.svg (3-layer architecture)
- memory-flow.svg (how memories are processed)
- git-style-branching.svg (branch visualization)

## Demo Videos
- 30-second-teaser.mp4 (social media)
- 5-minute-full-demo.mp4 (FOSS HACK presentation)
- installation-walkthrough.mp4 (getting started)

## Marketing Graphics
- feature-comparison.png (vs other memory systems)
- performance-benchmarks.png (speed/efficiency charts)
- use-cases-infographic.svg (applications diagram)
```

---

## 📊 **SUCCESS METRICS FOR FOSS HACK**

### **Technical Demonstration**
- ✅ **Live Demo**: Working web demo accessible to judges
- ✅ **Performance**: Sub-second response times during demo
- ✅ **Feature Coverage**: All major features demonstrated
- ✅ **Error Handling**: Graceful failure recovery

### **Documentation Quality**
- ✅ **Professional Website**: Modern, responsive design
- ✅ **Complete API Docs**: All endpoints and functions documented
- ✅ **Getting Started Guide**: 5-minute setup to working demo
- ✅ **Architecture Explanation**: Clear system design documentation

### **Open Source Excellence**
- ✅ **MIT License**: Clear licensing and attribution
- ✅ **Contributing Guidelines**: Detailed contribution workflow
- ✅ **Code Quality**: 85%+ test coverage, type safety
- ✅ **Community Ready**: Discord, GitHub discussions, roadmap

### **Innovation Impact**
- ✅ **Novel Approach**: First Git-style memory system
- ✅ **Real Problem Solved**: Persistent AI memory with conflict awareness
- ✅ **Production Quality**: Performance, scalability, reliability
- ✅ **Developer Experience**: Multiple APIs, easy integration

**This comprehensive website and documentation package positions Memora as a professional, innovative, and community-ready open source project worthy of FOSS HACK recognition.** 🏆