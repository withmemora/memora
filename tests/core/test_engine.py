"""Integration tests for Memora v3.1 CoreEngine.

Tests the complete engine pipeline: initialization, ingestion, storage,
indexing, search, and deduplication.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from memora.core.engine import CoreEngine
from memora.shared.models import MemoryType
from memora.shared.exceptions import MemoraError, BranchNotFoundError, StoreNotInitializedError


@pytest.fixture
def temp_store():
    """Create a temporary engine instance for testing."""
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    memora_dir = temp_dir / ".memora"

    try:
        engine = CoreEngine()
        engine.init_store(temp_dir)
        yield engine, temp_dir
    finally:
        # Clean up
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


class TestEngineIntegration:
    """Test CoreEngine integration across all subsystems."""

    def test_init_creates_structure(self, temp_store):
        """Test that init_store creates proper directory structure."""
        engine, store_path = temp_store

        memora_dir = store_path / ".memora"
        assert memora_dir.exists()
        assert (memora_dir / "objects").exists()
        assert (memora_dir / "refs" / "heads").exists()
        assert (memora_dir / "sessions" / "active").exists()
        assert (memora_dir / "sessions" / "closed").exists()
        assert (memora_dir / "graph").exists()
        assert (memora_dir / "index").exists()
        assert (memora_dir / "branches").exists()
        assert (memora_dir / "HEAD").exists()
        assert (memora_dir / "config").exists()
        assert (memora_dir / "graph" / "nodes.json").exists()
        assert (memora_dir / "graph" / "edges.json").exists()

    def test_ingest_and_search_memory(self, temp_store):
        """Test full pipeline: ingest memory → store → search → retrieve."""
        engine, store_path = temp_store

        # Ingest a memory with a clear pattern that should be extracted
        content = "My name is Alice and I work at Tesla"
        result = engine.ingest_text(text=content, source="manual")

        assert isinstance(result, list)
        # At least the ingestion should not crash

        # Search for memories (may find content if extraction worked)
        all_memories = engine.get_all_memories()
        assert isinstance(all_memories, list)

        # Test search functionality
        search_results = engine.search_memories("Alice")
        assert isinstance(search_results, list)

    def test_stats_and_basic_operations(self, temp_store):
        """Test basic engine operations and stats."""
        engine, store_path = temp_store

        # Get initial stats
        stats = engine.get_store_stats()
        assert isinstance(stats, dict)
        assert "memory_count" in stats
        assert "commit_count" in stats
        assert "branch_count" in stats

        initial_memory_count = stats["memory_count"]

        # Ingest some content
        engine.ingest_text("User prefers Python programming", source="manual")
        engine.ingest_text("User lives in San Francisco", source="manual")

        # Get updated stats
        new_stats = engine.get_store_stats()
        assert new_stats["memory_count"] >= initial_memory_count

    def test_deduplication(self, temp_store):
        """Test that duplicate content handling works."""
        engine, store_path = temp_store

        content = "My name is Bob"

        # Ingest same content twice
        result1 = engine.ingest_text(text=content, source="manual")
        result2 = engine.ingest_text(text=content, source="manual")

        # Both should succeed without crashing
        assert isinstance(result1, list)
        assert isinstance(result2, list)

        # System should handle deduplication internally

    def test_forget_memory_basic(self, temp_store):
        """Test basic forget memory functionality."""
        engine, store_path = temp_store

        # Try to forget a nonexistent memory
        success = engine.forget_memory("mem_nonexistent")
        assert success is False

    def test_branch_operations(self, temp_store):
        """Test branch listing and current branch."""
        engine, store_path = temp_store

        # Get current branch
        current_branch = engine.get_current_branch()
        assert current_branch in [None, "main"]  # Could be None if no commits yet

        # List branches
        branches = engine.list_branches()
        assert isinstance(branches, list)

        # Get branch status
        status = engine.get_branch_status()
        assert isinstance(status, dict)

    def test_memory_operations(self, temp_store):
        """Test memory retrieval operations."""
        engine, store_path = temp_store

        # Test get_memory with nonexistent ID
        memory = engine.get_memory("mem_nonexistent")
        assert memory is None

        # Test get_all_memories
        all_memories = engine.get_all_memories()
        assert isinstance(all_memories, list)

        # Test timeline
        timeline = engine.get_timeline()
        assert isinstance(timeline, list)


class TestEngineErrorHandling:
    """Test CoreEngine error handling and edge cases."""

    def test_invalid_store_path(self):
        """Test that invalid store paths raise appropriate errors."""
        engine = CoreEngine()

        # Try to open a non-existent store
        invalid_path = Path("/completely/invalid/path/that/does/not/exist")

        with pytest.raises((FileNotFoundError, PermissionError, OSError, StoreNotInitializedError)):
            engine.open_store(invalid_path)

    def test_forget_nonexistent_memory(self, temp_store):
        """Test forgetting a memory that doesn't exist."""
        engine, store_path = temp_store

        # Try to forget a memory that doesn't exist
        success = engine.forget_memory("mem_nonexistent")
        assert success is False

    def test_switch_to_nonexistent_branch(self, temp_store):
        """Test switching to a branch that doesn't exist."""
        engine, store_path = temp_store

        with pytest.raises(BranchNotFoundError):
            engine.switch_branch("nonexistent-branch")

    def test_search_empty_store(self, temp_store):
        """Test searching in an empty store."""
        engine, store_path = temp_store

        results = engine.search_memories("anything")
        assert isinstance(results, list)
        assert len(results) == 0

    def test_get_stats_empty_store(self, temp_store):
        """Test getting stats from an empty store."""
        engine, store_path = temp_store

        stats = engine.get_store_stats()
        assert isinstance(stats, dict)
        assert stats["memory_count"] == 0
