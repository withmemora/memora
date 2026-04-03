"""Core engine for Memora v3.0.

Orchestrates Memory objects, Session lifecycle, auto-commit, indices, graph, and branches.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from memora.core.branch_manager import BranchManager
from memora.core.conflicts import (
    detect_conflicts,
    store_conflict,
    list_open_conflicts,
    load_conflict,
    move_conflict_to_resolved,
)
from memora.core.graph import KnowledgeGraph
from memora.core.index import IndexManager
from memora.core.ingestion import extract_memories
from memora.core.refs import get_branch, set_branch, get_head, set_head_to_branch, list_branches
from memora.core.session import SessionManager
from memora.core.store import ObjectStore
from memora.shared.exceptions import (
    BranchNotFoundError,
    MemoraError,
    ObjectNotFoundError,
    StoreNotInitializedError,
)
from memora.shared.models import (
    Conflict,
    Memory,
    MemoryCommit,
    MemoryTree,
    MemorySource,
    MemoryType,
    now_iso,
)

logger = logging.getLogger(__name__)


class CoreEngine:
    """Unified core engine for Memora v3.0."""

    def __init__(self):
        self._store_path: Path | None = None
        self._object_store: ObjectStore | None = None
        self._session_manager: SessionManager | None = None
        self._index_manager: IndexManager | None = None
        self._graph: KnowledgeGraph | None = None
        self._branch_manager: BranchManager | None = None

    def _ensure(self) -> tuple[Path, ObjectStore]:
        if self._object_store is None or self._store_path is None:
            raise StoreNotInitializedError(
                "No store is open. Call init_store() or open_store() first."
            )
        return self._store_path, self._object_store

    # ==================== Store Lifecycle ====================

    def init_store(self, path: Path) -> None:
        store_path = path / ".memora"
        if store_path.exists():
            raise MemoraError(f"Memora store already exists at {store_path}")
        ObjectStore.initialize_directories(store_path)
        self._store_path = store_path
        self._object_store = ObjectStore(store_path)
        self._session_manager = SessionManager(store_path)
        self._index_manager = IndexManager(store_path)
        self._graph = KnowledgeGraph(store_path)
        self._branch_manager = BranchManager(store_path)
        logger.info(f"Initialized new Memora store at {store_path}")

    def open_store(self, path: Path) -> None:
        store_path = path / ".memora"
        if not store_path.exists():
            raise StoreNotInitializedError(f"No Memora store found at {store_path}")
        self._store_path = store_path
        self._object_store = ObjectStore(store_path)
        self._session_manager = SessionManager(store_path)
        self._index_manager = IndexManager(store_path)
        self._graph = KnowledgeGraph(store_path)
        self._branch_manager = BranchManager(store_path)
        logger.info(f"Opened Memora store at {store_path}")

    # ==================== Ingestion ====================

    def ingest_text(
        self, text: str, source: str = "ollama_chat", author: str = "user"
    ) -> list[tuple[str, Memory]]:
        """Extract memories from text and store them."""
        store_path, store = self._ensure()
        branch = self.get_current_branch() or "main"

        session_mgr = self._session_manager
        session = session_mgr.get_active_session() if session_mgr else None
        session_id = session.id if session else ""

        if not session_id and session_mgr:
            session = session_mgr.open_session(branch)
            session_id = session.id

        memories, ner_entities = extract_memories(
            text,
            source=source,
            session_id=session_id,
            branch=branch,
        )

        result = []
        for memory in memories:
            mem_hash = store.write(memory)
            result.append((mem_hash, memory))

            if session_mgr and session_id:
                session_mgr.add_memory_to_session(session_id, memory.id)

            if self._index_manager:
                self._index_manager.add_memory(
                    memory.id,
                    memory.content,
                    memory.memory_type.value,
                    memory.session_id,
                    memory.created_at,
                )

            if self._graph and ner_entities:
                self._graph.update_from_ner(ner_entities)

        logger.info(f"Ingested {len(result)} memories from text")
        return result

    def ingest_file(
        self, file_path: str, source: str = "file_ingestion"
    ) -> list[tuple[str, Memory]]:
        """Ingest a file and extract memories."""
        from memora.ai.file_processor import FileProcessor

        store_path, store = self._ensure()
        branch = self.get_current_branch() or "main"

        session_mgr = self._session_manager
        session = session_mgr.get_active_session() if session_mgr else None
        session_id = session.id if session else ""

        fp = FileProcessor()
        facts = fp.process_file(file_path, source_prefix=source)

        path = Path(file_path)
        file_type = path.suffix.lower().lstrip(".")

        full_text = ""
        try:
            full_text = path.read_text(encoding="utf-8")
        except Exception:
            full_text = " ".join([f.content for f in facts])

        memories, ner_entities = extract_memories(
            full_text,
            source=source,
            session_id=session_id,
            branch=branch,
            filename=path.name,
            file_type=file_type,
        )

        result = []
        for memory in memories:
            mem_hash = store.write(memory)
            result.append((mem_hash, memory))

            if session_mgr and session_id:
                session_mgr.add_memory_to_session(session_id, memory.id)
                session_mgr.add_file_to_session(session_id, path.name)

            if self._index_manager:
                self._index_manager.add_memory(
                    memory.id,
                    memory.content,
                    memory.memory_type.value,
                    memory.session_id,
                    memory.created_at,
                )

        logger.info(f"Ingested {len(result)} memories from file {file_path}")
        return result

    # ==================== Session & Auto-Commit ====================

    def auto_commit_session(self, session_id: str, author: str = "system") -> str | None:
        """Auto-commit when a session closes."""
        store_path, store = self._ensure()
        session_mgr = self._session_manager
        if not session_mgr:
            return None

        session = session_mgr.close_session(session_id)
        if not session or not session.memory_ids:
            return None

        # Fetch actual memories for a descriptive commit message
        memories = []
        all_hashes = store.list_all_hashes()
        for obj_hash in all_hashes:
            try:
                memory = store.read_memory(obj_hash)
                if memory.id in session.memory_ids:
                    memories.append(memory)
            except Exception:
                continue

        commit_message = session_mgr.generate_commit_message(session, memories)

        tree = MemoryTree(memory_ids=session.memory_ids)
        tree_hash = store.write(tree)

        try:
            branch_name, current_commit_hash = get_head(store_path)
            parent_hash = current_commit_hash if current_commit_hash else None
        except Exception:
            parent_hash = None

        commit = MemoryCommit(
            root_tree_hash=tree_hash,
            parent_hash=parent_hash,
            author=author,
            message=commit_message,
            committed_at=now_iso(),
        )
        commit_hash = store.write(commit)

        branch_name = session.branch
        if branch_name:
            set_branch(store_path, branch_name, commit_hash)
        else:
            set_branch(store_path, "main", commit_hash)
            set_head_to_branch(store_path, "main")

        session.commit_hash = commit_hash
        session.auto_commit_message = commit_message
        session_mgr._write_session(session, session_mgr.closed_path / f"{session_id}.json")

        if self._branch_manager:
            session_count = len(session_mgr.list_sessions(include_closed=True))
            memory_count = len(session.memory_ids)
            self._branch_manager.update_branch_counts(
                session.branch or "main", session_count, memory_count
            )
            self._branch_manager.check_and_auto_create(session.branch or "main")

        logger.info(f"Auto-committed session {session_id}: {commit_hash[:8]}")
        return commit_hash

    def forget_memory(self, memory_id: str) -> bool:
        """Remove a memory by ID. Selective forgetting.

        This:
        1. Deletes the memory object from the store
        2. Removes it from the session index
        3. Removes it from the word/temporal/type indices
        4. Removes it from any active session's memory_ids
        5. Supersedes any graph edges referencing it

        Returns True if found and deleted, False if not found.
        """
        store_path, store = self._ensure()

        # Find the memory object
        target_hash = None
        all_hashes = store.list_all_hashes()
        for obj_hash in all_hashes:
            try:
                memory = store.read_memory(obj_hash)
                if memory.id == memory_id:
                    target_hash = obj_hash
                    break
            except Exception:
                continue

        if not target_hash:
            return False

        # Delete the object file
        obj_path = store._object_path_from_hash(target_hash)
        if obj_path.exists():
            obj_path.unlink()

        # Remove from active session if present
        session_mgr = self._session_manager
        if session_mgr:
            session = session_mgr.get_active_session()
            if session and memory_id in session.memory_ids:
                session.memory_ids.remove(memory_id)
                session_mgr._write_session(session, session_mgr.active_path / f"{session.id}.json")

        # Remove from indices
        if self._index_manager:
            idx = self._index_manager
            # Remove from word index
            words = idx._read_index("words")
            for token, mem_ids in words.items():
                if memory_id in mem_ids:
                    mem_ids.remove(memory_id)
            idx._write_index("words", words)
            # Remove from temporal index
            temporal = idx._read_index("temporal")
            for date_key, mem_ids in temporal.items():
                if memory_id in mem_ids:
                    mem_ids.remove(memory_id)
            idx._write_index("temporal", temporal)
            # Remove from session index
            sessions = idx._read_index("sessions")
            for sess_id, mem_ids in sessions.items():
                if memory_id in mem_ids:
                    mem_ids.remove(memory_id)
            idx._write_index("sessions", sessions)
            # Remove from type index
            types = idx._read_index("types")
            for mem_type, mem_ids in types.items():
                if memory_id in mem_ids:
                    mem_ids.remove(memory_id)
            idx._write_index("types", types)

        # Supersede graph edges
        if self._graph:
            edges = self._graph._load_edges()
            changed = False
            for edge in edges:
                if edge.get("memory_id") == memory_id:
                    edge["superseded_at"] = now_iso()
                    changed = True
            if changed:
                self._graph._save_edges(edges)

        # Clear LRU cache for this hash
        store.read_memory.cache_clear()

        logger.info(f"Forgot memory {memory_id}")
        return True

    def get_active_session(self):
        if self._session_manager:
            return self._session_manager.get_active_session()
        return None

    def list_sessions(self):
        if self._session_manager:
            return self._session_manager.list_sessions()
        return []

    # ==================== Reading ====================

    def get_memory(self, memory_id: str) -> Memory | None:
        store_path, store = self._ensure()
        all_hashes = store.list_all_hashes()
        for obj_hash in all_hashes:
            try:
                memory = store.read_memory(obj_hash)
                if memory.id == memory_id:
                    return memory
            except Exception:
                continue
        return None

    def get_commit(self, hash: str) -> MemoryCommit:
        store_path, store = self._ensure()
        return store.read_commit(hash)

    def get_current_commit(self) -> MemoryCommit | None:
        store_path, store = self._ensure()
        try:
            branch_name, commit_hash = get_head(store_path)
            if commit_hash:
                return store.read_commit(commit_hash)
        except Exception:
            pass
        return None

    def get_log(self, limit: int = 20) -> list[MemoryCommit]:
        store_path, store = self._ensure()
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

    def get_all_memories(
        self,
        branch: str | None = None,
        memory_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Memory]:
        """Get all memories with optional filters and pagination."""
        store_path, store = self._ensure()

        if self._index_manager and memory_type:
            mem_ids = self._index_manager.get_type_memories(memory_type)
            return self._fetch_memories_by_ids(store, mem_ids, skip, limit)

        all_hashes = store.list_all_hashes()
        memories = []
        for obj_hash in all_hashes:
            try:
                memory = store.read_memory(obj_hash)
                if branch and memory.branch != branch:
                    continue
                if memory_type and memory.memory_type.value != memory_type:
                    continue
                memories.append(memory)
            except Exception:
                continue

        memories.sort(key=lambda m: m.created_at, reverse=True)
        return memories[skip : skip + limit]

    def _fetch_memories_by_ids(
        self, store, mem_ids: list[str], skip: int, limit: int
    ) -> list[Memory]:
        memories = []
        for mem_id in mem_ids:
            all_hashes = store.list_all_hashes()
            for obj_hash in all_hashes:
                try:
                    memory = store.read_memory(obj_hash)
                    if memory.id == mem_id:
                        memories.append(memory)
                        break
                except Exception:
                    continue
        return memories[skip : skip + limit]

    # ==================== Search ====================

    def search_memories(self, query: str) -> list[Memory]:
        """Search memories using word index."""
        store_path, store = self._ensure()

        if self._index_manager:
            mem_ids = self._index_manager.search_words(query)
            if mem_ids:
                results = []
                all_hashes = store.list_all_hashes()
                for obj_hash in all_hashes:
                    try:
                        memory = store.read_memory(obj_hash)
                        if memory.id in mem_ids:
                            results.append(memory)
                    except Exception:
                        continue
                return results

        query_lower = query.lower()
        all_hashes = store.list_all_hashes()
        results = []
        for obj_hash in all_hashes:
            try:
                memory = store.read_memory(obj_hash)
                if query_lower in memory.content.lower():
                    results.append(memory)
            except Exception:
                continue
        return results

    def get_timeline(self, start_date: str = "", end_date: str = "") -> list[Memory]:
        """Get memories in chronological order."""
        store_path, store = self._ensure()

        if self._index_manager and (start_date or end_date):
            s = start_date or "2000-01-01"
            e = end_date or "2099-12-31"
            mem_ids = self._index_manager.get_temporal_range(s, e)
            if mem_ids:
                return self._fetch_memories_by_ids(store, mem_ids, 0, 1000)

        all_hashes = store.list_all_hashes()
        memories = []
        for obj_hash in all_hashes:
            try:
                memory = store.read_memory(obj_hash)
                memories.append(memory)
            except Exception:
                continue
        memories.sort(key=lambda m: m.created_at)
        return memories

    # ==================== Conflicts ====================

    def get_open_conflicts(self) -> list[tuple[str, Conflict]]:
        store_path, store = self._ensure()
        conflict_ids = list_open_conflicts(store_path)
        conflicts = []
        for cid in conflict_ids:
            conflict = load_conflict(cid, store_path)
            if conflict:
                conflicts.append((cid, conflict))
        return conflicts

    def resolve_conflict(
        self, conflict_id: str, winning_memory_id: str, reason: str
    ) -> Conflict | None:
        store_path, store = self._ensure()
        conflict = load_conflict(conflict_id, store_path)
        if not conflict:
            return None
        conflict.conflict_status = ConflictStatus.USER_RESOLVED
        conflict.resolution_memory_id = winning_memory_id
        conflict.resolution_reason = reason
        conflict.resolved_at = now_iso()
        move_conflict_to_resolved(conflict, store_path)
        return conflict

    # ==================== Branches ====================

    def create_branch(self, name: str) -> None:
        store_path, store = self._ensure()
        try:
            get_branch(store_path, name)
            raise MemoraError(f"Branch '{name}' already exists")
        except BranchNotFoundError:
            pass
        branch_name, current_commit_hash = get_head(store_path)
        if not current_commit_hash:
            raise MemoraError("No commits exist yet - cannot create branch")
        set_branch(store_path, name, current_commit_hash)
        logger.info(f"Created branch '{name}'")

    def switch_branch(self, name: str) -> None:
        store_path, store = self._ensure()
        try:
            get_branch(store_path, name)
        except BranchNotFoundError:
            raise BranchNotFoundError(f"Branch '{name}' not found")
        set_head_to_branch(store_path, name)
        logger.info(f"Switched to branch '{name}'")

    def list_branches(self) -> list[tuple[str, str]]:
        store_path, store = self._ensure()
        return list_branches(store_path)

    def get_current_branch(self) -> str | None:
        store_path, store = self._ensure()
        try:
            branch_name, _ = get_head(store_path)
            return branch_name
        except Exception:
            return None

    def get_branch_status(self) -> dict:
        """Get current branch size info."""
        store_path, store = self._ensure()
        branch = self.get_current_branch() or "main"
        if self._branch_manager:
            info = self._branch_manager.get_branch_info(branch)
            if info:
                return info
        return {"name": branch, "status": "active"}

    def get_all_branches_status(self) -> list[dict]:
        if self._branch_manager:
            return self._branch_manager.get_all_branches_status()
        return []

    # ==================== Graph ====================

    def get_graph_nodes(self, node_type: str | None = None) -> list[dict]:
        if self._graph:
            return self._graph.get_nodes(node_type)
        return []

    def get_graph_edges(self) -> list[dict]:
        if self._graph:
            return self._graph._load_edges()
        return []

    def get_graph_profile(self) -> dict:
        if self._graph:
            return self._graph.build_profile()
        return {}

    def graph_query(self, entity: str) -> list[dict]:
        if self._graph:
            node_id = entity.lower().replace(" ", "_")
            return self._graph.get_neighbors(node_id)
        return []

    # ==================== Stats ====================

    def get_store_stats(self) -> dict:
        store_path, store = self._ensure()
        all_hashes = store.list_all_hashes()
        memory_count = 0
        for h in all_hashes:
            try:
                store.read_memory(h)
                memory_count += 1
            except Exception:
                pass

        branches = list_branches(store_path)
        open_conflicts = list_open_conflicts(store_path)

        session_count = 0
        if self._session_manager:
            session_count = len(self._session_manager.list_sessions())

        return {
            "memory_count": memory_count,
            "commit_count": len(self.get_log()),
            "branch_count": len(branches),
            "session_count": session_count,
            "open_conflict_count": len(open_conflicts),
            "object_count": len(all_hashes),
        }

    # ==================== Export ====================

    def export_memories(self, format: str = "markdown", branch: str | None = None) -> str:
        """Export memories in the given format."""
        memories = self.get_all_memories(branch=branch, skip=0, limit=10000)

        if format == "json":
            import json

            return json.dumps([m.to_dict() for m in memories], indent=2)
        elif format == "text":
            return "\n".join(m.content for m in memories)
        else:
            lines = []
            current_date = ""
            for m in memories:
                date = m.created_at[:10] if m.created_at else ""
                if date != current_date:
                    lines.append(f"\n## {date}\n")
                    current_date = date
                icon = {"conversation": "💬", "code": "🐍", "document": "📄", "file": "📁"}.get(
                    m.memory_type.value, "💬"
                )
                lines.append(f"{icon} {m.content}")
            return "\n".join(lines)
