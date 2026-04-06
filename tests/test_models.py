"""Model tests for Memora v3.1.

Tests Memory and Session dataclasses for correct serialization/deserialization.
"""

import pytest
from datetime import datetime
from memora.shared.models import Memory, Session, MemoryType, MemorySource, MemoryCommit, MemoryTree


class TestMemoryModel:
    """Test Memory dataclass serialization and validation."""

    def test_memory_creation(self):
        """Test creating a Memory instance."""
        memory = Memory(
            id="mem_abc123",
            content="User prefers Python",
            memory_type=MemoryType.CONVERSATION,
            confidence=0.95,
            source=MemorySource.OLLAMA_CHAT,
            session_id="sess_test",
            branch="main",
            turn_index=0,
            created_at="2026-04-05T10:00:00Z",
            updated_at="2026-04-05T10:00:00Z",
        )

        assert memory.id == "mem_abc123"
        assert memory.content == "User prefers Python"
        assert memory.memory_type == MemoryType.CONVERSATION
        assert memory.confidence == 0.95
        assert memory.source == MemorySource.OLLAMA_CHAT
        assert memory.session_id == "sess_test"
        assert memory.branch == "main"
        assert memory.turn_index == 0

    def test_memory_to_dict(self):
        """Test Memory serialization to dict."""
        memory = Memory(
            id="mem_xyz",
            content="User lives in Seattle",
            memory_type=MemoryType.CONVERSATION,
            confidence=0.92,
            source=MemorySource.OLLAMA_CHAT,
            session_id="sess_test",
            branch="main",
            turn_index=1,
            created_at="2026-04-05T10:00:00Z",
            updated_at="2026-04-05T10:00:00Z",
        )

        data = memory.to_dict()
        assert isinstance(data, dict)
        assert data["id"] == "mem_xyz"
        assert data["content"] == "User lives in Seattle"
        assert data["memory_type"] == "conversation"
        assert data["source"] == "ollama_chat"
        assert data["session_id"] == "sess_test"
        assert data["branch"] == "main"
        assert data["turn_index"] == 1
        assert data["confidence"] == 0.92

    def test_memory_from_dict(self):
        """Test Memory deserialization from dict."""
        data = {
            "id": "mem_fromdict",
            "content": "Test memory from dict",
            "memory_type": "conversation",
            "confidence": 0.88,
            "source": "manual",
            "session_id": "sess_dict",
            "branch": "test",
            "turn_index": 2,
            "created_at": "2026-04-05T11:00:00Z",
            "updated_at": "2026-04-05T11:00:00Z",
            "entities": ["test"],
            "metadata": {"test": True},
            "supersedes": None,
            "pinned": False,
            "hidden": False,
        }

        memory = Memory.from_dict(data)
        assert memory.id == "mem_fromdict"
        assert memory.content == "Test memory from dict"
        assert memory.memory_type == MemoryType.CONVERSATION
        assert memory.source == MemorySource.MANUAL
        assert memory.session_id == "sess_dict"
        assert memory.branch == "test"
        assert memory.turn_index == 2

    def test_memory_roundtrip(self):
        """Test Memory serialization roundtrip (to_dict -> from_dict)."""
        original = Memory(
            id="mem_roundtrip",
            content="Roundtrip test memory",
            memory_type=MemoryType.CODE,
            confidence=0.97,
            source=MemorySource.FILE_INGESTION,
            session_id="sess_roundtrip",
            branch="dev",
            turn_index=5,
            created_at="2026-04-05T12:00:00Z",
            updated_at="2026-04-05T12:00:00Z",
            entities=["python", "test"],
            metadata={"language": "python"},
        )

        # Serialize and deserialize
        data = original.to_dict()
        deserialized = Memory.from_dict(data)

        # Verify all fields match
        assert deserialized.id == original.id
        assert deserialized.content == original.content
        assert deserialized.memory_type == original.memory_type
        assert deserialized.confidence == original.confidence
        assert deserialized.source == original.source
        assert deserialized.session_id == original.session_id
        assert deserialized.branch == original.branch
        assert deserialized.turn_index == original.turn_index
        assert deserialized.entities == original.entities
        assert deserialized.metadata == original.metadata


class TestSessionModel:
    """Test Session dataclass serialization and validation."""

    def test_session_creation(self):
        """Test creating a Session instance."""
        session = Session(
            id="sess_abc",
            branch="main",
            started_at="2026-04-05T10:00:00Z",
            ended_at=None,
            memory_ids=["mem_1", "mem_2"],
            ollama_model="llama3.2:3b",
        )

        assert session.id == "sess_abc"
        assert session.branch == "main"
        assert len(session.memory_ids) == 2
        assert session.ollama_model == "llama3.2:3b"

    def test_session_to_dict(self):
        """Test Session serialization to dict."""
        session = Session(
            id="sess_xyz",
            branch="main",
            started_at="2026-04-05T10:00:00Z",
            ended_at="2026-04-05T11:00:00Z",
            memory_ids=["mem_a", "mem_b", "mem_c"],
            ollama_model="mistral:latest",
        )

        data = session.to_dict()
        assert isinstance(data, dict)
        assert data["id"] == "sess_xyz"
        assert data["branch"] == "main"
        assert len(data["memory_ids"]) == 3
        assert data["ollama_model"] == "mistral:latest"

    def test_session_from_dict(self):
        """Test Session deserialization from dict."""
        data = {
            "id": "sess_test",
            "branch": "feature",
            "started_at": "2026-04-05T10:00:00Z",
            "ended_at": None,
            "memory_ids": ["mem_1"],
            "ollama_model": "llama3.2:3b",
        }

        session = Session.from_dict(data)
        assert isinstance(session, Session)
        assert session.id == "sess_test"
        assert session.branch == "feature"
        assert len(session.memory_ids) == 1

    def test_session_roundtrip(self):
        """Test that Session survives serialization roundtrip."""
        original = Session(
            id="sess_roundtrip",
            branch="main",
            started_at="2026-04-05T10:00:00Z",
            ended_at="2026-04-05T11:00:00Z",
            memory_ids=["mem_1", "mem_2", "mem_3"],
            ollama_model="llama3.2:3b",
        )

        # Serialize and deserialize
        data = original.to_dict()
        recovered = Session.from_dict(data)

        assert recovered.id == original.id
        assert recovered.branch == original.branch
        assert recovered.memory_ids == original.memory_ids
        assert recovered.ollama_model == original.ollama_model


class TestMemoryCommitModel:
    """Test MemoryCommit dataclass serialization."""

    def test_commit_creation(self):
        """Test creating a MemoryCommit instance."""
        commit = MemoryCommit(
            root_tree_hash="tree_abc123",
            parent_hash="commit_parent",
            author="system",
            message="Session: 3 memories captured",
            committed_at="2026-04-05T10:00:00Z",
        )

        assert commit.root_tree_hash == "tree_abc123"
        assert commit.parent_hash == "commit_parent"
        assert commit.author == "system"
        assert commit.message == "Session: 3 memories captured"

    def test_commit_to_dict(self):
        """Test MemoryCommit serialization to dict."""
        commit = MemoryCommit(
            root_tree_hash="tree_xyz456",
            parent_hash=None,
            author="user",
            message="Initial commit",
            committed_at="2026-04-05T10:00:00Z",
        )

        data = commit.to_dict()
        assert isinstance(data, dict)
        assert data["root_tree_hash"] == "tree_xyz456"
        assert data["parent_hash"] is None
        assert data["author"] == "user"
        assert data["message"] == "Initial commit"

    def test_commit_roundtrip(self):
        """Test that MemoryCommit survives serialization roundtrip."""
        original = MemoryCommit(
            root_tree_hash="tree_roundtrip",
            parent_hash="parent_commit",
            author="test_user",
            message="Test commit for roundtrip",
            committed_at="2026-04-05T10:00:00Z",
        )

        # Serialize and deserialize
        data = original.to_dict()
        recovered = MemoryCommit.from_dict(data)

        assert recovered.root_tree_hash == original.root_tree_hash
        assert recovered.parent_hash == original.parent_hash
        assert recovered.author == original.author
        assert recovered.message == original.message
        assert recovered.committed_at == original.committed_at


class TestMemoryTypeEnum:
    """Test MemoryType enum values."""

    def test_memory_types_exist(self):
        """Test that all expected memory types exist."""
        assert MemoryType.CONVERSATION
        assert MemoryType.CODE
        assert MemoryType.DOCUMENT
        assert MemoryType.FILE

    def test_memory_type_values(self):
        """Test that memory type values are correct strings."""
        assert MemoryType.CONVERSATION.value == "conversation"
        assert MemoryType.CODE.value == "code"
        assert MemoryType.DOCUMENT.value == "document"
        assert MemoryType.FILE.value == "file"
