"""Content-addressable object store for Memora.

This module implements Git-style storage with atomic writes, file locking,
and content deduplication. All objects are stored at paths derived from
their SHA-256 hash.
"""

import json
import os
import secrets
import uuid
from pathlib import Path

from filelock import FileLock, Timeout

from memora.core.objects import (
    deserialize_commit,
    deserialize_fact,
    deserialize_tree,
    hash_fact,
    serialize_commit,
    serialize_fact,
    serialize_tree,
    verify_hash,
)
from memora.shared.exceptions import (
    HashMismatchError,
    ObjectNotFoundError,
    StoreLockError,
)
from memora.shared.models import Fact, MemoryCommit, MemoryTree


class ObjectStore:
    """Content-addressable object store with atomic writes and locking."""

    def __init__(self, store_path: Path):
        self.store_path = store_path
        self.objects_path = store_path / "objects"
        self.lock_path = store_path / ".write_lock"
        self._lock = FileLock(str(self.lock_path), timeout=30)

    def _object_path(self, hash: str) -> Path:
        return self.objects_path / hash[:2] / hash[2:]

    def write(self, obj: Fact | MemoryTree | MemoryCommit) -> str:
        if isinstance(obj, Fact):
            compressed_bytes, obj_hash = serialize_fact(obj)
        elif isinstance(obj, MemoryTree):
            compressed_bytes, obj_hash = serialize_tree(obj)
        elif isinstance(obj, MemoryCommit):
            compressed_bytes, obj_hash = serialize_commit(obj)
        else:
            raise TypeError(f"Unsupported object type: {type(obj)}")

        final_path = self._object_path(obj_hash)

        if final_path.exists():
            return obj_hash

        final_path.parent.mkdir(parents=True, exist_ok=True)

        tmp_dir = self.objects_path / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / str(uuid.uuid4())

        tmp_path.write_bytes(compressed_bytes)
        os.replace(str(tmp_path), str(final_path))

        return obj_hash

    def read_fact(self, hash: str) -> Fact:
        path = self._object_path(hash)

        if not path.exists():
            raise ObjectNotFoundError(f"Object not found: {hash[:8]}...")

        data = path.read_bytes()
        fact = deserialize_fact(data)

        actual_hash = hash_fact(fact)
        if actual_hash != hash:
            raise HashMismatchError(
                f"Hash mismatch: expected {hash[:8]}..., got {actual_hash[:8]}..."
            )

        return fact

    def read_tree(self, hash: str) -> MemoryTree:
        path = self._object_path(hash)

        if not path.exists():
            raise ObjectNotFoundError(f"Object not found: {hash[:8]}...")

        data = path.read_bytes()
        verify_hash(data, hash)

        return deserialize_tree(data)

    def read_commit(self, hash: str) -> MemoryCommit:
        path = self._object_path(hash)

        if not path.exists():
            raise ObjectNotFoundError(f"Object not found: {hash[:8]}...")

        data = path.read_bytes()
        verify_hash(data, hash)

        return deserialize_commit(data)

    def exists(self, hash: str) -> bool:
        return self._object_path(hash).exists()

    def acquire_lock(self) -> None:
        try:
            self._lock.acquire()
        except Timeout:
            raise StoreLockError("Write lock timeout.")

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

    # ✅ FIXED: search method INSIDE class
    def search(self, query: str) -> list[str]:
        """Search facts by keyword."""
        results = []

        all_hashes = self.list_all_hashes()

        for h in all_hashes:
            try:
                fact = self.read_fact(h)
                if query.lower() in fact.content.lower():
                    results.append(fact.content)
            except:
                pass

        return results

    @staticmethod
    def initialize_directories(store_path: Path) -> None:
        directories = [
            store_path / "objects",
            store_path / "objects" / "tmp",
            store_path / "refs" / "heads",
            store_path / "staging",
            store_path / "conflicts" / "open",
            store_path / "conflicts" / "resolved",
            store_path / "index",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        head_file = store_path / "HEAD"
        if not head_file.exists():
            head_file.write_text("ref: refs/heads/main")

        stage_file = store_path / "staging" / "STAGE"
        if not stage_file.exists():
            stage_file.write_text("[]")

        entities_index = store_path / "index" / "entities.json"
        if not entities_index.exists():
            entities_index.write_text("{}")

        topics_index = store_path / "index" / "topics.json"
        if not topics_index.exists():
            topics_index.write_text("{}")

        temporal_index = store_path / "index" / "temporal.json"
        if not temporal_index.exists():
            temporal_index.write_text("[]")

        config_file = store_path / "config"
        if not config_file.exists():
            config = {
                "auto_commit": True,
                "max_context_tokens": 2000,
                "conflict_mode": "lenient",
                "default_branch": "main",
                "api_key": secrets.token_hex(16),
            }
            config_file.write_text(json.dumps(config, indent=2))

        if os.name != "nt":
            os.chmod(store_path, 0o700)