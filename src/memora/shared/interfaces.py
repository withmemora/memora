"""Abstract interfaces for Memora core engine.

This module defines the contract between the core and interface layers.
The interface layer calls ONLY methods defined in these interfaces.
The core layer implements ALL of them.

Following the three-layer architecture:
- interface/ imports from core/ and shared/
- core/ imports from shared/
- shared/ imports from nothing in the project
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from .models import Conflict, ContextBlock, Fact, MemoryCommit, QueryResult


class CoreEngineInterface(ABC):
    """Abstract contract that CoreEngine must implement.

    This interface defines all operations that the interface layer
    can perform on the core engine. It serves as the single point
    of interaction between interface/ and core/ layers.

    The core engine implements this interface and provides all
    storage, indexing, conflict detection, and versioning logic.
    """

    # ==================== Store Lifecycle ====================

    @abstractmethod
    def init_store(self, path: Path) -> None:
        """Initialize a new Memora store at the given path.

        Creates the .memora/ directory structure with all required
        subdirectories and initial files.

        Args:
            path: Directory where .memora/ should be created

        Raises:
            MemoraError: If store already exists or cannot be created
        """
        ...

    @abstractmethod
    def open_store(self, path: Path) -> None:
        """Open an existing Memora store at the given path.

        Validates that .memora/ exists and is properly structured.

        Args:
            path: Directory containing .memora/

        Raises:
            StoreNotInitializedError: If .memora/ does not exist or is invalid
        """
        ...

    # ==================== Ingestion ====================

    @abstractmethod
    def ingest_text(self, text: str, source: str, author: str) -> list[tuple[str, Fact]]:
        """Extract facts from text and stage them.

        Runs the full NLP pipeline (normalize, NER, extract, confidence, dedup)
        and adds extracted facts to staging area.

        Args:
            text: Raw text to extract facts from
            source: Provenance string (e.g., "conversation:session-001")
            author: Author identifier

        Returns:
            List of (hash, fact) tuples that were staged
        """
        ...

    @abstractmethod
    def ingest_fact(self, fact: Fact) -> str:
        """Add a single fact to staging area.

        Computes hash, writes to object store, and stages for commit.

        Args:
            fact: Fact to ingest

        Returns:
            SHA-256 hash of the fact
        """
        ...

    @abstractmethod
    def get_staging_status(self) -> list[tuple[str, Fact]]:
        """Get all facts currently in the staging area.

        Returns:
            List of (hash, fact) tuples in staging
        """
        ...

    # ==================== Commits ====================

    @abstractmethod
    def commit(self, message: str, author: str, mode: str = "lenient") -> str:
        """Create a commit from staged facts.

        Executes the atomic 11-step commit process:
        1. Acquire write lock
        2. Read staged hashes
        3. Load fact objects
        4. Check conflicts (if strict mode)
        5. Build memory trees
        6. Write tree objects
        7. Read parent commit
        8. Create commit object
        9. Write commit object
        10. Update branch pointer atomically
        11. Update indexes and clear staging

        Args:
            message: Commit message
            author: Author identifier
            mode: "strict" or "lenient" - strict blocks on unresolved conflicts

        Returns:
            SHA-256 hash of the created commit

        Raises:
            StagingEmptyError: If nothing is staged
            ConflictExistsError: If mode="strict" and unresolved conflicts exist
            StoreLockError: If write lock cannot be acquired
        """
        ...

    @abstractmethod
    def reset_staging(self) -> None:
        """Clear the staging area without committing.

        Removes all staged facts. Facts remain in object store.
        """
        ...

    # ==================== Reading Objects ====================

    @abstractmethod
    def get_fact(self, hash: str) -> Fact:
        """Retrieve a fact by its hash.

        Args:
            hash: SHA-256 hash of the fact

        Returns:
            The fact object

        Raises:
            ObjectNotFoundError: If hash not in store
            HashMismatchError: If content doesn't match hash (corruption)
        """
        ...

    @abstractmethod
    def get_commit(self, hash: str) -> MemoryCommit:
        """Retrieve a commit by its hash.

        Args:
            hash: SHA-256 hash of the commit

        Returns:
            The commit object

        Raises:
            ObjectNotFoundError: If hash not in store
        """
        ...

    @abstractmethod
    def get_current_commit(self) -> MemoryCommit | None:
        """Get the commit pointed to by current branch HEAD.

        Returns:
            Current commit, or None if no commits exist yet
        """
        ...

    @abstractmethod
    def get_log(self, limit: int = 20) -> list[MemoryCommit]:
        """Get commit history starting from current HEAD.

        Walks the commit graph backwards from HEAD following parent pointers.

        Args:
            limit: Maximum number of commits to return

        Returns:
            List of commits in reverse chronological order (newest first)
        """
        ...

    # ==================== Index Queries ====================

    @abstractmethod
    def get_facts_for_entity(self, name: str) -> list[tuple[str, Fact]]:
        """Query facts by entity name using entity index.

        Args:
            name: Entity name (e.g., "user", "current_project")

        Returns:
            List of (hash, fact) tuples for the entity
        """
        ...

    @abstractmethod
    def get_facts_for_topic(self, path: str) -> list[tuple[str, Fact]]:
        """Query facts by topic path using topic index.

        Args:
            path: Topic path (e.g., "personal/name", "project/deadline")

        Returns:
            List of (hash, fact) tuples under that topic
        """
        ...

    @abstractmethod
    def get_facts_as_of(self, timestamp: str) -> list[tuple[str, Fact]]:
        """Query facts observed up to a given timestamp using temporal index.

        Args:
            timestamp: ISO 8601 timestamp

        Returns:
            List of (hash, fact) tuples observed before or at timestamp
        """
        ...

    @abstractmethod
    def get_all_facts(self) -> list[tuple[str, Fact]]:
        """Get all facts in the current commit.

        Returns:
            List of all (hash, fact) tuples
        """
        ...

    @abstractmethod
    def search_facts_by_keyword(self, keyword: str) -> list[tuple[str, Fact]]:
        """Search fact values by keyword.

        Args:
            keyword: Keyword to search for in fact values

        Returns:
            List of (hash, fact) tuples containing the keyword
        """
        ...

    # ==================== Conflicts ====================

    @abstractmethod
    def get_open_conflicts(self) -> list[tuple[str, Conflict]]:
        """Get all unresolved conflicts.

        Returns:
            List of (conflict_id, conflict) tuples with status=UNRESOLVED
        """
        ...

    @abstractmethod
    def get_resolved_conflicts(self) -> list[tuple[str, Conflict]]:
        """Get all resolved conflicts.

        Returns:
            List of (conflict_id, conflict) tuples with status != UNRESOLVED
        """
        ...

    @abstractmethod
    def resolve_conflict(self, conflict_id: str, winning_hash: str, reason: str) -> Conflict:
        """Manually resolve a conflict by choosing a winning fact.

        Args:
            conflict_id: ID of the conflict to resolve
            winning_hash: Hash of the fact chosen as correct
            reason: Human-readable explanation of resolution

        Returns:
            Updated conflict with status=USER_RESOLVED

        Raises:
            ObjectNotFoundError: If conflict_id not found
        """
        ...

    # ==================== Branches ====================

    @abstractmethod
    def create_branch(self, name: str) -> None:
        """Create a new branch pointing to current HEAD.

        Args:
            name: Branch name

        Raises:
            MemoraError: If branch already exists
        """
        ...

    @abstractmethod
    def switch_branch(self, name: str) -> None:
        """Switch to an existing branch.

        Args:
            name: Branch name

        Raises:
            BranchNotFoundError: If branch does not exist
        """
        ...

    @abstractmethod
    def list_branches(self) -> list[tuple[str, str]]:
        """List all branches and their commit hashes.

        Returns:
            List of (branch_name, commit_hash) tuples
        """
        ...

    @abstractmethod
    def get_current_branch(self) -> str | None:
        """Get the name of the current branch.

        Returns:
            Current branch name, or None if in detached HEAD state
        """
        ...

    # ==================== Info ====================

    @abstractmethod
    def get_store_stats(self) -> dict:
        """Get statistics about the store.

        Returns:
            Dictionary with keys:
            - fact_count: Total facts in current commit
            - commit_count: Total commits
            - branch_count: Total branches
            - open_conflict_count: Unresolved conflicts
            - object_count: Total objects in store
        """
        ...
