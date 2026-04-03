"""Memora API module - Facade for the Memora memory system v3.0."""

from pathlib import Path
from memora.core.engine import CoreEngine
from memora.shared.models import Memory


class MemoraStore:
    """Simple facade for the Memora memory system v3.0."""

    def __init__(self, memory_root: str = "./memora_data"):
        self.memory_root = Path(memory_root)
        self.memory_root.mkdir(parents=True, exist_ok=True)
        self.engine = CoreEngine()
        if (self.memory_root / ".memora").exists():
            self.engine.open_store(self.memory_root)
        else:
            self.engine.init_store(self.memory_root)

    def add(self, text: str, source: str = "api") -> dict:
        results = self.engine.ingest_text(text, source=source)
        return {
            "memories_created": len(results),
            "memories": [(m.id, m.content) for _, m in results],
        }

    def search(self, query: str, limit: int = 20) -> list:
        memories = self.engine.search_memories(query)
        return [
            {"id": m.id, "content": m.content, "confidence": m.confidence} for m in memories[:limit]
        ]

    def get_all(self) -> list:
        memories = self.engine.get_all_memories(skip=0, limit=1000)
        return [{"id": m.id, "content": m.content, "confidence": m.confidence} for m in memories]


__all__ = ["MemoraStore"]
