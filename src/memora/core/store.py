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
    """Content-addressable object store with atomic writes and locking.

    Objects are stored at paths derived from their hash:
    objects/{hash[:2]}/{hash[2:]}

    All writes are atomic (tmp file -> os.replace).
    Write lock prevents concurrent modifications.
    """

    def __init__(self, store_path: Path):
        """Initialize object store.

        Args:
            store_path: Path to .memora/ directory
        """
        self.store_path = store_path
        self.objects_path = store_path / "objects"
        self.lock_path = store_path / ".write_lock"
        self._lock = FileLock(str(self.lock_path), timeout=30)

    def _object_path(self, hash: str) -> Path:
        """Compute storage path for a hash.

        Uses Git-style two-character subdirectory to avoid
        filesystem slowdown with many files in one directory.

        Args:
            hash: 64-character hex string (SHA-256)

        Returns:
            Path: objects/{hash[:2]}/{hash[2:]}
        """
        return self.objects_path / hash[:2] / hash[2:]

    def write(self, obj: Fact | MemoryTree | MemoryCommit) -> str:
        """Write object to store atomically.

        Idempotent - writing the same object twice creates only one file.
        Uses atomic write pattern (tmp -> os.replace) to prevent partial files.

        Args:
            obj: Object to write (Fact, MemoryTree, or MemoryCommit)

        Returns:
            SHA-256 hash of the object (64-char hex)
        """
        # 1. Serialize object
        if isinstance(obj, Fact):
            compressed_bytes, obj_hash = serialize_fact(obj)
        elif isinstance(obj, MemoryTree):
            compressed_bytes, obj_hash = serialize_tree(obj)
        elif isinstance(obj, MemoryCommit):
            compressed_bytes, obj_hash = serialize_commit(obj)
        else:
            raise TypeError(f"Unsupported object type: {type(obj)}")

        # 2. Compute final path
        final_path = self._object_path(obj_hash)

        # 3. Free deduplication - if exists, return immediately
        if final_path.exists():
            return obj_hash

        # 4. Create subdirectory
        final_path.parent.mkdir(parents=True, exist_ok=True)

        # 5. Write to tmp file
        tmp_dir = self.objects_path / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / str(uuid.uuid4())

        # 6. Write bytes
        tmp_path.write_bytes(compressed_bytes)

        # 7. Atomic move
        os.replace(str(tmp_path), str(final_path))

        # 8. Return hash
        return obj_hash

    def read_fact(self, hash: str) -> Fact:
        """Read and verify a Fact from store.

        Args:
            hash: SHA-256 hash of the fact

        Returns:
            Fact object

        Raises:
            ObjectNotFoundError: If hash not in store
            HashMismatchError: If file content doesn't match hash (corruption)
        """
        # 1. Compute path
        path = self._object_path(hash)

        # 2. Check existence
        if not path.exists():
            raise ObjectNotFoundError(f"Object not found: {hash[:8]}...")

        # 3. Read bytes
        data = path.read_bytes()

        # 4. Deserialize
        fact = deserialize_fact(data)

        # 5. Verify hash by recomputing from fact (semantic identity)
        actual_hash = hash_fact(fact)
        if actual_hash != hash:
            raise HashMismatchError(
                f"Hash mismatch: expected {hash[:8]}..., got {actual_hash[:8]}..."
            )

        return fact

    def read_tree(self, hash: str) -> MemoryTree:
        """Read and verify a MemoryTree from store.

        Args:
            hash: SHA-256 hash of the tree

        Returns:
            MemoryTree object

        Raises:
            ObjectNotFoundError: If hash not in store
            HashMismatchError: If file content doesn't match hash (corruption)
        """
        path = self._object_path(hash)

        if not path.exists():
            raise ObjectNotFoundError(f"Object not found: {hash[:8]}...")

        data = path.read_bytes()
        verify_hash(data, hash)

        return deserialize_tree(data)

    def read_commit(self, hash: str) -> MemoryCommit:
        """Read and verify a MemoryCommit from store.

        Args:
            hash: SHA-256 hash of the commit

        Returns:
            MemoryCommit object

        Raises:
            ObjectNotFoundError: If hash not in store
            HashMismatchError: If file content doesn't match hash (corruption)
        """
        path = self._object_path(hash)

        if not path.exists():
            raise ObjectNotFoundError(f"Object not found: {hash[:8]}...")

        data = path.read_bytes()
        verify_hash(data, hash)

        return deserialize_commit(data)

    def exists(self, hash: str) -> bool:
        """Fast check if object exists in store.

        Does not read or deserialize - just checks file existence.

        Args:
            hash: SHA-256 hash to check

        Returns:
            True if object exists, False otherwise
        """
        return self._object_path(hash).exists()

    def acquire_lock(self) -> None:
        """Acquire write lock.

        Prevents concurrent writes to the store.
        30 second timeout.

        Raises:
            StoreLockError: If lock cannot be acquired within timeout
        """
        try:
            self._lock.acquire()
        except Timeout:
            raise StoreLockError("Write lock timeout. Another process may be writing.")

    def release_lock(self) -> None:
        """Release write lock.

        ALWAYS call in finally block to ensure lock is released
        even if an error occurs.
        """
        try:
            self._lock.release()
        except Exception:
            # Swallow exceptions - lock may already be released
            pass

    def list_all_hashes(self) -> list[str]:
        """List all object hashes in the store.

        Walks the objects/ directory and reconstructs hashes
        from subdirectory names and filenames.

        Skips the tmp/ subdirectory.

        Returns:
            List of 64-character hash strings
        """
        hashes: list[str] = []

        if not self.objects_path.exists():
            return hashes

        # Walk through two-character subdirectories
        for subdir in self.objects_path.iterdir():
            # Skip tmp directory
            if subdir.name == "tmp":
                continue

            # Skip if not a directory
            if not subdir.is_dir():
                continue

            # Each file in subdirectory is an object
            for obj_file in subdir.iterdir():
                if obj_file.is_file():
                    # Reconstruct hash: subdir_name + filename
                    full_hash = subdir.name + obj_file.name
                    if len(full_hash) == 64:  # Valid SHA-256 hash
                        hashes.append(full_hash)

        return hashes

    @staticmethod
    def initialize_directories(store_path: Path) -> None:
        """Create complete .memora/ directory structure.

        Creates all required directories and files for a new Memora store.
        Safe to call on existing store - won't overwrite existing files.

        Args:
            store_path: Path to .memora/ directory (will be created)
        """
        # Create all required directories
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

        # Write HEAD file (only if doesn't exist)
        head_file = store_path / "HEAD"
        if not head_file.exists():
            head_file.write_text("ref: refs/heads/main")

        # Write empty STAGE file
        stage_file = store_path / "staging" / "STAGE"
        if not stage_file.exists():
            stage_file.write_text("[]")

        # Write empty index files
        entities_index = store_path / "index" / "entities.json"
        if not entities_index.exists():
            entities_index.write_text("{}")

        topics_index = store_path / "index" / "topics.json"
        if not topics_index.exists():
            topics_index.write_text("{}")

        temporal_index = store_path / "index" / "temporal.json"
        if not temporal_index.exists():
            temporal_index.write_text("[]")

        # Write config file
        config_file = store_path / "config"
        if not config_file.exists():
            config = {
                "auto_commit": True,
                "max_context_tokens": 2000,
                "conflict_mode": "lenient",
                "default_branch": "main",
                "api_key": secrets.token_hex(16),  # 32-char hex string
            }
            config_file.write_text(json.dumps(config, indent=2))

        # Set permissions on non-Windows
        if os.name != "nt":
            os.chmod(store_path, 0o700)
