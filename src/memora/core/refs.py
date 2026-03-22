"""Branch pointer and HEAD management for Memora.

This module provides functions for managing Git-style branch references
and the HEAD pointer in the .memora directory.
"""

import os
from pathlib import Path

from memora.shared.exceptions import BranchNotFoundError


def get_branch(store_path: Path, name: str) -> str:
    """Get the commit hash that a branch points to.

    Args:
        store_path: Path to .memora directory
        name: Branch name (e.g., 'main')

    Returns:
        Commit hash that the branch points to

    Raises:
        BranchNotFoundError: If branch does not exist
    """
    branch_file = store_path / "refs" / "heads" / name
    if not branch_file.exists():
        raise BranchNotFoundError(f"Branch '{name}' not found")

    return branch_file.read_text(encoding="utf-8").strip()


def set_branch(store_path: Path, name: str, commit_hash: str) -> None:
    """Set a branch to point to a specific commit hash.

    Uses atomic write pattern (tmp -> os.replace) for safety.

    Args:
        store_path: Path to .memora directory
        name: Branch name (e.g., 'main')
        commit_hash: 64-character SHA-256 hash of commit
    """
    branch_file = store_path / "refs" / "heads" / name
    branch_file.parent.mkdir(parents=True, exist_ok=True)

    # Atomic write pattern
    tmp_file = branch_file.with_suffix(".tmp")
    tmp_file.write_text(commit_hash + "\n", encoding="utf-8")
    os.replace(tmp_file, branch_file)


def get_head(store_path: Path) -> tuple[str | None, str | None]:
    """Get the current HEAD reference.

    Returns:
        Tuple of (branch_name, commit_hash) or (None, None) if uninitialized

    Examples:
        - ("main", "abc123...") for normal branch HEAD
        - (None, None) if HEAD file doesn't exist (uninitialized)
    """
    head_file = store_path / "HEAD"
    if not head_file.exists():
        return (None, None)

    content = head_file.read_text(encoding="utf-8").strip()

    # HEAD contains "ref: refs/heads/main"
    if content.startswith("ref: refs/heads/"):
        branch_name = content.removeprefix("ref: refs/heads/")
        try:
            commit_hash = get_branch(store_path, branch_name)
            return (branch_name, commit_hash)
        except BranchNotFoundError:
            # Branch reference exists but branch file doesn't (first commit case)
            return (branch_name, None)

    # Detached HEAD (direct hash) - not used in MVP but supported
    return (None, content)


def set_head_to_branch(store_path: Path, name: str) -> None:
    """Set HEAD to point to a branch.

    Uses atomic write pattern (tmp -> os.replace) for safety.

    Args:
        store_path: Path to .memora directory
        name: Branch name (e.g., 'main')
    """
    head_file = store_path / "HEAD"

    # Atomic write pattern
    tmp_file = head_file.with_suffix(".tmp")
    tmp_file.write_text(f"ref: refs/heads/{name}\n", encoding="utf-8")
    os.replace(tmp_file, head_file)


def list_branches(store_path: Path) -> list[tuple[str, str]]:
    """List all branches and their commit hashes.

    Args:
        store_path: Path to .memora directory

    Returns:
        List of (branch_name, commit_hash) tuples sorted alphabetically
    """
    heads_dir = store_path / "refs" / "heads"
    if not heads_dir.exists():
        return []

    branches = []
    for branch_file in heads_dir.iterdir():
        if branch_file.is_file():
            name = branch_file.name
            commit_hash = branch_file.read_text(encoding="utf-8").strip()
            branches.append((name, commit_hash))

    return sorted(branches)
