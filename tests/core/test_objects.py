"""Tests for core/objects.py serialization and hashing."""

import json
import zlib
from datetime import datetime

import pytest

from memora.core.objects import (
    deserialize_commit,
    deserialize_fact,
    deserialize_tree,
    hash_bytes,
    hash_fact,
    hash_object,
    serialize_commit,
    serialize_fact,
    serialize_tree,
    verify_hash,
)
from memora.shared.exceptions import HashMismatchError
from memora.shared.models import (
    ContentType,
    Fact,
    MemoryCommit,
    MemoryTree,
    MemoryTreeEntry,
)


class TestHashBytes:
    """Test hash_bytes function."""

    def test_hash_bytes_deterministic(self):
        """Test that same bytes always produce same hash."""
        data = b"test data"
        hash1 = hash_bytes(data)
        hash2 = hash_bytes(data)
        assert hash1 == hash2

    def test_hash_bytes_length(self):
        """Test that hash is 64 characters (SHA-256)."""
        data = b"anything"
        result = hash_bytes(data)
        assert len(result) == 64

    def test_hash_bytes_different_data(self):
        """Test that different data produces different hash."""
        hash1 = hash_bytes(b"data1")
        hash2 = hash_bytes(b"data2")
        assert hash1 != hash2

    def test_hash_bytes_hex_string(self):
        """Test that hash is valid hex string."""
        data = b"test"
        result = hash_bytes(data)
        # Should not raise ValueError
        int(result, 16)


class TestHashObject:
    """Test hash_object function."""

    def test_hash_object_deterministic(self):
        """Test that same dict always produces same hash."""
        obj = {"name": "Alice", "age": 30}
        hash1 = hash_object(obj)
        hash2 = hash_object(obj)
        assert hash1 == hash2

    def test_hash_object_key_order_independent(self):
        """Test that key order doesn't affect hash (sort_keys)."""
        obj1 = {"b": 1, "a": 2}
        obj2 = {"a": 2, "b": 1}
        hash1 = hash_object(obj1)
        hash2 = hash_object(obj2)
        assert hash1 == hash2

    def test_hash_object_different_values(self):
        """Test that different values produce different hash."""
        obj1 = {"name": "Alice"}
        obj2 = {"name": "Bob"}
        hash1 = hash_object(obj1)
        hash2 = hash_object(obj2)
        assert hash1 != hash2

    def test_hash_object_nested_dicts(self):
        """Test hashing nested dictionaries."""
        obj1 = {"outer": {"inner": "value"}}
        obj2 = {"outer": {"inner": "value"}}
        hash1 = hash_object(obj1)
        hash2 = hash_object(obj2)
        assert hash1 == hash2


class TestHashFact:
    """Test hash_fact function."""

    def test_hash_fact_semantic_identity(self):
        """Test that hash includes only semantic identity fields."""
        now = datetime.now()
        fact1 = Fact(
            content="My name is Alice",
            content_type=ContentType.TRIPLE,
            entity="user",
            attribute="name",
            value="Alice",
            source="source1",
            observed_at=now,
            confidence=0.95,
        )

        fact2 = Fact(
            content="Different content",
            content_type=ContentType.TRIPLE,
            entity="user",
            attribute="name",
            value="Alice",
            source="source2",
            observed_at=datetime(2020, 1, 1),
            confidence=0.50,
        )

        # Same semantic content = same hash despite different metadata
        hash1 = hash_fact(fact1)
        hash2 = hash_fact(fact2)
        assert hash1 == hash2

    def test_hash_fact_excludes_metadata(self):
        """Test that changing metadata doesn't change hash."""
        base_fact = Fact(
            content="test",
            content_type=ContentType.TRIPLE,
            entity="user",
            attribute="name",
            value="Alice",
            source="s1",
            observed_at=datetime.now(),
            confidence=0.95,
        )

        base_hash = hash_fact(base_fact)

        # Change source
        fact2 = Fact(
            content=base_fact.content,
            content_type=base_fact.content_type,
            entity=base_fact.entity,
            attribute=base_fact.attribute,
            value=base_fact.value,
            source="different_source",
            observed_at=base_fact.observed_at,
            confidence=base_fact.confidence,
        )
        assert hash_fact(fact2) == base_hash

        # Change timestamp
        fact3 = Fact(
            content=base_fact.content,
            content_type=base_fact.content_type,
            entity=base_fact.entity,
            attribute=base_fact.attribute,
            value=base_fact.value,
            source=base_fact.source,
            observed_at=datetime(2020, 1, 1),
            confidence=base_fact.confidence,
        )
        assert hash_fact(fact3) == base_hash

        # Change confidence
        fact4 = Fact(
            content=base_fact.content,
            content_type=base_fact.content_type,
            entity=base_fact.entity,
            attribute=base_fact.attribute,
            value=base_fact.value,
            source=base_fact.source,
            observed_at=base_fact.observed_at,
            confidence=0.10,
        )
        assert hash_fact(fact4) == base_hash

    def test_hash_fact_case_normalization(self):
        """Test that entity and attribute are lowercased in hash."""
        now = datetime.now()
        fact1 = Fact(
            content="test",
            content_type=ContentType.TRIPLE,
            entity="User",
            attribute="Name",
            value="Alice",
            source="test",
            observed_at=now,
            confidence=1.0,
        )

        fact2 = Fact(
            content="test",
            content_type=ContentType.TRIPLE,
            entity="user",
            attribute="name",
            value="Alice",
            source="test",
            observed_at=now,
            confidence=1.0,
        )

        # Should have same hash due to lowercase normalization
        assert hash_fact(fact1) == hash_fact(fact2)

    def test_hash_fact_different_values(self):
        """Test that different values produce different hash."""
        now = datetime.now()
        fact1 = Fact(
            content="test",
            content_type=ContentType.TRIPLE,
            entity="user",
            attribute="name",
            value="Alice",
            source="test",
            observed_at=now,
            confidence=1.0,
        )

        fact2 = Fact(
            content="test",
            content_type=ContentType.TRIPLE,
            entity="user",
            attribute="name",
            value="Bob",
            source="test",
            observed_at=now,
            confidence=1.0,
        )

        assert hash_fact(fact1) != hash_fact(fact2)

    def test_hash_fact_deterministic_100_times(self):
        """Test that same fact produces same hash 100 times."""
        now = datetime.now()
        fact = Fact(
            content="test",
            content_type=ContentType.TRIPLE,
            entity="user",
            attribute="name",
            value="Alice",
            source="test",
            observed_at=now,
            confidence=1.0,
        )

        hashes = [hash_fact(fact) for _ in range(100)]
        assert len(set(hashes)) == 1  # All identical


class TestSerializeFact:
    """Test serialize_fact function."""

    def test_serialize_fact_returns_tuple(self):
        """Test that serialize returns (bytes, str) tuple."""
        now = datetime.now()
        fact = Fact(
            content="test",
            content_type=ContentType.TRIPLE,
            entity="user",
            attribute="name",
            value="Alice",
            source="test",
            observed_at=now,
            confidence=1.0,
        )

        result = serialize_fact(fact)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bytes)
        assert isinstance(result[1], str)

    def test_serialize_fact_compressed(self):
        """Test that output is actually compressed."""
        now = datetime.now()
        fact = Fact(
            content="test",
            content_type=ContentType.TRIPLE,
            entity="user",
            attribute="name",
            value="Alice",
            source="test",
            observed_at=now,
            confidence=1.0,
        )

        compressed, _ = serialize_fact(fact)

        # Should be able to decompress
        decompressed = zlib.decompress(compressed)
        assert isinstance(decompressed, bytes)

        # Should be valid JSON
        json_str = decompressed.decode("utf-8")
        data = json.loads(json_str)
        assert "entity" in data

    def test_serialize_fact_uses_hash_fact(self):
        """Test that serialization uses hash_fact (not hash_object)."""
        now = datetime.now()
        fact = Fact(
            content="test",
            content_type=ContentType.TRIPLE,
            entity="user",
            attribute="name",
            value="Alice",
            source="test",
            observed_at=now,
            confidence=1.0,
        )

        _, fact_hash = serialize_fact(fact)
        expected_hash = hash_fact(fact)

        assert fact_hash == expected_hash

    def test_serialize_fact_deterministic(self):
        """Test that same fact produces same serialization."""
        now = datetime.now()
        fact = Fact(
            content="test",
            content_type=ContentType.TRIPLE,
            entity="user",
            attribute="name",
            value="Alice",
            source="test",
            observed_at=now,
            confidence=1.0,
        )

        compressed1, hash1 = serialize_fact(fact)
        compressed2, hash2 = serialize_fact(fact)

        assert compressed1 == compressed2
        assert hash1 == hash2


class TestDeserializeFact:
    """Test deserialize_fact function."""

    def test_deserialize_fact_roundtrip(self):
        """Test serialize -> deserialize returns identical fact."""
        now = datetime.now()
        original = Fact(
            content="My name is Alice",
            content_type=ContentType.TRIPLE,
            entity="user",
            attribute="name",
            value="Alice",
            source="conversation:session-001",
            observed_at=now,
            confidence=0.95,
        )

        compressed, _ = serialize_fact(original)
        restored = deserialize_fact(compressed)

        assert restored.content == original.content
        assert restored.content_type == original.content_type
        assert restored.entity == original.entity
        assert restored.attribute == original.attribute
        assert restored.value == original.value
        assert restored.source == original.source
        # Compare timestamps at second precision (microseconds may vary in serialization)
        assert restored.observed_at.replace(microsecond=0) == original.observed_at.replace(
            microsecond=0
        )
        assert restored.confidence == original.confidence

    def test_deserialize_fact_all_content_types(self):
        """Test deserialization for all ContentType enums."""
        now = datetime.now()

        for content_type in ContentType:
            fact = Fact(
                content="test",
                content_type=content_type,
                entity="test_entity",
                attribute="test_attr",
                value="test_value",
                source="test",
                observed_at=now,
                confidence=0.75,
            )

            compressed, _ = serialize_fact(fact)
            restored = deserialize_fact(compressed)

            assert restored.content_type == content_type


class TestSerializeTree:
    """Test serialize_tree function."""

    def test_serialize_tree_empty(self):
        """Test serializing empty tree."""
        tree = MemoryTree(entries=[])

        compressed, tree_hash = serialize_tree(tree)

        assert isinstance(compressed, bytes)
        assert isinstance(tree_hash, str)
        assert len(tree_hash) == 64

    def test_serialize_tree_with_entries(self):
        """Test serializing tree with entries."""
        entries = [
            MemoryTreeEntry(name="user", entry_type="fact", hash="hash1"),
            MemoryTreeEntry(name="project", entry_type="subtree", hash="hash2"),
        ]
        tree = MemoryTree(entries=entries)

        compressed, _ = serialize_tree(tree)

        # Should be compressed
        decompressed = zlib.decompress(compressed)
        data = json.loads(decompressed.decode("utf-8"))

        assert "entries" in data
        assert len(data["entries"]) == 2

    def test_serialize_tree_sorts_entries(self):
        """Test that entries are sorted by name for determinism."""
        # Create entries in non-alphabetical order
        entries = [
            MemoryTreeEntry(name="zebra", entry_type="fact", hash="hash3"),
            MemoryTreeEntry(name="apple", entry_type="fact", hash="hash1"),
            MemoryTreeEntry(name="middle", entry_type="fact", hash="hash2"),
        ]
        tree = MemoryTree(entries=entries)

        compressed, _ = serialize_tree(tree)
        decompressed = zlib.decompress(compressed)
        data = json.loads(decompressed.decode("utf-8"))

        # Entries should be sorted alphabetically
        names = [e["name"] for e in data["entries"]]
        assert names == sorted(names)

    def test_serialize_tree_deterministic(self):
        """Test that same tree produces same serialization regardless of entry order."""
        entries1 = [
            MemoryTreeEntry(name="b", entry_type="fact", hash="hash2"),
            MemoryTreeEntry(name="a", entry_type="fact", hash="hash1"),
        ]

        entries2 = [
            MemoryTreeEntry(name="a", entry_type="fact", hash="hash1"),
            MemoryTreeEntry(name="b", entry_type="fact", hash="hash2"),
        ]

        tree1 = MemoryTree(entries=entries1)
        tree2 = MemoryTree(entries=entries2)

        compressed1, hash1 = serialize_tree(tree1)
        compressed2, hash2 = serialize_tree(tree2)

        # Should be identical despite different insertion order
        assert compressed1 == compressed2
        assert hash1 == hash2


class TestDeserializeTree:
    """Test deserialize_tree function."""

    def test_deserialize_tree_roundtrip(self):
        """Test serialize -> deserialize returns identical tree."""
        entries = [
            MemoryTreeEntry(name="user", entry_type="fact", hash="hash1"),
            MemoryTreeEntry(name="project", entry_type="subtree", hash="hash2"),
        ]
        original = MemoryTree(entries=entries)

        compressed, _ = serialize_tree(original)
        restored = deserialize_tree(compressed)

        assert len(restored.entries) == len(original.entries)
        for i, entry in enumerate(restored.entries):
            # Entries may be sorted, so compare by name
            orig_entry = next(e for e in original.entries if e.name == entry.name)
            assert entry.name == orig_entry.name
            assert entry.entry_type == orig_entry.entry_type
            assert entry.hash == orig_entry.hash


class TestSerializeCommit:
    """Test serialize_commit function."""

    def test_serialize_commit_with_parent(self):
        """Test serializing commit with parent."""
        now = datetime.now()
        commit = MemoryCommit(
            root_tree_hash="tree_hash_123",
            parent_hash="parent_hash_456",
            author="test_user",
            message="Initial commit",
            committed_at=now,
        )

        compressed, commit_hash = serialize_commit(commit)

        assert isinstance(compressed, bytes)
        assert isinstance(commit_hash, str)
        assert len(commit_hash) == 64

    def test_serialize_commit_no_parent(self):
        """Test serializing first commit (no parent)."""
        now = datetime.now()
        commit = MemoryCommit(
            root_tree_hash="tree_hash_123",
            parent_hash=None,
            author="test_user",
            message="Initial commit",
            committed_at=now,
        )

        compressed, _ = serialize_commit(commit)

        decompressed = zlib.decompress(compressed)
        data = json.loads(decompressed.decode("utf-8"))

        assert data["parent_hash"] is None

    def test_serialize_commit_deterministic(self):
        """Test that same commit produces same serialization."""
        now = datetime.now()
        commit = MemoryCommit(
            root_tree_hash="tree_hash",
            parent_hash="parent_hash",
            author="alice",
            message="Test commit",
            committed_at=now,
        )

        compressed1, hash1 = serialize_commit(commit)
        compressed2, hash2 = serialize_commit(commit)

        assert compressed1 == compressed2
        assert hash1 == hash2


class TestDeserializeCommit:
    """Test deserialize_commit function."""

    def test_deserialize_commit_roundtrip(self):
        """Test serialize -> deserialize returns identical commit."""
        now = datetime.now()
        original = MemoryCommit(
            root_tree_hash="tree_hash_abc",
            parent_hash="parent_hash_def",
            author="test_author",
            message="Test message",
            committed_at=now,
        )

        compressed, _ = serialize_commit(original)
        restored = deserialize_commit(compressed)

        assert restored.root_tree_hash == original.root_tree_hash
        assert restored.parent_hash == original.parent_hash
        assert restored.author == original.author
        assert restored.message == original.message
        # Compare at second precision
        assert restored.committed_at.replace(microsecond=0) == original.committed_at.replace(
            microsecond=0
        )


class TestVerifyHash:
    """Test verify_hash function."""

    def test_verify_hash_valid(self):
        """Test that valid hash passes verification."""
        data = b"test data"
        expected_hash = hash_bytes(data)

        # Should not raise
        verify_hash(data, expected_hash)

    def test_verify_hash_mismatch_raises(self):
        """Test that invalid hash raises HashMismatchError."""
        data = b"test data"
        wrong_hash = "0" * 64

        with pytest.raises(HashMismatchError) as exc_info:
            verify_hash(data, wrong_hash)

        assert "Hash mismatch" in str(exc_info.value)
        assert "expected" in str(exc_info.value)

    def test_verify_hash_corrupted_data(self):
        """Test detecting corrupted data."""
        # Serialize a fact
        now = datetime.now()
        fact = Fact(
            content="test",
            content_type=ContentType.TRIPLE,
            entity="user",
            attribute="name",
            value="Alice",
            source="test",
            observed_at=now,
            confidence=1.0,
        )

        compressed, original_hash = serialize_fact(fact)

        # Corrupt the data
        corrupted = compressed[:-5] + b"xxxxx"

        # Should raise
        with pytest.raises(HashMismatchError):
            verify_hash(corrupted, original_hash)


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_fact_full_cycle(self):
        """Test complete serialize -> verify -> deserialize cycle for Fact."""
        now = datetime.now()
        original = Fact(
            content="The deadline is March 31st",
            content_type=ContentType.DATE_VALUE,
            entity="current_project",
            attribute="deadline",
            value="March 31st",
            source="conversation:session-042",
            observed_at=now,
            confidence=0.90,
        )

        # Serialize
        compressed, fact_hash = serialize_fact(original)

        # Verify (should not raise)
        # Note: For facts, verify_hash checks the compressed data,
        # but the hash is computed from semantic identity
        # So we verify the compressed data produces the expected compressed hash
        compressed_hash = hash_bytes(compressed)
        verify_hash(compressed, compressed_hash)

        # Deserialize
        restored = deserialize_fact(compressed)

        # Verify content matches
        assert restored.value == original.value
        assert restored.entity == original.entity
        assert restored.attribute == original.attribute

    def test_tree_full_cycle(self):
        """Test complete serialize -> verify -> deserialize cycle for Tree."""
        entries = [
            MemoryTreeEntry(name="fact1", entry_type="fact", hash="abc123"),
            MemoryTreeEntry(name="subtree1", entry_type="subtree", hash="def456"),
        ]
        original = MemoryTree(entries=entries)

        # Serialize
        compressed, tree_hash = serialize_tree(original)

        # Verify
        verify_hash(compressed, tree_hash)

        # Deserialize
        restored = deserialize_tree(compressed)

        assert len(restored.entries) == 2

    def test_commit_full_cycle(self):
        """Test complete serialize -> verify -> deserialize cycle for Commit."""
        now = datetime.now()
        original = MemoryCommit(
            root_tree_hash="root_abc",
            parent_hash="parent_def",
            author="alice",
            message="Add user facts",
            committed_at=now,
        )

        # Serialize
        compressed, commit_hash = serialize_commit(original)

        # Verify
        verify_hash(compressed, commit_hash)

        # Deserialize
        restored = deserialize_commit(compressed)

        assert restored.message == original.message
        assert restored.author == original.author
