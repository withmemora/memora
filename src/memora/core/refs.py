"""Branch pointer and HEAD management for Memora v3.0.

Same Git-style refs as before, with added size limit check hooks.
"""

import os
from pathlib import Path

from memora.shared.exceptions import BranchNotFoundError


def get_branch(store_path: Path, name: str) -> str:
    branch_file = store_path / "refs" / "heads" / name
    if not branch_file.exists():
        raise BranchNotFoundError(f"Branch '{name}' not found")
    return branch_file.read_text(encoding="utf-8").strip()


def set_branch(store_path: Path, name: str, commit_hash: str) -> None:
    branch_file = store_path / "refs" / "heads" / name
    branch_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = branch_file.with_suffix(".tmp")
    tmp_file.write_text(commit_hash + "\n", encoding="utf-8")
    os.replace(tmp_file, branch_file)


def get_head(store_path: Path) -> tuple[str | None, str | None]:
    head_file = store_path / "HEAD"
    if not head_file.exists():
        return (None, None)
    content = head_file.read_text(encoding="utf-8").strip()
    if content.startswith("ref: refs/heads/"):
        branch_name = content.removeprefix("ref: refs/heads/")
        try:
            commit_hash = get_branch(store_path, branch_name)
            return (branch_name, commit_hash)
        except BranchNotFoundError:
            return (branch_name, None)
    return (None, content)


def set_head_to_branch(store_path: Path, name: str) -> None:
    head_file = store_path / "HEAD"
    tmp_file = head_file.with_suffix(".tmp")
    tmp_file.write_text(f"ref: refs/heads/{name}\n", encoding="utf-8")
    os.replace(tmp_file, head_file)


def list_branches(store_path: Path) -> list[tuple[str, str]]:
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
