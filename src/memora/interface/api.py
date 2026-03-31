"""Memora API module - Facade for the Memora memory system."""

from pathlib import Path
from .server import app, start_server
from .readable_memory import ReadableMemoryManager


class MemoraStore:
    """Simple facade for the Memora memory system."""

    def __init__(self, memory_root: str = "./memora_data"):
        """Initialize Memora store."""
        self.memory_root = Path(memory_root)
        self.memory_root.mkdir(exist_ok=True)
        self.manager = ReadableMemoryManager(self.memory_root)
        self._session_id = None

    def _get_session(self) -> str:
        """Get or create a persistent session."""
        if self._session_id is None:
            self._session_id = self.manager.start_conversation("main")
        return self._session_id

    def add(self, text: str, source: str = "api") -> dict:
        """Add text to memory and return results."""
        session_id = self._get_session()
        return self.manager.add_message(session_id, text, source)

    def search(self, query: str, limit: int = 20) -> list:
        """Search memories."""
        session_id = self._get_session()
        return self.manager.search_memories(session_id=session_id, search_text=query, limit=limit)

    def get_all(self) -> list:
        """Get all memories."""
        session_id = self._get_session()
        return self.manager.search_memories(session_id=session_id, limit=1000)


__all__ = ["app", "start_server", "MemoraStore"]

# API facade for easy integration
