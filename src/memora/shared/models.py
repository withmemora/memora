"""Core data models for Memora.

This module defines all data structures used throughout the Memora system.
These models form the contract between the core, interface, and shared layers.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ContentType(Enum):
    """Type of content extracted from conversation."""

    PLAIN_TEXT = "plain_text"
    TRIPLE = "triple"
    DATE_VALUE = "date_value"
    PREFERENCE = "preference"
    CODE_SNIPPET = "code_snippet"  # Code shared in conversations
    FILE_CONTENT = "file_content"  # Content from ingested files


class ConflictType(Enum):
    """Classification of conflict between facts."""

    DIRECT_CONTRADICTION = "direct_contradiction"
    TEMPORAL_SUPERSESSION = "temporal_supersession"
    SOURCE_CONFLICT = "source_conflict"
    SCOPE_CONFLICT = "scope_conflict"
    UNCERTAIN = "uncertain"


class ConflictStatus(Enum):
    """Resolution status of a conflict."""

    UNRESOLVED = "unresolved"
    AUTO_RESOLVED = "auto_resolved"
    USER_RESOLVED = "user_resolved"
    AGENT_RESOLVED = "agent_resolved"


@dataclass
class Fact:
    """A single extracted piece of information from conversation.

    Facts are the atomic unit of memory in Memora. Each fact represents
    a single piece of information with provenance, confidence, and temporal data.

    The hash is computed from ONLY: content_type + entity.lower() + attribute.lower() + value
    This means facts with identical semantic content but different sources, timestamps,
    or confidence scores will deduplicate to the same hash.
    """

    content: str  # Raw source sentence this was extracted from
    content_type: ContentType
    entity: str  # Lowercase normalized entity name
    attribute: str  # Lowercase normalized attribute name
    value: str  # The actual value
    source: str  # Provenance (e.g., "conversation:session-001")
    observed_at: datetime  # UTC timestamp
    confidence: float  # 0.0 to 1.0

    def compute_hash(self) -> str:
        """Compute SHA-256 hash from content_type, entity, attribute, and value only.

        Source, observed_at, and confidence are EXCLUDED from hash computation.
        This allows deduplication of semantically identical facts from different sources.

        Returns:
            64-character hex string (SHA-256 hash)
        """
        # Normalize and concatenate the fields that define semantic identity
        hash_input = (
            f"{self.content_type.value}{self.entity.lower()}{self.attribute.lower()}{self.value}"
        )
        return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        """Convert Fact to dictionary for serialization.

        Returns:
            Dictionary with all fields, datetime as ISO 8601 string
        """
        return {
            "content": self.content,
            "content_type": self.content_type.value,
            "entity": self.entity,
            "attribute": self.attribute,
            "value": self.value,
            "source": self.source,
            "observed_at": self.observed_at.isoformat(),
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Fact:
        """Construct Fact from dictionary.

        Args:
            d: Dictionary with fact data

        Returns:
            Fact instance
        """
        return cls(
            content=d["content"],
            content_type=ContentType(d["content_type"]),
            entity=d["entity"],
            attribute=d["attribute"],
            value=d["value"],
            source=d["source"],
            observed_at=datetime.fromisoformat(d["observed_at"]),
            confidence=d["confidence"],
        )


@dataclass
class MemoryTreeEntry:
    """Single entry in a memory tree (either a fact or subtree reference).

    Memory trees organize facts hierarchically, similar to Git trees.
    Each entry points to either a fact object or another tree object.
    """

    name: str  # Entry name (e.g., "user", "project")
    entry_type: str  # "fact" or "subtree"
    hash: str  # SHA-256 hash of the referenced object

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "entry_type": self.entry_type,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, d: dict) -> MemoryTreeEntry:
        """Construct from dictionary."""
        return cls(
            name=d["name"],
            entry_type=d["entry_type"],
            hash=d["hash"],
        )


@dataclass
class MemoryTree:
    """Hierarchical tree structure organizing facts, similar to Git trees.

    Trees allow organizing facts into a hierarchy (e.g., user/name, project/deadline).
    Each tree contains entries that point to either facts or other trees.
    """

    entries: list[MemoryTreeEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "entries": [entry.to_dict() for entry in self.entries],
        }

    @classmethod
    def from_dict(cls, d: dict) -> MemoryTree:
        """Construct from dictionary."""
        return cls(
            entries=[MemoryTreeEntry.from_dict(e) for e in d["entries"]],
        )


@dataclass
class MemoryCommit:
    """A commit representing a snapshot of memory state, similar to Git commits.

    Commits create an immutable, versioned history of memory states.
    Each commit points to a root tree and optionally to a parent commit.
    """

    root_tree_hash: str  # SHA-256 hash of root tree
    parent_hash: str | None  # SHA-256 of parent commit, None for first commit
    author: str  # Author identifier
    message: str  # Commit message describing changes
    committed_at: datetime  # UTC timestamp

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "root_tree_hash": self.root_tree_hash,
            "parent_hash": self.parent_hash,
            "author": self.author,
            "message": self.message,
            "committed_at": self.committed_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> MemoryCommit:
        """Construct from dictionary."""
        return cls(
            root_tree_hash=d["root_tree_hash"],
            parent_hash=d["parent_hash"],
            author=d["author"],
            message=d["message"],
            committed_at=datetime.fromisoformat(d["committed_at"]),
        )


@dataclass
class Conflict:
    """Detected conflict between two facts.

    Conflicts represent contradictions or inconsistencies between facts.
    They track the conflicting facts, classification, and resolution state.
    """

    conflict_id: str  # SHA-256 of (fact_a_hash + fact_b_hash + detected_at)
    fact_a_hash: str  # SHA-256 of first fact
    fact_b_hash: str  # SHA-256 of second fact
    conflict_type: ConflictType  # Classification of conflict
    conflict_status: ConflictStatus  # Resolution status
    detected_at: datetime  # UTC timestamp of detection
    resolution_fact_hash: str | None  # Hash of fact chosen as resolution
    resolution_reason: str | None  # Explanation of resolution
    resolved_at: datetime | None  # UTC timestamp of resolution

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "conflict_id": self.conflict_id,
            "fact_a_hash": self.fact_a_hash,
            "fact_b_hash": self.fact_b_hash,
            "conflict_type": self.conflict_type.value,
            "conflict_status": self.conflict_status.value,
            "detected_at": self.detected_at.isoformat(),
            "resolution_fact_hash": self.resolution_fact_hash,
            "resolution_reason": self.resolution_reason,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Conflict:
        """Construct from dictionary."""
        return cls(
            conflict_id=d["conflict_id"],
            fact_a_hash=d["fact_a_hash"],
            fact_b_hash=d["fact_b_hash"],
            conflict_type=ConflictType(d["conflict_type"]),
            conflict_status=ConflictStatus(d["conflict_status"]),
            detected_at=datetime.fromisoformat(d["detected_at"]),
            resolution_fact_hash=d.get("resolution_fact_hash"),
            resolution_reason=d.get("resolution_reason"),
            resolved_at=datetime.fromisoformat(d["resolved_at"]) if d.get("resolved_at") else None,
        )


@dataclass
class QueryResult:
    """Result of a memory query operation.

    Contains the facts matching a query along with metadata about
    the query execution and context.
    """

    facts: list[tuple[str, Fact]]  # List of (hash, fact) tuples
    query_time: float  # Query execution time in seconds
    branch: str  # Branch name queried
    total_found: int  # Total number of facts found


@dataclass
class ContextBlock:
    """Formatted memory context ready for injection into LLM prompt.

    A context block is the final output of the retrieval system,
    containing formatted facts and conflict warnings ready to be
    injected into an LLM's system prompt.
    """

    formatted_text: str  # Formatted text ready for LLM injection
    fact_count: int  # Number of facts included
    has_conflicts: bool  # Whether any conflicts are present
    assembled_at: datetime  # UTC timestamp of assembly
