"""Tests for object store and refs management.

This module tests:
- ObjectStore: write, read, deduplication, locking, hash verification
- refs functions: branch management, HEAD operations
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from memora.core.objects import hash_fact
from memora.core.refs import (
    get_branch,
    get_head,
    list_branches,
    set_branch,
    set_head_to_branch,
)
from memora.core.store import ObjectStore
from memora.shared.exceptions import (
    BranchNotFoundError,
    HashMismatchError,
    ObjectNotFoundError,
    StoreLockError,
)
from memora.shared.models import ContentType, Fact, MemoryCommit, MemoryTree


@pytest.fixture
def temp_store(tmp_path: Path) -> Path:
    """Create a temporary .memora directory structure."""
    store_path = tmp_path / ".memora"
    ObjectStore.initialize_directories(store_path)
    return store_path


@pytest.fixture
def sample_fact() -> Fact:
    """Create a sample fact for testing."""
    return Fact(
        content="My name is Alice",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="name",
        value="Alice",
        source="test",
        observed_at=datetime(2026, 3, 23, 10, 0, 0, tzinfo=timezone.utc),
        confidence=0.95,
    )


@pytest.fixture
def sample_tree() -> MemoryTree:
    """Create a sample memory tree for testing."""
    from memora.shared.models import MemoryTreeEntry

    return MemoryTree(
        entries=[
            MemoryTreeEntry(
                name="fact1",
                entry_type="fact",
                hash="abc123def456" * 5,
            ),
            MemoryTreeEntry(
                name="fact2",
                entry_type="fact",
                hash="fedcba987654" * 5,
            ),
        ]
    )


@pytest.fixture
def sample_commit() -> MemoryCommit:
    """Create a sample commit for testing."""
    return MemoryCommit(
        root_tree_hash="0" * 64,
        parent_hash=None,
        author="test_user",
        message="Initial commit",
        committed_at=datetime(2026, 3, 23, 10, 0, 0, tzinfo=timezone.utc),
    )


# ========== ObjectStore Tests ==========


def test_initialize_directories(tmp_path: Path):
    """Test that initialize_directories creates correct structure."""
    store_path = tmp_path / ".memora"
    ObjectStore.initialize_directories(store_path)

    # Check all required directories exist
    assert (store_path / "objects").is_dir()
    assert (store_path / "objects" / "tmp").is_dir()
    assert (store_path / "refs" / "heads").is_dir()
    assert (store_path / "staging").is_dir()
    assert (store_path / "conflicts" / "open").is_dir()
    assert (store_path / "conflicts" / "resolved").is_dir()
    assert (store_path / "index").is_dir()

    # Check HEAD file is created correctly
    head_file = store_path / "HEAD"
    assert head_file.exists()
    assert head_file.read_text(encoding="utf-8").strip() == "ref: refs/heads/main"


def test_write_and_read_fact(temp_store: Path, sample_fact: Fact):
    """Test writing and reading a Fact returns identical data."""
    store = ObjectStore(temp_store)

    # Write fact
    fact_hash = store.write(sample_fact)

    # Verify hash is correct
    expected_hash = hash_fact(sample_fact)
    assert fact_hash == expected_hash

    # Read fact back
    read_fact = store.read_fact(fact_hash)

    # Verify data is identical
    assert read_fact.content == sample_fact.content
    assert read_fact.content_type == sample_fact.content_type
    assert read_fact.entity == sample_fact.entity
    assert read_fact.attribute == sample_fact.attribute
    assert read_fact.value == sample_fact.value
    assert read_fact.source == sample_fact.source
    assert read_fact.observed_at == sample_fact.observed_at
    assert read_fact.confidence == sample_fact.confidence


def test_write_and_read_tree(temp_store: Path, sample_tree: MemoryTree):
    """Test writing and reading a MemoryTree returns identical data."""
    store = ObjectStore(temp_store)

    # Write tree
    tree_hash = store.write(sample_tree)

    # Read tree back
    read_tree = store.read_tree(tree_hash)

    # Verify data is identical
    assert len(read_tree.entries) == len(sample_tree.entries)
    for read_entry, sample_entry in zip(read_tree.entries, sample_tree.entries):
        assert read_entry.name == sample_entry.name
        assert read_entry.entry_type == sample_entry.entry_type
        assert read_entry.hash == sample_entry.hash


def test_write_and_read_commit(temp_store: Path, sample_commit: MemoryCommit):
    """Test writing and reading a MemoryCommit returns identical data."""
    store = ObjectStore(temp_store)

    # Write commit
    commit_hash = store.write(sample_commit)

    # Read commit back
    read_commit = store.read_commit(commit_hash)

    # Verify data is identical
    assert read_commit.root_tree_hash == sample_commit.root_tree_hash
    assert read_commit.parent_hash == sample_commit.parent_hash
    assert read_commit.author == sample_commit.author
    assert read_commit.message == sample_commit.message
    assert read_commit.committed_at == sample_commit.committed_at


def test_write_deduplication(temp_store: Path, sample_fact: Fact):
    """Test that writing same object twice creates only one file."""
    store = ObjectStore(temp_store)

    # Write fact twice
    hash1 = store.write(sample_fact)
    hash2 = store.write(sample_fact)

    # Hashes should be identical
    assert hash1 == hash2

    # Only one file should exist in objects/
    object_file = temp_store / "objects" / hash1[:2] / hash1[2:]
    assert object_file.exists()

    # Count total files in objects/ (excluding tmp/)
    object_files = []
    for subdir in (temp_store / "objects").iterdir():
        if subdir.is_dir() and subdir.name != "tmp":
            object_files.extend(subdir.iterdir())

    # Should only be one file
    assert len(object_files) == 1


def test_exists(temp_store: Path, sample_fact: Fact):
    """Test exists() correctly identifies stored objects."""
    store = ObjectStore(temp_store)

    # Write fact
    fact_hash = store.write(sample_fact)

    # exists() should return True
    assert store.exists(fact_hash) is True

    # Non-existent hash should return False
    assert store.exists("0" * 64) is False


def test_read_nonexistent_object(temp_store: Path):
    """Test that reading non-existent hash raises ObjectNotFoundError."""
    store = ObjectStore(temp_store)

    with pytest.raises(ObjectNotFoundError) as exc_info:
        store.read_fact("0" * 64)

    assert "Object not found" in str(exc_info.value)


def test_hash_mismatch_detection(temp_store: Path, sample_fact: Fact):
    """Test that corrupted file raises HashMismatchError."""
    import zlib

    store = ObjectStore(temp_store)

    # Write fact
    fact_hash = store.write(sample_fact)

    # Manually corrupt the file
    object_file = temp_store / "objects" / fact_hash[:2] / fact_hash[2:]
    object_file.write_bytes(b"corrupted data")

    # Reading should raise error (either zlib.error during decompression
    # or HashMismatchError during verification)
    with pytest.raises((HashMismatchError, zlib.error)):
        store.read_fact(fact_hash)


def test_list_all_hashes(temp_store: Path, sample_fact: Fact, sample_tree: MemoryTree):
    """Test list_all_hashes returns all stored hashes."""
    store = ObjectStore(temp_store)

    # Write multiple objects
    fact_hash = store.write(sample_fact)
    tree_hash = store.write(sample_tree)

    # List all hashes
    all_hashes = store.list_all_hashes()

    # Should contain both hashes
    assert len(all_hashes) == 2
    assert fact_hash in all_hashes
    assert tree_hash in all_hashes


def test_lock_acquisition_and_release(temp_store: Path):
    """Test lock acquisition and release."""
    store = ObjectStore(temp_store)

    # Acquire lock
    store.acquire_lock()

    # Lock file should exist
    lock_file = temp_store / ".write_lock"
    assert lock_file.exists()

    # Release lock
    store.release_lock()

    # Should be able to acquire again
    store.acquire_lock()
    store.release_lock()


def test_lock_timeout(temp_store: Path):
    """Test that lock timeout works correctly."""
    store1 = ObjectStore(temp_store)
    store2 = ObjectStore(temp_store)

    # Store1 acquires lock
    store1.acquire_lock()

    # Store2 should timeout (we use a very short timeout for testing)
    store2.lock_timeout = 0.1  # 100ms timeout

    with pytest.raises(StoreLockError) as exc_info:
        store2.acquire_lock()

    assert "Write lock timeout" in str(exc_info.value)

    # Cleanup
    store1.release_lock()


def test_atomic_write(temp_store: Path, sample_fact: Fact):
    """Test that atomic write pattern is used correctly."""
    store = ObjectStore(temp_store)

    # Write fact
    fact_hash = store.write(sample_fact)

    # Verify tmp file was cleaned up
    tmp_dir = temp_store / "objects" / "tmp"
    assert len(list(tmp_dir.iterdir())) == 0

    # Verify final file exists
    object_file = temp_store / "objects" / fact_hash[:2] / fact_hash[2:]
    assert object_file.exists()


# ========== refs Tests ==========


def test_set_and_get_branch(temp_store: Path):
    """Test setting and getting branch pointers."""
    commit_hash = "a" * 64

    set_branch(temp_store, "main", commit_hash)
    retrieved_hash = get_branch(temp_store, "main")

    assert retrieved_hash == commit_hash


def test_get_nonexistent_branch(temp_store: Path):
    """Test getting non-existent branch raises BranchNotFoundError."""
    with pytest.raises(BranchNotFoundError) as exc_info:
        get_branch(temp_store, "nonexistent")

    assert "not found" in str(exc_info.value)


def test_set_head_to_branch(temp_store: Path):
    """Test setting HEAD to point to a branch."""
    set_head_to_branch(temp_store, "main")

    head_file = temp_store / "HEAD"
    content = head_file.read_text(encoding="utf-8").strip()

    assert content == "ref: refs/heads/main"


def test_get_head_with_branch(temp_store: Path):
    """Test getting HEAD when it points to a branch."""
    # Set up branch and HEAD
    commit_hash = "b" * 64
    set_branch(temp_store, "main", commit_hash)
    set_head_to_branch(temp_store, "main")

    branch_name, retrieved_hash = get_head(temp_store)

    assert branch_name == "main"
    assert retrieved_hash == commit_hash


def test_get_head_uninitialized(temp_store: Path):
    """Test getting HEAD when file doesn't exist."""
    # Remove HEAD file
    (temp_store / "HEAD").unlink()

    branch_name, commit_hash = get_head(temp_store)

    assert branch_name is None
    assert commit_hash is None


def test_get_head_with_no_commits(temp_store: Path):
    """Test getting HEAD when branch exists but has no commits yet."""
    # HEAD points to main but main branch file doesn't exist
    set_head_to_branch(temp_store, "main")

    # Remove the branch file if it exists
    branch_file = temp_store / "refs" / "heads" / "main"
    if branch_file.exists():
        branch_file.unlink()

    branch_name, commit_hash = get_head(temp_store)

    assert branch_name == "main"
    assert commit_hash is None


def test_list_branches(temp_store: Path):
    """Test listing all branches."""
    # Create multiple branches
    set_branch(temp_store, "main", "a" * 64)
    set_branch(temp_store, "dev", "b" * 64)
    set_branch(temp_store, "feature", "c" * 64)

    branches = list_branches(temp_store)

    # Should be sorted alphabetically
    assert len(branches) == 3
    assert branches[0][0] == "dev"
    assert branches[1][0] == "feature"
    assert branches[2][0] == "main"

    # Verify hashes
    assert branches[0][1] == "b" * 64
    assert branches[1][1] == "c" * 64
    assert branches[2][1] == "a" * 64


def test_list_branches_empty(temp_store: Path):
    """Test listing branches when none exist."""
    # Remove heads directory
    import shutil

    heads_dir = temp_store / "refs" / "heads"
    if heads_dir.exists():
        shutil.rmtree(heads_dir)

    branches = list_branches(temp_store)

    assert branches == []


def test_branch_atomic_write(temp_store: Path):
    """Test that branch updates use atomic write pattern."""
    commit_hash = "d" * 64
    set_branch(temp_store, "main", commit_hash)

    # Verify no .tmp files left behind
    refs_dir = temp_store / "refs" / "heads"
    tmp_files = list(refs_dir.glob("*.tmp"))
    assert len(tmp_files) == 0

    # Verify final file exists and is correct
    branch_file = refs_dir / "main"
    assert branch_file.exists()
    content = branch_file.read_text(encoding="utf-8").strip()
    assert content == commit_hash
