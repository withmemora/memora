"""Core data models for Memora v3.0.

This module defines the new data model: Memory objects (not Fact triples),
Session lifecycle tracking, and supporting enums.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class MemoryType(Enum):
    """Type of memory content."""

    CONVERSATION = "conversation"
    CODE = "code"
    DOCUMENT = "document"
    FILE = "file"


class MemorySource(Enum):
    """Where a memory came from."""

    OLLAMA_CHAT = "ollama_chat"
    FILE_INGESTION = "file_ingestion"
    MANUAL = "manual"


class ConflictType(Enum):
    """Classification of conflict between memories."""

    TEMPORAL_SUPERSESSION = "temporal_supersession"
    SOURCE_CONFLICT = "source_conflict"
    DIRECT_CONTRADICTION = "direct_contradiction"
    UNCERTAIN = "uncertain"


class ConflictStatus(Enum):
    """Resolution status of a conflict."""

    UNRESOLVED = "unresolved"
    AUTO_RESOLVED = "auto_resolved"
    USER_RESOLVED = "user_resolved"


@dataclass
class Memory:
    """A single piece of human-readable memory.

    Unlike the old Fact model (entity-attribute-value triples),
    Memory.content is ALWAYS a human-readable string.
    """

    id: str
    content: str
    memory_type: MemoryType
    confidence: float
    source: MemorySource
    session_id: str
    branch: str
    turn_index: int
    created_at: str
    updated_at: str
    supersedes: str | None = None
    entities: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @staticmethod
    def generate_id() -> str:
        return f"mem_{uuid.uuid4().hex[:12]}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "confidence": self.confidence,
            "source": self.source.value,
            "session_id": self.session_id,
            "branch": self.branch,
            "turn_index": self.turn_index,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "supersedes": self.supersedes,
            "entities": self.entities,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Memory:
        return cls(
            id=d["id"],
            content=d["content"],
            memory_type=MemoryType(d["memory_type"]),
            confidence=d["confidence"],
            source=MemorySource(d["source"]),
            session_id=d["session_id"],
            branch=d["branch"],
            turn_index=d["turn_index"],
            created_at=d["created_at"],
            updated_at=d["updated_at"],
            supersedes=d.get("supersedes"),
            entities=d.get("entities", []),
            metadata=d.get("metadata", {}),
        )

    def compute_hash(self) -> str:
        hash_input = f"{self.content.lower()}{self.memory_type.value}{self.session_id}"
        return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()


@dataclass
class Session:
    """A single Ollama chat session."""

    id: str
    branch: str
    started_at: str
    ended_at: str | None = None
    ollama_model: str = ""
    memory_ids: list[str] = field(default_factory=list)
    commit_hash: str | None = None
    auto_commit_message: str | None = None
    files_ingested: list[str] = field(default_factory=list)

    @staticmethod
    def generate_id() -> str:
        return f"sess_{uuid.uuid4().hex[:12]}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "branch": self.branch,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "ollama_model": self.ollama_model,
            "memory_ids": self.memory_ids,
            "commit_hash": self.commit_hash,
            "auto_commit_message": self.auto_commit_message,
            "files_ingested": self.files_ingested,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Session:
        return cls(
            id=d["id"],
            branch=d["branch"],
            started_at=d["started_at"],
            ended_at=d.get("ended_at"),
            ollama_model=d.get("ollama_model", ""),
            memory_ids=d.get("memory_ids", []),
            commit_hash=d.get("commit_hash"),
            auto_commit_message=d.get("auto_commit_message"),
            files_ingested=d.get("files_ingested", []),
        )


@dataclass
class MemoryCommit:
    """A commit representing a snapshot of memory state."""

    root_tree_hash: str
    parent_hash: str | None
    author: str
    message: str
    committed_at: str

    def to_dict(self) -> dict:
        return {
            "root_tree_hash": self.root_tree_hash,
            "parent_hash": self.parent_hash,
            "author": self.author,
            "message": self.message,
            "committed_at": self.committed_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> MemoryCommit:
        return cls(
            root_tree_hash=d["root_tree_hash"],
            parent_hash=d.get("parent_hash"),
            author=d["author"],
            message=d["message"],
            committed_at=d["committed_at"],
        )


@dataclass
class MemoryTree:
    """Collection of memory references, similar to Git trees."""

    memory_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"memory_ids": self.memory_ids}

    @classmethod
    def from_dict(cls, d: dict) -> MemoryTree:
        return cls(memory_ids=d.get("memory_ids", []))


@dataclass
class Conflict:
    """Detected conflict between two memories."""

    conflict_id: str
    memory_a_id: str
    memory_b_id: str
    conflict_type: ConflictType
    conflict_status: ConflictStatus
    detected_at: str
    resolution_memory_id: str | None = None
    resolution_reason: str | None = None
    resolved_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "conflict_id": self.conflict_id,
            "memory_a_id": self.memory_a_id,
            "memory_b_id": self.memory_b_id,
            "conflict_type": self.conflict_type.value,
            "conflict_status": self.conflict_status.value,
            "detected_at": self.detected_at,
            "resolution_memory_id": self.resolution_memory_id,
            "resolution_reason": self.resolution_reason,
            "resolved_at": self.resolved_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Conflict:
        return cls(
            conflict_id=d["conflict_id"],
            memory_a_id=d["memory_a_id"],
            memory_b_id=d["memory_b_id"],
            conflict_type=ConflictType(d["conflict_type"]),
            conflict_status=ConflictStatus(d["conflict_status"]),
            detected_at=d["detected_at"],
            resolution_memory_id=d.get("resolution_memory_id"),
            resolution_reason=d.get("resolution_reason"),
            resolved_at=d.get("resolved_at"),
        )


@dataclass
class GraphNode:
    """A node in the knowledge graph."""

    id: str
    name: str
    type: str
    first_seen: str
    last_seen: str
    memory_count: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "memory_count": self.memory_count,
        }

    @classmethod
    def from_dict(cls, d: dict) -> GraphNode:
        return cls(
            id=d["id"],
            name=d["name"],
            type=d["type"],
            first_seen=d["first_seen"],
            last_seen=d["last_seen"],
            memory_count=d.get("memory_count", 0),
        )


@dataclass
class GraphEdge:
    """An edge in the knowledge graph."""

    id: str
    source: str
    relation: str
    target: str
    confidence: float
    created_at: str
    superseded_at: str | None = None
    memory_id: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "relation": self.relation,
            "target": self.target,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "superseded_at": self.superseded_at,
            "memory_id": self.memory_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> GraphEdge:
        return cls(
            id=d["id"],
            source=d["source"],
            relation=d["relation"],
            target=d["target"],
            confidence=d["confidence"],
            created_at=d["created_at"],
            superseded_at=d.get("superseded_at"),
            memory_id=d.get("memory_id", ""),
        )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
