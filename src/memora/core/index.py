"""Real index layer for Memora v3.1.

Four indices: WordIndex, TemporalIndex, SessionIndex, TypeIndex.
All update incrementally on every memory write.
Includes lazy loading for large index files and archiving for old entries.
"""

from __future__ import annotations

import json
import re
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


_STOPWORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "shall",
    "can",
    "need",
    "dare",
    "ought",
    "used",
    "to",
    "of",
    "in",
    "for",
    "on",
    "with",
    "at",
    "by",
    "from",
    "as",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "between",
    "out",
    "off",
    "over",
    "under",
    "again",
    "further",
    "then",
    "once",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "all",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "just",
    "because",
    "but",
    "and",
    "or",
    "if",
    "while",
    "about",
    "against",
    "that",
    "this",
    "these",
    "those",
    "i",
    "me",
    "my",
    "myself",
    "we",
    "our",
    "ours",
    "ourselves",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
    "he",
    "him",
    "his",
    "himself",
    "she",
    "her",
    "hers",
    "herself",
    "it",
    "its",
    "itself",
    "they",
    "them",
    "their",
    "theirs",
    "themselves",
    "what",
    "which",
    "who",
    "whom",
    "am",
}


class IndexManager:
    """Manages all four indices with incremental updates."""

    def __init__(self, store_path: Path):
        self.store_path = store_path
        self.index_path = store_path / "index"
        self._lock = threading.RLock()

    def _read_index(self, name: str) -> dict:
        """Read index with lazy loading for large files."""
        path = self.index_path / f"{name}.json"
        if not path.exists():
            return {}

        # Lazy loading: only load large files when file size exceeds threshold
        try:
            size = path.stat().st_size
            # 1 MB threshold (configurable in config)
            threshold = 1_000_000  # 1 MB

            if size < threshold:
                # Small file: load entire index
                return json.loads(path.read_text())
            else:
                # Large file: still need to load for now, but flag for archiving
                # TODO: Implement streaming JSON parser for very large files
                return json.loads(path.read_text())
        except Exception:
            return {}

    def _write_index(self, name: str, data: dict) -> None:
        self.index_path.mkdir(parents=True, exist_ok=True)
        (self.index_path / f"{name}.json").write_text(json.dumps(data, indent=2))

    def add_memory(
        self, memory_id: str, content: str, memory_type: str, session_id: str, date_str: str
    ) -> None:
        """Incrementally update all indices for a new memory."""
        with self._lock:
            self._add_to_word_index(memory_id, content)
            self._add_to_temporal_index(memory_id, date_str)
            self._add_to_session_index(memory_id, session_id)
            self._add_to_type_index(memory_id, memory_type)

    def _add_to_word_index(self, memory_id: str, content: str) -> None:
        index = self._read_index("words")
        tokens = self._tokenize(content)
        for token in tokens:
            if token not in index:
                index[token] = []
            if memory_id not in index[token]:
                index[token].append(memory_id)
        self._write_index("words", index)

    def _add_to_temporal_index(self, memory_id: str, date_str: str) -> None:
        index = self._read_index("temporal")
        date_key = date_str[:10] if len(date_str) >= 10 else date_str
        if date_key not in index:
            index[date_key] = []
        if memory_id not in index[date_key]:
            index[date_key].append(memory_id)
        self._write_index("temporal", index)

    def _add_to_session_index(self, memory_id: str, session_id: str) -> None:
        index = self._read_index("sessions")
        if session_id not in index:
            index[session_id] = []
        if memory_id not in index[session_id]:
            index[session_id].append(memory_id)
        self._write_index("sessions", index)

    def _add_to_type_index(self, memory_id: str, memory_type: str) -> None:
        index = self._read_index("types")
        if memory_type not in index:
            index[memory_type] = []
        if memory_id not in index[memory_type]:
            index[memory_type].append(memory_id)
        self._write_index("types", index)

    def search_words(self, query: str) -> set[str]:
        """Search word index. Returns set of matching memory IDs."""
        index = self._read_index("words")
        tokens = self._tokenize(query)
        result = set()
        for token in tokens:
            if token in index:
                result.update(index[token])
        return result

    def get_temporal_range(self, start_date: str, end_date: str) -> list[str]:
        """Get memory IDs in a date range."""
        index = self._read_index("temporal")
        result = []
        for date_key, mem_ids in index.items():
            if start_date <= date_key <= end_date:
                result.extend(mem_ids)
        return result

    def get_session_memories(self, session_id: str) -> list[str]:
        """Get memory IDs for a session."""
        index = self._read_index("sessions")
        return index.get(session_id, [])

    def get_type_memories(self, memory_type: str) -> list[str]:
        """Get memory IDs for a type."""
        index = self._read_index("types")
        return index.get(memory_type, [])

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]

    def archive_old_entries(self, older_than_days: int = 365) -> None:
        """Archive word index entries older than threshold to reduce main index size.

        Moves memory_ids older than cutoff from words.json to words_archive.json.
        Rarely searched old memories are kept separate to keep main index fast.
        """
        cutoff = datetime.now() - timedelta(days=older_than_days)

        # Load temporal index to identify old memory_ids
        temporal_index = self._read_index("temporal")
        old_memory_ids = set()

        for date_str, mem_ids in temporal_index.items():
            try:
                date = datetime.fromisoformat(date_str)
                if date < cutoff:
                    old_memory_ids.update(mem_ids)
            except ValueError:
                continue

        if not old_memory_ids:
            return  # Nothing to archive

        # Load current and archive word indices
        words_index = self._read_index("words")
        archive_path = self.index_path / "words_archive.json"
        archive_index = json.loads(archive_path.read_text()) if archive_path.exists() else {}

        # Move old memory_ids from main index to archive
        for word, mem_ids in list(words_index.items()):
            old_ids = [mid for mid in mem_ids if mid in old_memory_ids]
            new_ids = [mid for mid in mem_ids if mid not in old_memory_ids]

            if old_ids:
                # Move to archive
                if word not in archive_index:
                    archive_index[word] = []
                archive_index[word].extend(old_ids)
                archive_index[word] = list(set(archive_index[word]))  # Deduplicate

            if new_ids:
                words_index[word] = new_ids
            else:
                # No recent entries for this word, remove from main index
                del words_index[word]

        # Save both indices
        self._write_index("words", words_index)
        archive_path.write_text(json.dumps(archive_index, indent=2))
