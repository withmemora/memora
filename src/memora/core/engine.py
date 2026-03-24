"""Core engine implementation for Memora.

This is the main assembly point that combines all core modules into
a unified CoreEngine that implements CoreEngineInterface.

The CoreEngine provides the complete contract expected by the interface layer,
orchestrating object storage, ingestion, conflicts, versioning, and retrieval.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from memora.core.conflicts import (
    detect_conflicts,
    store_conflict,
    load_conflict,
    list_open_conflicts,
    move_conflict_to_resolved,
)
from memora.core.ingestion import extract_facts, normalize_text
from memora.core.refs import (
    get_branch,
    set_branch,
    get_head,
    set_head_to_branch,
    list_branches,
)
from memora.core.store import ObjectStore
from memora.shared.exceptions import (
    BranchNotFoundError,
    ConflictExistsError,
    MemoraError,
    ObjectNotFoundError,
    StagingEmptyError,
    StoreNotInitializedError,
)
from memora.shared.interfaces import CoreEngineInterface
from memora.shared.models import Conflict, Fact, MemoryCommit, MemoryTree, MemoryTreeEntry

logger = logging.getLogger(__name__)


class CoreEngine(CoreEngineInterface):
    """Unified core engine implementing the full CoreEngineInterface.

    This engine coordinates all core modules:
    - ObjectStore for content-addressable storage
    - refs functions for branch and HEAD management
    - conflicts functions for conflict detection and resolution
    - Ingestion pipeline for fact extraction

    Since Phase 3 (indexing) and Phase 4 (commit) modules are not available
    in the public repository, this implementation provides simplified fallback
    behavior that works with direct ObjectStore scanning.
    """

    def __init__(self):
        """Initialize the core engine.

        Components are initialized when a store is opened.
        """
        self._store_path: Path | None = None
        self._object_store: ObjectStore | None = None

        # Simple staging area (Phase 3 replacement)
        self._staging: list[str] = []  # List of fact hashes

    def _ensure_initialized(self) -> tuple[Path, ObjectStore]:
        """Ensure store is initialized and return components.

        Returns:
            Tuple of (store_path, object_store)

        Raises:
            StoreNotInitializedError: If no store is open
        """
        if self._object_store is None or self._store_path is None:
            raise StoreNotInitializedError(
                "No store is open. Call init_store() or open_store() first."
            )

        return self._store_path, self._object_store

    # ==================== Store Lifecycle ====================

    def init_store(self, path: Path) -> None:
        """Initialize a new Memora store at the given path."""
        store_path = path / ".memora"

        if store_path.exists():
            raise MemoraError(f"Memora store already exists at {store_path}")

        # Initialize directory structure
        ObjectStore.initialize_directories(store_path)

        # Initialize components
        self._store_path = store_path
        self._object_store = ObjectStore(store_path)

        # Initialize staging
        self._staging = []

        logger.info(f"Initialized new Memora store at {store_path}")

    def open_store(self, path: Path) -> None:
        """Open an existing Memora store at the given path."""
        store_path = path / ".memora"

        if not store_path.exists():
            raise StoreNotInitializedError(f"No Memora store found at {store_path}")

        # Validate basic structure
        required_dirs = ["objects", "refs", "conflicts"]
        for dir_name in required_dirs:
            if not (store_path / dir_name).exists():
                raise StoreNotInitializedError(f"Invalid store structure: missing {dir_name}/")

        # Initialize components
        self._store_path = store_path
        self._object_store = ObjectStore(store_path)

        # Initialize staging (simplified - no persistent staging)
        self._staging = []

        logger.info(f"Opened Memora store at {store_path}")

    # ==================== Ingestion ====================

    def ingest_text(self, text: str, source: str, author: str) -> list[tuple[str, Fact]]:
        """Extract facts from text and stage them."""
        store_path, store = self._ensure_initialized()

        # Run NLP pipeline
        normalized = normalize_text(text)
        if not normalized:
            return []

        # Extract facts from each normalized sentence
        all_facts = []
        for sentence in normalized:
            facts = extract_facts(sentence, source)
            all_facts.extend(facts)

        # Stage extracted facts
        staged_facts = []
        for fact in all_facts:
            fact_hash = self.ingest_fact(fact)
            staged_facts.append((fact_hash, fact))

        logger.info(f"Ingested {len(staged_facts)} facts from text")
        return staged_facts

    def ingest_fact(self, fact: Fact) -> str:
        """Add a single fact to staging area."""
        store_path, store = self._ensure_initialized()

        # Write fact to object store
        fact_hash = store.write(fact)

        # Add to staging
        if fact_hash not in self._staging:
            self._staging.append(fact_hash)

        # Check for conflicts (immediate detection)
        try:
            # Get all existing facts to check conflicts
            all_hashes = store.list_all_hashes()
            existing_facts = []

            for existing_hash in all_hashes:
                if existing_hash == fact_hash:
                    continue
                try:
                    existing_fact = store.read_fact(existing_hash)
                    existing_facts.append(existing_fact)
                except Exception:
                    # Skip if can't read as fact (might be tree/commit)
                    continue

            # Detect conflicts
            conflicts = detect_conflicts(fact, existing_facts)
            for conflict in conflicts:
                store_conflict(conflict, store_path)

        except Exception as e:
            logger.warning(f"Error during conflict detection: {e}")

        return fact_hash

    def get_staging_status(self) -> list[tuple[str, Fact]]:
        """Get all facts currently in the staging area."""
        store_path, store = self._ensure_initialized()

        staged_facts = []
        for fact_hash in self._staging:
            try:
                fact = store.read_fact(fact_hash)
                staged_facts.append((fact_hash, fact))
            except Exception:
                # Remove invalid hash from staging
                self._staging.remove(fact_hash)

        return staged_facts

    # ==================== Commits ====================

    def commit(self, message: str, author: str, mode: str = "lenient") -> str:
        """Create a commit from staged facts."""
        store_path, store = self._ensure_initialized()

        if not self._staging:
            raise StagingEmptyError("Nothing to commit - staging area is empty")

        # Check for unresolved conflicts if strict mode
        if mode == "strict":
            open_conflicts = list_open_conflicts(store_path)
            if open_conflicts:
                raise ConflictExistsError(
                    f"Unresolved conflicts exist: {len(open_conflicts)} conflicts"
                )

        # Build memory tree from staged facts
        entries = []
        for fact_hash in self._staging:
            try:
                fact = store.read_fact(fact_hash)
                # Create tree entry for each fact
                entry = MemoryTreeEntry(
                    name=f"{fact.entity}_{fact.attribute}", entry_type="fact", hash=fact_hash
                )
                entries.append(entry)
            except Exception as e:
                logger.warning(f"Skipping invalid staged fact {fact_hash}: {e}")

        # Create memory tree
        tree = MemoryTree(entries=entries)
        tree_hash = store.write(tree)

        # Get parent commit
        try:
            parent_commit = self.get_current_commit()
            parent_hash = parent_commit.root_tree_hash if parent_commit else None
        except Exception:
            parent_hash = None

        # Create commit
        commit = MemoryCommit(
            root_tree_hash=tree_hash,
            parent_hash=parent_hash,
            author=author,
            message=message,
            committed_at=datetime.utcnow(),
        )
        commit_hash = store.write(commit)

        # Update current branch to point to new commit
        try:
            branch_name, current_commit_hash = get_head(store_path)
            if branch_name:
                set_branch(store_path, branch_name, commit_hash)
            else:
                # Create main branch if no branches exist
                set_branch(store_path, "main", commit_hash)
                set_head_to_branch(store_path, "main")
        except Exception:
            # Create main branch if no branches exist
            set_branch(store_path, "main", commit_hash)
            set_head_to_branch(store_path, "main")

        # Clear staging
        self._staging.clear()

        logger.info(f"Created commit {commit_hash[:8]} with {len(entries)} facts")
        return commit_hash

    def reset_staging(self) -> None:
        """Clear the staging area without committing."""
        self._staging.clear()
        logger.info("Cleared staging area")

    # ==================== Reading Objects ====================

    def get_fact(self, hash: str) -> Fact:
        """Retrieve a fact by its hash."""
        store_path, store = self._ensure_initialized()
        return store.read_fact(hash)

    def get_commit(self, hash: str) -> MemoryCommit:
        """Retrieve a commit by its hash."""
        store_path, store = self._ensure_initialized()
        return store.read_commit(hash)

    def get_current_commit(self) -> MemoryCommit | None:
        """Get the commit pointed to by current branch HEAD."""
        store_path, store = self._ensure_initialized()

        try:
            branch_name, commit_hash = get_head(store_path)
            if commit_hash:
                return store.read_commit(commit_hash)
        except Exception:
            pass

        return None

    def get_log(self, limit: int = 20) -> list[MemoryCommit]:
        """Get commit history starting from current HEAD."""
        store_path, store = self._ensure_initialized()

        current_commit = self.get_current_commit()
        if not current_commit:
            return []

        commits = []
        commit = current_commit

        for _ in range(limit):
            commits.append(commit)

            if not commit.parent_hash:
                break

            try:
                commit = store.read_commit(commit.parent_hash)
            except Exception:
                break

        return commits

    # ==================== Index Queries (Simplified) ====================

    def _get_all_current_facts(self) -> list[tuple[str, Fact]]:
        """Get all facts in current commit by scanning tree structure."""
        current_commit = self.get_current_commit()
        if not current_commit:
            return []

        store_path, store = self._ensure_initialized()

        try:
            tree = store.read_tree(current_commit.root_tree_hash)
            facts = []

            for entry in tree.entries:
                try:
                    if entry.entry_type == "fact":
                        fact = store.read_fact(entry.hash)
                        facts.append((entry.hash, fact))
                except Exception:
                    continue

            return facts
        except Exception:
            return []

    def get_facts_for_entity(self, name: str) -> list[tuple[str, Fact]]:
        """Query facts by entity name."""
        all_facts = self._get_all_current_facts()
        return [(h, f) for h, f in all_facts if f.entity.lower() == name.lower()]

    def get_facts_for_topic(self, path: str) -> list[tuple[str, Fact]]:
        """Query facts by topic path."""
        # Simple attribute matching (topic path extraction would be more complex)
        if "/" in path:
            _, attribute = path.split("/", 1)
        else:
            attribute = path

        all_facts = self._get_all_current_facts()
        return [(h, f) for h, f in all_facts if f.attribute.lower() == attribute.lower()]

    def get_facts_as_of(self, timestamp: str) -> list[tuple[str, Fact]]:
        """Query facts observed up to a given timestamp."""
        try:
            cutoff = datetime.fromisoformat(timestamp)
        except ValueError:
            return []

        all_facts = self._get_all_current_facts()
        return [(h, f) for h, f in all_facts if f.observed_at <= cutoff]

    def get_all_facts(self) -> list[tuple[str, Fact]]:
        """Get all facts in the current commit."""
        return self._get_all_current_facts()

    def search_facts_by_keyword(self, keyword: str) -> list[tuple[str, Fact]]:
        """Search fact values by keyword."""
        keyword_lower = keyword.lower()
        all_facts = self._get_all_current_facts()

        matching = []
        for hash, fact in all_facts:
            if (
                keyword_lower in fact.value.lower()
                or keyword_lower in fact.content.lower()
                or keyword_lower in fact.attribute.lower()
                or keyword_lower in fact.entity.lower()
            ):
                matching.append((hash, fact))

        return matching

    # ==================== Conflicts ====================

    def get_open_conflicts(self) -> list[tuple[str, Conflict]]:
        """Get all unresolved conflicts."""
        store_path, store = self._ensure_initialized()

        conflict_ids = list_open_conflicts(store_path)
        conflicts = []

        for conflict_id in conflict_ids:
            try:
                conflict = load_conflict(conflict_id, store_path)
                if conflict:
                    conflicts.append((conflict_id, conflict))
            except Exception:
                continue

        return conflicts

    def get_resolved_conflicts(self) -> list[tuple[str, Conflict]]:
        """Get all resolved conflicts."""
        store_path, store = self._ensure_initialized()

        # Scan resolved directory
        try:
            resolved_dir = store_path / "conflicts" / "resolved"
            conflicts = []

            if resolved_dir.exists():
                for file in resolved_dir.glob("*.json"):
                    try:
                        conflict = load_conflict(file.stem, store_path)
                        if conflict:
                            conflicts.append((file.stem, conflict))
                    except Exception:
                        continue

            return conflicts
        except Exception:
            return []

    def resolve_conflict(self, conflict_id: str, winning_hash: str, reason: str) -> Conflict:
        """Manually resolve a conflict by choosing a winning fact."""
        store_path, store = self._ensure_initialized()

        conflict = load_conflict(conflict_id, store_path)
        if not conflict:
            raise ObjectNotFoundError(f"Conflict {conflict_id} not found")

        # Update conflict with resolution
        from memora.shared.models import ConflictStatus

        conflict.conflict_status = ConflictStatus.USER_RESOLVED
        conflict.resolution_fact_hash = winning_hash
        conflict.resolution_reason = reason
        conflict.resolved_at = datetime.utcnow()

        # Move to resolved directory
        move_conflict_to_resolved(conflict, store_path)

        return conflict

    # ==================== Branches ====================

    def create_branch(self, name: str) -> None:
        """Create a new branch pointing to current HEAD."""
        store_path, store = self._ensure_initialized()

        # Check if branch already exists
        try:
            get_branch(store_path, name)
            raise MemoraError(f"Branch '{name}' already exists")
        except BranchNotFoundError:
            pass  # Branch doesn't exist, good

        # Get current HEAD
        branch_name, current_commit_hash = get_head(store_path)
        if not current_commit_hash:
            raise MemoraError("No commits exist yet - cannot create branch")

        # Create branch
        set_branch(store_path, name, current_commit_hash)
        logger.info(f"Created branch '{name}' pointing to {current_commit_hash[:8]}")

    def switch_branch(self, name: str) -> None:
        """Switch to an existing branch."""
        store_path, store = self._ensure_initialized()

        try:
            get_branch(store_path, name)
        except BranchNotFoundError:
            raise BranchNotFoundError(f"Branch '{name}' not found")

        set_head_to_branch(store_path, name)
        logger.info(f"Switched to branch '{name}'")

    def list_branches(self) -> list[tuple[str, str]]:
        """List all branches and their commit hashes."""
        store_path, store = self._ensure_initialized()
        return list_branches(store_path)

    def get_current_branch(self) -> str | None:
        """Get the name of the current branch."""
        store_path, store = self._ensure_initialized()
        try:
            branch_name, commit_hash = get_head(store_path)
            return branch_name
        except Exception:
            return None

    # ==================== Info ====================

    def get_store_stats(self) -> dict:
        """Get statistics about the store."""
        store_path, store = self._ensure_initialized()

        # Count facts in current commit
        current_facts = self._get_all_current_facts()
        fact_count = len(current_facts)

        # Count commits by walking from each branch head
        commits = set()
        branches = list_branches(store_path)
        for branch_name, commit_hash in branches:
            try:
                commit = store.read_commit(commit_hash)
                visited = set()

                while commit and commit_hash not in visited:
                    commits.add(commit_hash)
                    visited.add(commit_hash)

                    if commit.parent_hash:
                        commit_hash = commit.parent_hash
                        commit = store.read_commit(commit_hash)
                    else:
                        break
            except Exception:
                continue

        # Count all objects
        all_hashes = store.list_all_hashes()
        object_count = len(all_hashes)

        # Count open conflicts
        open_conflicts = list_open_conflicts(store_path)
        open_conflict_count = len(open_conflicts)

        return {
            "fact_count": fact_count,
            "commit_count": len(commits),
            "branch_count": len(branches),
            "open_conflict_count": open_conflict_count,
            "object_count": object_count,
        }
