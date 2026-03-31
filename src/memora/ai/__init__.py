"""AI integration module for Memora.

This module provides AI capabilities including:
- File processing (TXT, MD, PDF)
- Conversational AI with Ollama
- Code snippet detection and storage
- Memory extraction from conversations
"""

from .file_processor import FileProcessor
from .conversational_ai import MemoraChat

__all__ = ["FileProcessor", "MemoraChat"]
