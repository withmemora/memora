"""Content-addressable object store for Memora v3.0.

Stores Memory objects using Git-style content-addressable storage with
zlib compression, SHA-256 hashing, and LRU caching.
"""

from __future__ import annotations

import functools
import json
import os
import secrets
import uuid
from pathlib import Path
from typing import Any

from filelock import FileLock, Timeout

from memora.shared.exceptions import (
    HashMismatchError,
    ObjectNotFoundError,
    StoreLockError,
)
from memora.shared.models import (
    Memory,
    MemoryCommit,
    MemoryTree,
)


class ObjectStore:
    """Content-addressable object store with atomic writes and locking."""

    def __init__(self, store_path: Path):
        self.store_path = store_path
        self.objects_path = store_path / "objects"
        self.lock_path = store_path / ".write_lock"
        self._lock = FileLock(str(self.lock_path), timeout=30)

    def _object_path_from_hash(self, obj_hash: str) -> Path:
        return self.objects_path / obj_hash[:2] / obj_hash[2:]

    @staticmethod
    def _serialize(obj: Memory | MemoryTree | MemoryCommit) -> tuple[bytes, str]:
        obj_dict = obj.to_dict()
        json_str = json.dumps(obj_dict, separators=(",", ":"), sort_keys=True)
        json_bytes = json_str.encode("utf-8")

        import zlib

        compressed = zlib.compress(json_bytes, level=6)

        import hashlib

        obj_hash = hashlib.sha256(compressed).hexdigest()
        return compressed, obj_hash

    @staticmethod
    def _deserialize_memory(data: bytes, expected_hash: str) -> Memory:
        import zlib

        json_bytes = zlib.decompress(data)
        json_str = json_bytes.decode("utf-8")
        obj_dict = json.loads(json_str)
        memory = Memory.from_dict(obj_dict)

        import hashlib

        actual_hash = hashlib.sha256(data).hexdigest()
        if actual_hash != expected_hash:
            raise HashMismatchError(f"Hash mismatch for memory {memory.id}")
        return memory

    @staticmethod
    def _deserialize_tree(data: bytes, expected_hash: str) -> MemoryTree:
        import zlib

        json_bytes = zlib.decompress(data)
        json_str = json_bytes.decode("utf-8")
        obj_dict = json.loads(json_str)
        tree = MemoryTree.from_dict(obj_dict)

        import hashlib

        actual_hash = hashlib.sha256(data).hexdigest()
        if actual_hash != expected_hash:
            raise HashMismatchError(f"Hash mismatch for tree")
        return tree

    @staticmethod
    def _deserialize_commit(data: bytes, expected_hash: str) -> MemoryCommit:
        import zlib

        json_bytes = zlib.decompress(data)
        json_str = json_bytes.decode("utf-8")
        obj_dict = json.loads(json_str)
        commit = MemoryCommit.from_dict(obj_dict)

        import hashlib

        actual_hash = hashlib.sha256(data).hexdigest()
        if actual_hash != expected_hash:
            raise HashMismatchError(f"Hash mismatch for commit")
        return commit

    def write(self, obj: Memory | MemoryTree | MemoryCommit) -> str:
        """Write object atomically. Returns the object hash."""
        compressed_bytes, obj_hash = self._serialize(obj)
        final_path = self._object_path_from_hash(obj_hash)

        if final_path.exists():
            return obj_hash

        final_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_dir = self.objects_path / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / str(uuid.uuid4())
        tmp_path.write_bytes(compressed_bytes)
        os.replace(str(tmp_path), str(final_path))
        return obj_hash

    @functools.lru_cache(maxsize=1000)
    def read_memory(self, obj_hash: str) -> Memory:
        path = self._object_path_from_hash(obj_hash)
        if not path.exists():
            raise ObjectNotFoundError(f"Memory not found: {obj_hash[:8]}...")
        data = path.read_bytes()
        return self._deserialize_memory(data, obj_hash)

    def read_tree(self, obj_hash: str) -> MemoryTree:
        path = self._object_path_from_hash(obj_hash)
        if not path.exists():
            raise ObjectNotFoundError(f"Tree not found: {obj_hash[:8]}...")
        data = path.read_bytes()
        return self._deserialize_tree(data, obj_hash)

    def read_commit(self, obj_hash: str) -> MemoryCommit:
        path = self._object_path_from_hash(obj_hash)
        if not path.exists():
            raise ObjectNotFoundError(f"Commit not found: {obj_hash[:8]}...")
        data = path.read_bytes()
        return self._deserialize_commit(data, obj_hash)

    def exists(self, obj_hash: str) -> bool:
        return self._object_path_from_hash(obj_hash).exists()

    def acquire_lock(self) -> None:
        try:
            self._lock.acquire()
        except Timeout:
            raise StoreLockError("Write lock timeout. Another process may be writing.")

    def release_lock(self) -> None:
        try:
            self._lock.release()
        except Exception:
            pass

    def list_all_hashes(self) -> list[str]:
        hashes: list[str] = []
        if not self.objects_path.exists():
            return hashes
        for subdir in self.objects_path.iterdir():
            if subdir.name == "tmp":
                continue
            if not subdir.is_dir():
                continue
            for obj_file in subdir.iterdir():
                if obj_file.is_file():
                    full_hash = subdir.name + obj_file.name
                    if len(full_hash) == 64:
                        hashes.append(full_hash)
        return hashes

    @staticmethod
    def initialize_directories(store_path: Path) -> None:
        directories = [
            store_path / "objects",
            store_path / "objects" / "tmp",
            store_path / "refs" / "heads",
            store_path / "sessions" / "active",
            store_path / "sessions" / "closed",
            store_path / "graph",
            store_path / "index",
            store_path / "branches",
            store_path / "conflicts" / "open",
            store_path / "conflicts" / "resolved",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        head_file = store_path / "HEAD"
        if not head_file.exists():
            head_file.write_text("ref: refs/heads/main")

        branches_meta = store_path / "branches" / "meta.json"
        if not branches_meta.exists():
            branches_meta.write_text("{}")

        graph_nodes = store_path / "graph" / "nodes.json"
        if not graph_nodes.exists():
            graph_nodes.write_text("[]")

        graph_edges = store_path / "graph" / "edges.json"
        if not graph_edges.exists():
            graph_edges.write_text("[]")

        for index_file in ["words.json", "temporal.json", "sessions.json", "types.json"]:
            idx = store_path / "index" / index_file
            if not idx.exists():
                idx.write_text("{}")

        config_file = store_path / "config"
        if not config_file.exists():
            config = {
                "core": {"version": "3.0", "created_at": secrets.token_hex(8)},
                "proxy": {
                    "listen_port": 11435,
                    "target_port": 11434,
                    "session_timeout_minutes": 5,
                    "auto_commit": True,
                },
                "branches": {
                    "session_limit": 100,
                    "memory_limit": 5000,
                    "time_limit_days": 90,
                    "naming_strategy": "sequential",
                },
                "extraction": {
                    "min_confidence": 0.80,
                    "enable_code_extraction": True,
                    "enable_graph": True,
                    "spacy_model": "en_core_web_sm",
                },
                "index": {
                    "enable_word_index": True,
                    "enable_temporal_index": True,
                    "enable_session_index": True,
                    "lru_cache_size": 1000,
                },
                "dashboard": {
                    "default_memories_per_page": 50,
                    "default_branch": "main",
                },
            }
            config_file.write_text(json.dumps(config, indent=2))

        if os.name != "nt":
            os.chmod(store_path, 0o700)
