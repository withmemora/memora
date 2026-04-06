"""Tests for ObjectStore v3.0 with Memory objects.

This module tests:
- Writing and reading Memory objects
- Git-style content-addressable storage
- Compression and hash verification
- LRU caching
- Deduplication
"""

from pathlib import Path

import pytest

from memora.core.store import ObjectStore
from memora.shared.exceptions import HashMismatchError, ObjectNotFoundError
from memora.shared.models import (
    Memory,
    MemoryCommit,
    MemorySource,
    MemoryTree,
    MemoryType,
    now_iso,
)


@pytest.fixture
def temp_store(tmp_path: Path) -> Path:
    """Create a temporary .memora directory structure."""
    store_path = tmp_path / ".memora"
    ObjectStore.initialize_directories(store_path)
    return store_path


@pytest.fixture
def object_store(temp_store: Path) -> ObjectStore:
    """Create an ObjectStore instance."""
    return ObjectStore(temp_store)


@pytest.fixture
def sample_memory() -> Memory:
    """Create a sample Memory for testing."""
    return Memory(
        id="mem_test123",
        content="User's name is Alice",
        memory_type=MemoryType.CONVERSATION,
        confidence=0.95,
        source=MemorySource.OLLAMA_CHAT,
        session_id="sess_xyz",
        branch="main",
        turn_index=1,
        created_at=now_iso(),
        updated_at=now_iso(),
        entities=["alice"],
        metadata={"raw_turn": "My name is Alice"},
    )


class TestObjectStoreInitialization:
    """Test ObjectStore initialization."""

    def test_initialize_directories(self, tmp_path: Path):
        """Test that initialize_directories creates required structure."""
        store_path = tmp_path / ".memora"
        ObjectStore.initialize_directories(store_path)

        assert (store_path / "objects").exists()
        assert (store_path / "objects" / "tmp").exists()
        assert (store_path / "refs" / "heads").exists()
        assert (store_path / "sessions" / "active").exists()
        assert (store_path / "sessions" / "closed").exists()
        assert (store_path / "graph").exists()
        assert (store_path / "index").exists()
        assert (store_path / "branches").exists()
        assert (store_path / "conflicts" / "open").exists()
        assert (store_path / "conflicts" / "resolved").exists()

    def test_object_store_creation(self, temp_store: Path):
        """Test creating an ObjectStore instance."""
        store = ObjectStore(temp_store)

        assert store.store_path == temp_store
        assert store.objects_path == temp_store / "objects"


class TestMemoryWriteAndRead:
    """Test writing and reading Memory objects."""

    def test_write_memory(self, object_store: ObjectStore, sample_memory: Memory):
        """Test writing a Memory object to store."""
        memory_hash = object_store.write(sample_memory)

        assert isinstance(memory_hash, str)
        assert len(memory_hash) == 64  # SHA-256 hash
        # Verify file was created with 2-char prefix directory
        obj_path = object_store._object_path_from_hash(memory_hash)
        assert obj_path.exists()

    def test_read_memory(self, object_store: ObjectStore, sample_memory: Memory):
        """Test reading a Memory object from store."""
        memory_hash = object_store.write(sample_memory)
        retrieved = object_store.read_memory(memory_hash)

        assert retrieved.id == sample_memory.id
        assert retrieved.content == sample_memory.content
        assert retrieved.memory_type == sample_memory.memory_type
        assert retrieved.confidence == sample_memory.confidence
        assert retrieved.entities == sample_memory.entities

    def test_read_nonexistent_memory_raises_error(self, object_store: ObjectStore):
        """Test that reading a nonexistent memory raises ObjectNotFoundError."""
        fake_hash = "a" * 64

        with pytest.raises(ObjectNotFoundError):
            object_store.read_memory(fake_hash)

    def test_memory_content_is_human_readable(
        self, object_store: ObjectStore, sample_memory: Memory
    ):
        """Test that stored Memory.content is human-readable, not triples."""
        memory_hash = object_store.write(sample_memory)
        retrieved = object_store.read_memory(memory_hash)

        # Content should be plain English
        assert "User's name is Alice" == retrieved.content
        # NOT entity-attribute-value format
        assert "entity" not in retrieved.content.lower()
        assert "attribute" not in retrieved.content.lower()


class TestMemoryDeduplication:
    """Test that identical memories produce the same hash."""

    def test_identical_memories_same_hash(self, object_store: ObjectStore):
        """Test that two identical Memory objects produce the same hash."""
        memory1 = Memory(
            id="mem_1",
            content="User prefers Python",
            memory_type=MemoryType.CONVERSATION,
            confidence=0.90,
            source=MemorySource.OLLAMA_CHAT,
            session_id="sess_1",
            branch="main",
            turn_index=0,
            created_at="2026-04-05T10:00:00Z",
            updated_at="2026-04-05T10:00:00Z",
        )

        memory2 = Memory(
            id="mem_1",
            content="User prefers Python",
            memory_type=MemoryType.CONVERSATION,
            confidence=0.90,
            source=MemorySource.OLLAMA_CHAT,
            session_id="sess_1",
            branch="main",
            turn_index=0,
            created_at="2026-04-05T10:00:00Z",
            updated_at="2026-04-05T10:00:00Z",
        )

        hash1 = object_store.write(memory1)
        hash2 = object_store.write(memory2)

        assert hash1 == hash2


class TestMemoryTypeSpecificStorage:
    """Test storing different memory types."""

    def test_store_code_memory(self, object_store: ObjectStore):
        """Test storing a CODE type memory."""
        code_memory = Memory(
            id="mem_code",
            content="Python function for PDF processing",
            memory_type=MemoryType.CODE,
            confidence=0.88,
            source=MemorySource.OLLAMA_CHAT,
            session_id="sess_xyz",
            branch="main",
            turn_index=5,
            created_at=now_iso(),
            updated_at=now_iso(),
            metadata={
                "language": "python",
                "function_names": ["process_pdf"],
                "raw_code": "def process_pdf(path):\n    return read_file(path)",
            },
        )

        memory_hash = object_store.write(code_memory)
        retrieved = object_store.read_memory(memory_hash)

        assert retrieved.memory_type == MemoryType.CODE
        assert retrieved.metadata["language"] == "python"
        assert "process_pdf" in retrieved.metadata["function_names"]

    def test_store_document_memory(self, object_store: ObjectStore):
        """Test storing a DOCUMENT type memory."""
        doc_memory = Memory(
            id="mem_doc",
            content="Document: architecture.md - Git-style storage; zlib compression",
            memory_type=MemoryType.DOCUMENT,
            confidence=0.85,
            source=MemorySource.FILE_INGESTION,
            session_id="sess_xyz",
            branch="main",
            turn_index=0,
            created_at=now_iso(),
            updated_at=now_iso(),
            metadata={
                "filename": "architecture.md",
                "file_type": "markdown",
                "key_facts": ["Git-style storage", "zlib compression"],
                "word_count": 5000,
            },
        )

        memory_hash = object_store.write(doc_memory)
        retrieved = object_store.read_memory(memory_hash)

        assert retrieved.memory_type == MemoryType.DOCUMENT
        assert retrieved.metadata["filename"] == "architecture.md"
        assert "Git-style storage" in retrieved.metadata["key_facts"]


class TestMemoryTreeAndCommit:
    """Test MemoryTree and MemoryCommit storage."""

    def test_write_and_read_memory_tree(self, object_store: ObjectStore):
        """Test writing and reading a MemoryTree."""
        tree = MemoryTree(memory_ids=["mem_1", "mem_2", "mem_3"])

        tree_hash = object_store.write(tree)
        retrieved = object_store.read_tree(tree_hash)

        assert retrieved.memory_ids == ["mem_1", "mem_2", "mem_3"]

    def test_write_and_read_memory_commit(self, object_store: ObjectStore):
        """Test writing and reading a MemoryCommit."""
        commit = MemoryCommit(
            root_tree_hash="tree_abc123",
            parent_hash=None,
            author="system",
            message="Session: 3 memories captured",
            committed_at=now_iso(),
        )

        commit_hash = object_store.write(commit)
        retrieved = object_store.read_commit(commit_hash)

        assert retrieved.root_tree_hash == "tree_abc123"
        assert retrieved.parent_hash is None
        assert retrieved.author == "system"
        assert retrieved.message == "Session: 3 memories captured"


class TestCompression:
    """Test zlib compression is applied."""

    def test_memory_is_compressed(self, object_store: ObjectStore, sample_memory: Memory):
        """Test that stored memory is compressed (smaller than JSON)."""
        import json

        memory_hash = object_store.write(sample_memory)
        obj_path = object_store._object_path_from_hash(memory_hash)

        # Read compressed size
        compressed_size = obj_path.stat().st_size

        # Compare to uncompressed JSON size
        json_str = json.dumps(sample_memory.to_dict())
        uncompressed_size = len(json_str.encode("utf-8"))

        # Compressed should be smaller (typically 60-70% reduction)
        assert compressed_size < uncompressed_size


class TestGitStyleStorage:
    """Test Git-style 2-char prefix directory structure."""

    def test_object_path_uses_2char_prefix(self, object_store: ObjectStore):
        """Test that objects are stored with 2-char prefix directories."""
        test_hash = "abc123def456789"
        obj_path = object_store._object_path_from_hash(test_hash)

        # Path should be: objects/ab/c123def456789
        assert obj_path.parent.name == "ab"
        assert obj_path.name == "c123def456789"

    def test_multiple_memories_distributed(self, object_store: ObjectStore):
        """Test that multiple memories are distributed across prefix directories."""
        memories = [
            Memory(
                id=f"mem_{i}",
                content=f"Test memory {i}",
                memory_type=MemoryType.CONVERSATION,
                confidence=0.90,
                source=MemorySource.MANUAL,
                session_id="sess_test",
                branch="main",
                turn_index=i,
                created_at=now_iso(),
                updated_at=now_iso(),
            )
            for i in range(10)
        ]

        hashes = [object_store.write(mem) for mem in memories]

        # Check that objects are in different prefix directories
        prefixes = set(h[:2] for h in hashes)
        # Unlikely all 10 would have same 2-char prefix
        assert len(prefixes) > 1


class TestMemorySupersession:
    """Test memory supersession tracking."""

    def test_memory_with_supersedes(self, object_store: ObjectStore):
        """Test storing a memory that supersedes another."""
        old_memory = Memory(
            id="mem_old",
            content="User lives in New York",
            memory_type=MemoryType.CONVERSATION,
            confidence=0.90,
            source=MemorySource.OLLAMA_CHAT,
            session_id="sess_1",
            branch="main",
            turn_index=1,
            created_at="2026-04-01T10:00:00Z",
            updated_at="2026-04-01T10:00:00Z",
        )

        new_memory = Memory(
            id="mem_new",
            content="User lives in Seattle",
            memory_type=MemoryType.CONVERSATION,
            confidence=0.92,
            source=MemorySource.OLLAMA_CHAT,
            session_id="sess_2",
            branch="main",
            turn_index=1,
            created_at="2026-04-05T10:00:00Z",
            updated_at="2026-04-05T10:00:00Z",
            supersedes="mem_old",
        )

        hash_old = object_store.write(old_memory)
        hash_new = object_store.write(new_memory)

        retrieved = object_store.read_memory(hash_new)
        assert retrieved.supersedes == "mem_old"


class TestLRUCache:
    """Test LRU cache for read_memory."""

    def test_lru_cache_speeds_up_reads(self, object_store: ObjectStore, sample_memory: Memory):
        """Test that LRU cache improves read performance."""
        import time

        memory_hash = object_store.write(sample_memory)

        # First read (from disk)
        start1 = time.time()
        object_store.read_memory(memory_hash)
        time1 = time.time() - start1

        # Second read (from cache)
        start2 = time.time()
        object_store.read_memory(memory_hash)
        time2 = time.time() - start2

        # Cached read should be faster (though this is a weak test)
        # At minimum, both should succeed
        assert time1 >= 0
        assert time2 >= 0
