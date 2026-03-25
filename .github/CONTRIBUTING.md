# Contributing to Memora

Thank you for your interest in contributing to Memora! This document provides guidelines and information for contributors.

## Quick Start

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/memora.git`
3. Install dependencies: `poetry install`
4. Download spaCy model: `poetry run python -m spacy download en_core_web_sm`
5. Run tests: `poetry run pytest`
6. Make your changes
7. Submit a pull request

## Development Setup

### Prerequisites
- Python 3.11+
- Poetry (for dependency management)
- Git

### Installation
```bash
git clone https://github.com/yourusername/memora.git
cd memora
poetry install
poetry run python -m spacy download en_core_web_sm
```

### Running Tests
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src/memora --cov-report=term --cov-report=html

# Run specific test file
poetry run pytest tests/core/test_engine.py

# Run tests with verbose output
poetry run pytest -v
```

### Code Quality
```bash
# Lint code
poetry run ruff check src/ tests/

# Format code
poetry run ruff format src/ tests/

# Type checking
poetry run mypy src/memora/
```

## Project Structure

Memora follows a clean 3-layer architecture:

```
src/memora/
├── core/           # Layer 1: Core memory engine
│   ├── engine.py   # Main memory engine
│   ├── store.py    # Git-style storage
│   ├── conflicts.py # Conflict detection
│   └── ...
├── interface/      # Layer 2: User interfaces  
│   ├── cli.py      # Command-line interface
│   ├── api.py      # REST API
│   ├── server.py   # Web server
│   └── ...
└── shared/         # Layer 3: Shared models
    ├── models.py   # Data models
    ├── interfaces.py # Abstract interfaces
    └── ...
```

## Contribution Guidelines

### Types of Contributions

1. **Bug Fixes** - Fix issues in existing functionality
2. **New Features** - Add new capabilities to Memora
3. **Performance Improvements** - Optimize existing code
4. **Documentation** - Improve docs, examples, or comments
5. **Tests** - Add or improve test coverage
6. **Refactoring** - Improve code structure without changing behavior

### Before You Start

1. Check existing issues and PRs to avoid duplication
2. For major changes, open an issue first to discuss the approach
3. Make sure you understand the Memora architecture and design principles

### Design Principles

1. **Git-Like Memory Management** - Memories are versioned with content-addressable storage
2. **Conflict as Evolution** - Memory conflicts are preserved as branching evolution, not errors
3. **Clean Architecture** - Maintain separation between core, interface, and shared layers
4. **Performance First** - Optimize for memory operations and search performance
5. **Type Safety** - Use type hints and maintain mypy compliance
6. **Comprehensive Testing** - Maintain high test coverage (>85%)

### Making Changes

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes following the coding standards
3. Add tests for new functionality
4. Update documentation if needed
5. Commit with clear, descriptive messages
6. Push to your fork and create a pull request

### Commit Message Format

Use conventional commits:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Refactoring without functionality change
- `test`: Adding or modifying tests
- `perf`: Performance improvements
- `chore`: Maintenance tasks

Examples:
```
feat(core): add automatic memory conflict detection
fix(api): handle empty search results correctly
docs(readme): update installation instructions
```

### Code Style

- Follow PEP 8 Python style guidelines
- Use type hints for all functions and methods
- Keep functions focused and small (< 50 lines typically)
- Use descriptive variable and function names
- Add docstrings for public APIs
- Format code with Ruff: `poetry run ruff format`

### Testing

- Write unit tests for all new functionality
- Use pytest fixtures for common test setup
- Mock external dependencies (file system, network, etc.)
- Test edge cases and error conditions
- Aim for >85% test coverage

Example test structure:
```python
import pytest
from memora.core.engine import MemoryEngine

class TestMemoryEngine:
    @pytest.fixture
    def engine(self):
        return MemoryEngine()
    
    def test_add_memory_success(self, engine):
        # Test implementation
        pass
    
    def test_add_memory_duplicate_handling(self, engine):
        # Test implementation  
        pass
```

### Documentation

- Update README.md if adding user-facing features
- Add docstrings to public functions and classes
- Update CLI help text for new commands
- Add examples for new functionality
- Keep docs up-to-date with code changes

## Memory Layers

Understanding Memora's layered architecture helps guide contributions:

### Layer 1: Personal Memory
- Core memory storage and retrieval
- Conflict detection and resolution
- Git-style versioning
- NLP extraction and processing

### Layer 2: Document Intelligence  
- PDF, Word, CSV ingestion
- Text extraction and processing
- Structured data handling

### Layer 3: Project Memory
- Branch management
- Pack export/import
- Team collaboration features

### Layer 4: Code Intelligence
- AST parsing and analysis
- Incremental repository ingestion
- Code-aware memory extraction

### Layer 5: Memory Health
- Memory decay over time
- Health scoring algorithms
- Memory reinforcement

## Pull Request Process

1. **Create PR** - Open a pull request with a clear title and description
2. **Fill Template** - Complete the PR template with all relevant information
3. **Review** - Respond to review feedback promptly
4. **Update** - Make requested changes and push updates
5. **Merge** - Once approved, your PR will be merged

### PR Requirements

- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated if needed
- [ ] No breaking changes (or clearly documented)
- [ ] Performance impact assessed

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and provide helpful feedback
- Focus on what's best for the community
- Show empathy towards other contributors

### Getting Help

- **Issues** - For bugs, feature requests, and questions
- **Discussions** - For general questions and community chat
- **Discord** - Real-time community support (link in README)

### Recognition

Contributors are recognized in several ways:
- Listed in CONTRIBUTORS.md
- Tagged in release notes for their contributions
- Special recognition for significant contributions

## Release Process

Memora follows semantic versioning (SemVer):

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions  
- **PATCH** version for backwards-compatible bug fixes

## Security

If you discover a security vulnerability, please email the maintainers directly rather than opening a public issue.

## License

By contributing to Memora, you agree that your contributions will be licensed under the MIT License.

## Questions?

Don't hesitate to ask questions by:
- Opening an issue with the "question" label
- Starting a discussion in GitHub Discussions
- Joining our community Discord

Thank you for contributing to Memora! 🚀