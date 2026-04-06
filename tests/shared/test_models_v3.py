"""Tests for shared/models.py v3.0 data structures.

This module tests the new v3.0 data model:
- Memory (not Fact triples)
- Session lifecycle
- GraphNode and GraphEdge
- Supporting enums
"""

from datetime import datetime, timezone

import pytest

from memora.shared.models import (
    Conflict,
    ConflictStatus,
    ConflictType,
    GraphEdge,
    GraphNode,
    Memory,
    MemoryCommit,
    MemorySource,
    MemoryTree,
    MemoryType,
    Session,
    now_iso,
)


class TestMemoryType:
    """Test MemoryType enum."""

    def test_memory_type_values(self):
        """Test that MemoryType enum has expected values."""
        assert MemoryType.CONVERSATION.value == "conversation"
        assert MemoryType.CODE.value == "code"
        assert MemoryType.DOCUMENT.value == "document"
        assert MemoryType.FILE.value == "file"


class TestMemorySource:
    """Test MemorySource enum."""

    def test_memory_source_values(self):
        """Test that MemorySource enum has expected values."""
        assert MemorySource.OLLAMA_CHAT.value == "ollama_chat"
        assert MemorySource.FILE_INGESTION.value == "file_ingestion"
        assert MemorySource.MANUAL.value == "manual"


class TestConflictType:
    """Test ConflictType enum."""

    def test_conflict_type_values(self):
        """Test that ConflictType enum has expected values."""
        assert ConflictType.DIRECT_CONTRADICTION.value == "direct_contradiction"
        assert ConflictType.TEMPORAL_SUPERSESSION.value == "temporal_supersession"
        assert ConflictType.SOURCE_CONFLICT.value == "source_conflict"
        assert ConflictType.UNCERTAIN.value == "uncertain"


class TestConflictStatus:
    """Test ConflictStatus enum."""

    def test_conflict_status_values(self):
        """Test that ConflictStatus enum has expected values."""
        assert ConflictStatus.UNRESOLVED.value == "unresolved"
        assert ConflictStatus.AUTO_RESOLVED.value == "auto_resolved"
        assert ConflictStatus.USER_RESOLVED.value == "user_resolved"


class TestMemory:
    """Test Memory dataclass - the core v3.0 data model."""

    def test_memory_creation(self):
        """Test creating a Memory object."""
        memory = Memory(
            id="mem_abc123",
            content="User's name is Sarah",
            memory_type=MemoryType.CONVERSATION,
            confidence=0.95,
            source=MemorySource.OLLAMA_CHAT,
            session_id="sess_xyz",
            branch="main",
            turn_index=1,
            created_at="2026-04-05T10:00:00Z",
            updated_at="2026-04-05T10:00:00Z",
        )

        assert memory.id == "mem_abc123"
        assert memory.content == "User's name is Sarah"
        assert memory.memory_type == MemoryType.CONVERSATION
        assert memory.confidence == 0.95
        assert memory.source == MemorySource.OLLAMA_CHAT
        assert memory.session_id == "sess_xyz"
        assert memory.branch == "main"
        assert memory.turn_index == 1
        assert memory.supersedes is None
        assert memory.entities == []
        assert memory.metadata == {}

    def test_memory_with_entities(self):
        """Test Memory with entities list."""
        memory = Memory(
            id="mem_def456",
            content="User works at Microsoft in Seattle",
            memory_type=MemoryType.CONVERSATION,
            confidence=0.92,
            source=MemorySource.OLLAMA_CHAT,
            session_id="sess_xyz",
            branch="main",
            turn_index=2,
            created_at="2026-04-05T10:01:00Z",
            updated_at="2026-04-05T10:01:00Z",
            entities=["microsoft", "seattle"],
        )

        assert memory.entities == ["microsoft", "seattle"]

    def test_memory_with_metadata(self):
        """Test Memory with type-specific metadata."""
        memory = Memory(
            id="mem_ghi789",
            content="Python function for PDF processing",
            memory_type=MemoryType.CODE,
            confidence=0.90,
            source=MemorySource.OLLAMA_CHAT,
            session_id="sess_xyz",
            branch="main",
            turn_index=3,
            created_at="2026-04-05T10:02:00Z",
            updated_at="2026-04-05T10:02:00Z",
            metadata={
                "language": "python",
                "function_names": ["process_pdf"],
                "raw_code": "def process_pdf(path):\n    pass",
            },
        )

        assert memory.metadata["language"] == "python"
        assert "process_pdf" in memory.metadata["function_names"]

    def test_memory_generate_id(self):
        """Test Memory.generate_id() creates valid IDs."""
        id1 = Memory.generate_id()
        id2 = Memory.generate_id()

        assert id1.startswith("mem_")
        assert id2.startswith("mem_")
        assert id1 != id2
        assert len(id1) == 16  # "mem_" + 12 hex chars

    def test_memory_to_dict(self):
        """Test Memory.to_dict() serialization."""
        memory = Memory(
            id="mem_abc123",
            content="User's name is Sarah",
            memory_type=MemoryType.CONVERSATION,
            confidence=0.95,
            source=MemorySource.OLLAMA_CHAT,
            session_id="sess_xyz",
            branch="main",
            turn_index=1,
            created_at="2026-04-05T10:00:00Z",
            updated_at="2026-04-05T10:00:00Z",
            entities=["sarah"],
        )

        d = memory.to_dict()

        assert d["id"] == "mem_abc123"
        assert d["content"] == "User's name is Sarah"
        assert d["memory_type"] == "conversation"
        assert d["confidence"] == 0.95
        assert d["source"] == "ollama_chat"
        assert d["session_id"] == "sess_xyz"
        assert d["branch"] == "main"
        assert d["turn_index"] == 1
        assert d["entities"] == ["sarah"]

    def test_memory_from_dict(self):
        """Test Memory.from_dict() deserialization."""
        d = {
            "id": "mem_abc123",
            "content": "User's name is Sarah",
            "memory_type": "conversation",
            "confidence": 0.95,
            "source": "ollama_chat",
            "session_id": "sess_xyz",
            "branch": "main",
            "turn_index": 1,
            "created_at": "2026-04-05T10:00:00Z",
            "updated_at": "2026-04-05T10:00:00Z",
            "supersedes": None,
            "entities": ["sarah"],
            "metadata": {},
        }

        memory = Memory.from_dict(d)

        assert memory.id == "mem_abc123"
        assert memory.content == "User's name is Sarah"
        assert memory.memory_type == MemoryType.CONVERSATION
        assert memory.confidence == 0.95
        assert memory.source == MemorySource.OLLAMA_CHAT
        assert memory.entities == ["sarah"]

    def test_memory_compute_hash(self):
        """Test Memory.compute_hash() generates consistent hashes."""
        memory = Memory(
            id="mem_abc123",
            content="User's name is Sarah",
            memory_type=MemoryType.CONVERSATION,
            confidence=0.95,
            source=MemorySource.OLLAMA_CHAT,
            session_id="sess_xyz",
            branch="main",
            turn_index=1,
            created_at="2026-04-05T10:00:00Z",
            updated_at="2026-04-05T10:00:00Z",
        )

        hash1 = memory.compute_hash()
        hash2 = memory.compute_hash()

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex

    def test_memory_content_is_human_readable(self):
        """Test that Memory.content is always a human-readable string (not triples)."""
        memory = Memory(
            id="mem_test",
            content="User prefers Python over JavaScript",
            memory_type=MemoryType.CONVERSATION,
            confidence=0.90,
            source=MemorySource.OLLAMA_CHAT,
            session_id="sess_test",
            branch="main",
            turn_index=0,
            created_at=now_iso(),
            updated_at=now_iso(),
        )

        # Content should be a plain English sentence
        assert isinstance(memory.content, str)
        assert "User prefers Python" in memory.content
        # NOT entity-attribute-value format like "user.preference = Python"
        assert "=" not in memory.content


class TestSession:
    """Test Session dataclass."""

    def test_session_creation(self):
        """Test creating a Session object."""
        session = Session(
            id="sess_abc123",
            branch="main",
            started_at="2026-04-05T10:00:00Z",
            ollama_model="llama3.2:3b",
        )

        assert session.id == "sess_abc123"
        assert session.branch == "main"
        assert session.started_at == "2026-04-05T10:00:00Z"
        assert session.ended_at is None
        assert session.ollama_model == "llama3.2:3b"
        assert session.memory_ids == []
        assert session.commit_hash is None

    def test_session_generate_id(self):
        """Test Session.generate_id() creates valid IDs."""
        id1 = Session.generate_id()
        id2 = Session.generate_id()

        assert id1.startswith("sess_")
        assert id2.startswith("sess_")
        assert id1 != id2
        assert len(id1) == 17  # "sess_" + 12 hex chars

    def test_session_to_dict(self):
        """Test Session.to_dict() serialization."""
        session = Session(
            id="sess_abc123",
            branch="main",
            started_at="2026-04-05T10:00:00Z",
            ended_at="2026-04-05T10:30:00Z",
            ollama_model="llama3.2:3b",
            memory_ids=["mem_1", "mem_2", "mem_3"],
            commit_hash="abc123def456",
            auto_commit_message="Session: 3 memories captured",
            files_ingested=["architecture.md"],
        )

        d = session.to_dict()

        assert d["id"] == "sess_abc123"
        assert d["branch"] == "main"
        assert d["memory_ids"] == ["mem_1", "mem_2", "mem_3"]
        assert d["commit_hash"] == "abc123def456"
        assert d["files_ingested"] == ["architecture.md"]

    def test_session_from_dict(self):
        """Test Session.from_dict() deserialization."""
        d = {
            "id": "sess_abc123",
            "branch": "main",
            "started_at": "2026-04-05T10:00:00Z",
            "ended_at": "2026-04-05T10:30:00Z",
            "ollama_model": "llama3.2:3b",
            "memory_ids": ["mem_1", "mem_2"],
            "commit_hash": "abc123",
            "auto_commit_message": "Session: 2 memories",
            "files_ingested": [],
        }

        session = Session.from_dict(d)

        assert session.id == "sess_abc123"
        assert session.branch == "main"
        assert session.memory_ids == ["mem_1", "mem_2"]
        assert session.commit_hash == "abc123"


class TestGraphNode:
    """Test GraphNode dataclass."""

    def test_graph_node_creation(self):
        """Test creating a GraphNode."""
        node = GraphNode(
            id="microsoft",
            name="Microsoft",
            type="organization",
            first_seen="2026-04-05T10:00:00Z",
            last_seen="2026-04-05T11:00:00Z",
            memory_count=5,
        )

        assert node.id == "microsoft"
        assert node.name == "Microsoft"
        assert node.type == "organization"
        assert node.memory_count == 5

    def test_graph_node_to_dict(self):
        """Test GraphNode.to_dict() serialization."""
        node = GraphNode(
            id="sarah",
            name="Sarah",
            type="person",
            first_seen="2026-04-05T10:00:00Z",
            last_seen="2026-04-05T10:00:00Z",
            memory_count=1,
        )

        d = node.to_dict()

        assert d["id"] == "sarah"
        assert d["name"] == "Sarah"
        assert d["type"] == "person"

    def test_graph_node_from_dict(self):
        """Test GraphNode.from_dict() deserialization."""
        d = {
            "id": "python",
            "name": "Python",
            "type": "technology",
            "first_seen": "2026-04-05T10:00:00Z",
            "last_seen": "2026-04-05T10:00:00Z",
            "memory_count": 3,
        }

        node = GraphNode.from_dict(d)

        assert node.id == "python"
        assert node.name == "Python"
        assert node.type == "technology"


class TestGraphEdge:
    """Test GraphEdge dataclass."""

    def test_graph_edge_creation(self):
        """Test creating a GraphEdge."""
        edge = GraphEdge(
            id="edge_abc123",
            source="user",
            relation="works_at",
            target="microsoft",
            confidence=0.95,
            created_at="2026-04-05T10:00:00Z",
            memory_id="mem_xyz",
        )

        assert edge.id == "edge_abc123"
        assert edge.source == "user"
        assert edge.relation == "works_at"
        assert edge.target == "microsoft"
        assert edge.confidence == 0.95
        assert edge.superseded_at is None

    def test_graph_edge_to_dict(self):
        """Test GraphEdge.to_dict() serialization."""
        edge = GraphEdge(
            id="edge_abc123",
            source="user",
            relation="knows",
            target="sarah",
            confidence=0.90,
            created_at="2026-04-05T10:00:00Z",
            memory_id="mem_xyz",
        )

        d = edge.to_dict()

        assert d["id"] == "edge_abc123"
        assert d["source"] == "user"
        assert d["relation"] == "knows"
        assert d["target"] == "sarah"

    def test_graph_edge_from_dict(self):
        """Test GraphEdge.from_dict() deserialization."""
        d = {
            "id": "edge_def456",
            "source": "user",
            "relation": "uses",
            "target": "python",
            "confidence": 0.92,
            "created_at": "2026-04-05T10:00:00Z",
            "superseded_at": None,
            "memory_id": "mem_abc",
        }

        edge = GraphEdge.from_dict(d)

        assert edge.id == "edge_def456"
        assert edge.relation == "uses"
        assert edge.superseded_at is None


class TestConflict:
    """Test Conflict dataclass."""

    def test_conflict_creation(self):
        """Test creating a Conflict object."""
        conflict = Conflict(
            conflict_id="conflict_abc123",
            memory_a_id="mem_old",
            memory_b_id="mem_new",
            conflict_type=ConflictType.TEMPORAL_SUPERSESSION,
            conflict_status=ConflictStatus.AUTO_RESOLVED,
            detected_at="2026-04-05T10:00:00Z",
        )

        assert conflict.conflict_id == "conflict_abc123"
        assert conflict.memory_a_id == "mem_old"
        assert conflict.memory_b_id == "mem_new"
        assert conflict.conflict_type == ConflictType.TEMPORAL_SUPERSESSION
        assert conflict.conflict_status == ConflictStatus.AUTO_RESOLVED


class TestMemoryTree:
    """Test MemoryTree dataclass."""

    def test_memory_tree_creation(self):
        """Test creating a MemoryTree."""
        tree = MemoryTree(memory_ids=["mem_1", "mem_2", "mem_3"])

        assert tree.memory_ids == ["mem_1", "mem_2", "mem_3"]

    def test_memory_tree_to_dict(self):
        """Test MemoryTree.to_dict() serialization."""
        tree = MemoryTree(memory_ids=["mem_1", "mem_2"])

        d = tree.to_dict()

        assert d["memory_ids"] == ["mem_1", "mem_2"]

    def test_memory_tree_from_dict(self):
        """Test MemoryTree.from_dict() deserialization."""
        d = {"memory_ids": ["mem_1", "mem_2", "mem_3"]}

        tree = MemoryTree.from_dict(d)

        assert tree.memory_ids == ["mem_1", "mem_2", "mem_3"]


class TestMemoryCommit:
    """Test MemoryCommit dataclass."""

    def test_memory_commit_creation(self):
        """Test creating a MemoryCommit."""
        commit = MemoryCommit(
            root_tree_hash="tree_abc123",
            parent_hash="commit_def456",
            author="system",
            message="Session: 3 memories captured",
            committed_at="2026-04-05T10:00:00Z",
        )

        assert commit.root_tree_hash == "tree_abc123"
        assert commit.parent_hash == "commit_def456"
        assert commit.author == "system"
        assert commit.message == "Session: 3 memories captured"

    def test_memory_commit_to_dict(self):
        """Test MemoryCommit.to_dict() serialization."""
        commit = MemoryCommit(
            root_tree_hash="tree_abc",
            parent_hash=None,
            author="system",
            message="Initial commit",
            committed_at="2026-04-05T10:00:00Z",
        )

        d = commit.to_dict()

        assert d["root_tree_hash"] == "tree_abc"
        assert d["parent_hash"] is None
        assert d["author"] == "system"

    def test_memory_commit_from_dict(self):
        """Test MemoryCommit.from_dict() deserialization."""
        d = {
            "root_tree_hash": "tree_xyz",
            "parent_hash": "commit_abc",
            "author": "system",
            "message": "Session: 2 memories",
            "committed_at": "2026-04-05T10:00:00Z",
        }

        commit = MemoryCommit.from_dict(d)

        assert commit.root_tree_hash == "tree_xyz"
        assert commit.parent_hash == "commit_abc"


class TestNowIso:
    """Test now_iso() utility function."""

    def test_now_iso_returns_valid_timestamp(self):
        """Test that now_iso() returns a valid ISO timestamp."""
        timestamp = now_iso()

        assert isinstance(timestamp, str)
        assert "T" in timestamp
        assert "Z" in timestamp or "+" in timestamp

        # Should be parseable
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
