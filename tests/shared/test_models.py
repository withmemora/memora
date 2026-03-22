"""Tests for shared/models.py data structures."""

import hashlib
from datetime import datetime

import pytest

from memora.shared.models import (
    Conflict,
    ConflictStatus,
    ConflictType,
    ContentType,
    ContextBlock,
    Fact,
    MemoryCommit,
    MemoryTree,
    MemoryTreeEntry,
    QueryResult,
)


class TestContentType:
    """Test ContentType enum."""

    def test_content_type_values(self):
        """Test that ContentType enum has expected values."""
        assert ContentType.PLAIN_TEXT.value == "plain_text"
        assert ContentType.TRIPLE.value == "triple"
        assert ContentType.DATE_VALUE.value == "date_value"
        assert ContentType.PREFERENCE.value == "preference"


class TestConflictType:
    """Test ConflictType enum."""

    def test_conflict_type_values(self):
        """Test that ConflictType enum has expected values."""
        assert ConflictType.DIRECT_CONTRADICTION.value == "direct_contradiction"
        assert ConflictType.TEMPORAL_SUPERSESSION.value == "temporal_supersession"
        assert ConflictType.SOURCE_CONFLICT.value == "source_conflict"
        assert ConflictType.SCOPE_CONFLICT.value == "scope_conflict"
        assert ConflictType.UNCERTAIN.value == "uncertain"


class TestConflictStatus:
    """Test ConflictStatus enum."""

    def test_conflict_status_values(self):
        """Test that ConflictStatus enum has expected values."""
        assert ConflictStatus.UNRESOLVED.value == "unresolved"
        assert ConflictStatus.AUTO_RESOLVED.value == "auto_resolved"
        assert ConflictStatus.USER_RESOLVED.value == "user_resolved"
        assert ConflictStatus.AGENT_RESOLVED.value == "agent_resolved"


class TestFact:
    """Test Fact data class."""

    def test_fact_creation(self):
        """Test creating a Fact instance."""
        now = datetime.now()
        fact = Fact(
            content="User's name is Alice",
            content_type=ContentType.TRIPLE,
            entity="user",
            attribute="name",
            value="Alice",
            source="conversation:session-001",
            observed_at=now,
            confidence=0.95,
        )

        assert fact.content == "User's name is Alice"
        assert fact.content_type == ContentType.TRIPLE
        assert fact.entity == "user"
        assert fact.attribute == "name"
        assert fact.value == "Alice"
        assert fact.source == "conversation:session-001"
        assert fact.observed_at == now
        assert fact.confidence == 0.95

    def test_fact_compute_hash(self):
        """Test that hash is computed from content_type, entity, attribute, value only."""
        now = datetime.now()
        fact1 = Fact(
            content="User's name is Alice",
            content_type=ContentType.TRIPLE,
            entity="user",
            attribute="name",
            value="Alice",
            source="conversation:session-001",
            observed_at=now,
            confidence=0.95,
        )

        # Same semantic content, different source and confidence
        fact2 = Fact(
            content="The user is called Alice",
            content_type=ContentType.TRIPLE,
            entity="user",
            attribute="name",
            value="Alice",
            source="conversation:session-002",
            observed_at=now,
            confidence=0.85,
        )

        # Should have same hash despite different source/confidence
        hash1 = fact1.compute_hash()
        hash2 = fact2.compute_hash()
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 hex chars

        # Different value should produce different hash
        fact3 = Fact(
            content="User's name is Bob",
            content_type=ContentType.TRIPLE,
            entity="user",
            attribute="name",
            value="Bob",
            source="conversation:session-001",
            observed_at=now,
            confidence=0.95,
        )
        hash3 = fact3.compute_hash()
        assert hash1 != hash3

    def test_fact_hash_normalization(self):
        """Test that entity and attribute are lowercased in hash computation."""
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
        assert fact1.compute_hash() == fact2.compute_hash()

    def test_fact_to_dict(self):
        """Test serializing Fact to dictionary."""
        now = datetime(2024, 1, 15, 10, 30, 0)
        fact = Fact(
            content="User's name is Alice",
            content_type=ContentType.TRIPLE,
            entity="user",
            attribute="name",
            value="Alice",
            source="conversation:session-001",
            observed_at=now,
            confidence=0.95,
        )

        fact_dict = fact.to_dict()

        assert fact_dict["content"] == "User's name is Alice"
        assert fact_dict["content_type"] == "triple"
        assert fact_dict["entity"] == "user"
        assert fact_dict["attribute"] == "name"
        assert fact_dict["value"] == "Alice"
        assert fact_dict["source"] == "conversation:session-001"
        assert fact_dict["observed_at"] == now.isoformat()
        assert fact_dict["confidence"] == 0.95

    def test_fact_from_dict(self):
        """Test deserializing Fact from dictionary."""
        now = datetime(2024, 1, 15, 10, 30, 0)
        fact_dict = {
            "content": "User's name is Alice",
            "content_type": "triple",
            "entity": "user",
            "attribute": "name",
            "value": "Alice",
            "source": "conversation:session-001",
            "observed_at": now.isoformat(),
            "confidence": 0.95,
        }

        fact = Fact.from_dict(fact_dict)

        assert fact.content == "User's name is Alice"
        assert fact.content_type == ContentType.TRIPLE
        assert fact.entity == "user"
        assert fact.attribute == "name"
        assert fact.value == "Alice"
        assert fact.source == "conversation:session-001"
        assert fact.observed_at == now
        assert fact.confidence == 0.95

    def test_fact_roundtrip(self):
        """Test that Fact survives to_dict -> from_dict roundtrip."""
        now = datetime.now()
        original = Fact(
            content="Test content",
            content_type=ContentType.PREFERENCE,
            entity="test_entity",
            attribute="test_attr",
            value="test_value",
            source="test_source",
            observed_at=now,
            confidence=0.75,
        )

        fact_dict = original.to_dict()
        restored = Fact.from_dict(fact_dict)

        assert restored.content == original.content
        assert restored.content_type == original.content_type
        assert restored.entity == original.entity
        assert restored.attribute == original.attribute
        assert restored.value == original.value
        assert restored.source == original.source
        # Compare timestamps at microsecond precision (isoformat() preserves this)
        assert restored.observed_at.replace(microsecond=0) == original.observed_at.replace(
            microsecond=0
        )
        assert restored.confidence == original.confidence


class TestMemoryTreeEntry:
    """Test MemoryTreeEntry data class."""

    def test_memory_tree_entry_creation(self):
        """Test creating a MemoryTreeEntry."""
        entry = MemoryTreeEntry(
            name="user",
            entry_type="fact",
            hash="abc123",
        )

        assert entry.name == "user"
        assert entry.entry_type == "fact"
        assert entry.hash == "abc123"

    def test_memory_tree_entry_to_dict(self):
        """Test serializing MemoryTreeEntry to dictionary."""
        entry = MemoryTreeEntry(
            name="project",
            entry_type="subtree",
            hash="def456",
        )

        entry_dict = entry.to_dict()

        assert entry_dict["name"] == "project"
        assert entry_dict["entry_type"] == "subtree"
        assert entry_dict["hash"] == "def456"

    def test_memory_tree_entry_from_dict(self):
        """Test deserializing MemoryTreeEntry from dictionary."""
        entry_dict = {
            "name": "settings",
            "entry_type": "fact",
            "hash": "xyz789",
        }

        entry = MemoryTreeEntry.from_dict(entry_dict)

        assert entry.name == "settings"
        assert entry.entry_type == "fact"
        assert entry.hash == "xyz789"


class TestMemoryTree:
    """Test MemoryTree data class."""

    def test_memory_tree_creation_empty(self):
        """Test creating an empty MemoryTree."""
        tree = MemoryTree()

        assert tree.entries == []

    def test_memory_tree_creation_with_entries(self):
        """Test creating a MemoryTree with entries."""
        entries = [
            MemoryTreeEntry(name="user", entry_type="fact", hash="hash1"),
            MemoryTreeEntry(name="project", entry_type="subtree", hash="hash2"),
        ]

        tree = MemoryTree(entries=entries)

        assert len(tree.entries) == 2
        assert tree.entries[0].name == "user"
        assert tree.entries[1].name == "project"

    def test_memory_tree_to_dict(self):
        """Test serializing MemoryTree to dictionary."""
        entries = [
            MemoryTreeEntry(name="user", entry_type="fact", hash="hash1"),
            MemoryTreeEntry(name="project", entry_type="subtree", hash="hash2"),
        ]
        tree = MemoryTree(entries=entries)

        tree_dict = tree.to_dict()

        assert "entries" in tree_dict
        assert len(tree_dict["entries"]) == 2
        assert tree_dict["entries"][0]["name"] == "user"
        assert tree_dict["entries"][1]["name"] == "project"

    def test_memory_tree_from_dict(self):
        """Test deserializing MemoryTree from dictionary."""
        tree_dict = {
            "entries": [
                {"name": "user", "entry_type": "fact", "hash": "hash1"},
                {"name": "project", "entry_type": "subtree", "hash": "hash2"},
            ]
        }

        tree = MemoryTree.from_dict(tree_dict)

        assert len(tree.entries) == 2
        assert tree.entries[0].name == "user"
        assert tree.entries[0].entry_type == "fact"
        assert tree.entries[1].name == "project"
        assert tree.entries[1].entry_type == "subtree"


class TestMemoryCommit:
    """Test MemoryCommit data class."""

    def test_memory_commit_creation(self):
        """Test creating a MemoryCommit."""
        now = datetime.now()
        commit = MemoryCommit(
            root_tree_hash="tree_hash_123",
            parent_hash="parent_hash_456",
            author="test_user",
            message="Initial commit",
            committed_at=now,
        )

        assert commit.root_tree_hash == "tree_hash_123"
        assert commit.parent_hash == "parent_hash_456"
        assert commit.author == "test_user"
        assert commit.message == "Initial commit"
        assert commit.committed_at == now

    def test_memory_commit_creation_no_parent(self):
        """Test creating a MemoryCommit without a parent (first commit)."""
        now = datetime.now()
        commit = MemoryCommit(
            root_tree_hash="tree_hash_123",
            parent_hash=None,
            author="test_user",
            message="Initial commit",
            committed_at=now,
        )

        assert commit.parent_hash is None

    def test_memory_commit_to_dict(self):
        """Test serializing MemoryCommit to dictionary."""
        now = datetime(2024, 1, 15, 10, 30, 0)
        commit = MemoryCommit(
            root_tree_hash="tree_hash",
            parent_hash="parent_hash",
            author="alice",
            message="Add user facts",
            committed_at=now,
        )

        commit_dict = commit.to_dict()

        assert commit_dict["root_tree_hash"] == "tree_hash"
        assert commit_dict["parent_hash"] == "parent_hash"
        assert commit_dict["author"] == "alice"
        assert commit_dict["message"] == "Add user facts"
        assert commit_dict["committed_at"] == now.isoformat()

    def test_memory_commit_from_dict(self):
        """Test deserializing MemoryCommit from dictionary."""
        now = datetime(2024, 1, 15, 10, 30, 0)
        commit_dict = {
            "root_tree_hash": "tree_hash",
            "parent_hash": None,
            "author": "bob",
            "message": "Initial memory",
            "committed_at": now.isoformat(),
        }

        commit = MemoryCommit.from_dict(commit_dict)

        assert commit.root_tree_hash == "tree_hash"
        assert commit.parent_hash is None
        assert commit.author == "bob"
        assert commit.message == "Initial memory"
        assert commit.committed_at == now


class TestConflict:
    """Test Conflict data class."""

    def test_conflict_creation(self):
        """Test creating a Conflict."""
        now = datetime.now()
        conflict = Conflict(
            conflict_id="conflict_123",
            fact_a_hash="fact_a",
            fact_b_hash="fact_b",
            conflict_type=ConflictType.DIRECT_CONTRADICTION,
            conflict_status=ConflictStatus.UNRESOLVED,
            detected_at=now,
            resolution_fact_hash=None,
            resolution_reason=None,
            resolved_at=None,
        )

        assert conflict.conflict_id == "conflict_123"
        assert conflict.fact_a_hash == "fact_a"
        assert conflict.fact_b_hash == "fact_b"
        assert conflict.conflict_type == ConflictType.DIRECT_CONTRADICTION
        assert conflict.conflict_status == ConflictStatus.UNRESOLVED
        assert conflict.detected_at == now
        assert conflict.resolution_fact_hash is None
        assert conflict.resolution_reason is None
        assert conflict.resolved_at is None

    def test_conflict_resolved(self):
        """Test creating a resolved Conflict."""
        detected = datetime(2024, 1, 15, 10, 0, 0)
        resolved = datetime(2024, 1, 15, 11, 0, 0)

        conflict = Conflict(
            conflict_id="conflict_123",
            fact_a_hash="fact_a",
            fact_b_hash="fact_b",
            conflict_type=ConflictType.TEMPORAL_SUPERSESSION,
            conflict_status=ConflictStatus.USER_RESOLVED,
            detected_at=detected,
            resolution_fact_hash="fact_b",
            resolution_reason="More recent information",
            resolved_at=resolved,
        )

        assert conflict.conflict_status == ConflictStatus.USER_RESOLVED
        assert conflict.resolution_fact_hash == "fact_b"
        assert conflict.resolution_reason == "More recent information"
        assert conflict.resolved_at == resolved

    def test_conflict_to_dict(self):
        """Test serializing Conflict to dictionary."""
        now = datetime(2024, 1, 15, 10, 30, 0)
        conflict = Conflict(
            conflict_id="conflict_123",
            fact_a_hash="fact_a",
            fact_b_hash="fact_b",
            conflict_type=ConflictType.SOURCE_CONFLICT,
            conflict_status=ConflictStatus.UNRESOLVED,
            detected_at=now,
            resolution_fact_hash=None,
            resolution_reason=None,
            resolved_at=None,
        )

        conflict_dict = conflict.to_dict()

        assert conflict_dict["conflict_id"] == "conflict_123"
        assert conflict_dict["fact_a_hash"] == "fact_a"
        assert conflict_dict["fact_b_hash"] == "fact_b"
        assert conflict_dict["conflict_type"] == "source_conflict"
        assert conflict_dict["conflict_status"] == "unresolved"
        assert conflict_dict["detected_at"] == now.isoformat()
        assert conflict_dict["resolution_fact_hash"] is None
        assert conflict_dict["resolution_reason"] is None
        assert conflict_dict["resolved_at"] is None

    def test_conflict_to_dict_resolved(self):
        """Test serializing a resolved Conflict to dictionary."""
        detected = datetime(2024, 1, 15, 10, 0, 0)
        resolved = datetime(2024, 1, 15, 11, 0, 0)

        conflict = Conflict(
            conflict_id="conflict_123",
            fact_a_hash="fact_a",
            fact_b_hash="fact_b",
            conflict_type=ConflictType.UNCERTAIN,
            conflict_status=ConflictStatus.AUTO_RESOLVED,
            detected_at=detected,
            resolution_fact_hash="fact_a",
            resolution_reason="Higher confidence",
            resolved_at=resolved,
        )

        conflict_dict = conflict.to_dict()

        assert conflict_dict["resolution_fact_hash"] == "fact_a"
        assert conflict_dict["resolution_reason"] == "Higher confidence"
        assert conflict_dict["resolved_at"] == resolved.isoformat()

    def test_conflict_from_dict(self):
        """Test deserializing Conflict from dictionary."""
        now = datetime(2024, 1, 15, 10, 30, 0)
        conflict_dict = {
            "conflict_id": "conflict_456",
            "fact_a_hash": "hash_x",
            "fact_b_hash": "hash_y",
            "conflict_type": "scope_conflict",
            "conflict_status": "agent_resolved",
            "detected_at": now.isoformat(),
            "resolution_fact_hash": "hash_y",
            "resolution_reason": "Broader scope",
            "resolved_at": now.isoformat(),
        }

        conflict = Conflict.from_dict(conflict_dict)

        assert conflict.conflict_id == "conflict_456"
        assert conflict.fact_a_hash == "hash_x"
        assert conflict.fact_b_hash == "hash_y"
        assert conflict.conflict_type == ConflictType.SCOPE_CONFLICT
        assert conflict.conflict_status == ConflictStatus.AGENT_RESOLVED
        assert conflict.detected_at == now
        assert conflict.resolution_fact_hash == "hash_y"
        assert conflict.resolution_reason == "Broader scope"
        assert conflict.resolved_at == now


class TestQueryResult:
    """Test QueryResult data class."""

    def test_query_result_creation(self):
        """Test creating a QueryResult."""
        now = datetime.now()
        fact = Fact(
            content="test",
            content_type=ContentType.PLAIN_TEXT,
            entity="user",
            attribute="name",
            value="Alice",
            source="test",
            observed_at=now,
            confidence=1.0,
        )

        result = QueryResult(
            facts=[("hash123", fact)],
            query_time=0.05,
            branch="main",
            total_found=1,
        )

        assert len(result.facts) == 1
        assert result.facts[0][0] == "hash123"
        assert result.facts[0][1] == fact
        assert result.query_time == 0.05
        assert result.branch == "main"
        assert result.total_found == 1

    def test_query_result_empty(self):
        """Test creating an empty QueryResult."""
        result = QueryResult(
            facts=[],
            query_time=0.01,
            branch="main",
            total_found=0,
        )

        assert result.facts == []
        assert result.total_found == 0


class TestContextBlock:
    """Test ContextBlock data class."""

    def test_context_block_creation(self):
        """Test creating a ContextBlock."""
        now = datetime.now()
        block = ContextBlock(
            formatted_text="Memory context:\n- User name: Alice",
            fact_count=1,
            has_conflicts=False,
            assembled_at=now,
        )

        assert block.formatted_text == "Memory context:\n- User name: Alice"
        assert block.fact_count == 1
        assert block.has_conflicts is False
        assert block.assembled_at == now

    def test_context_block_with_conflicts(self):
        """Test creating a ContextBlock with conflicts."""
        now = datetime.now()
        block = ContextBlock(
            formatted_text="Memory context with conflicts",
            fact_count=5,
            has_conflicts=True,
            assembled_at=now,
        )

        assert block.has_conflicts is True
        assert block.fact_count == 5
