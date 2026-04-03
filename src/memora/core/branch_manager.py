"""Branch manager for Memora v3.0.

Handles size limits, auto-creation of successor branches, and context inheritance.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from memora.core.refs import get_branch, set_branch, get_head, set_head_to_branch, list_branches
from memora.shared.models import now_iso


class BranchManager:
    """Manage branch size limits and auto-creation."""

    def __init__(self, store_path: Path):
        self.store_path = store_path
        self.meta_file = store_path / "branches" / "meta.json"

    def _load_meta(self) -> dict:
        if not self.meta_file.exists():
            return {}
        try:
            return json.loads(self.meta_file.read_text())
        except Exception:
            return {}

    def _save_meta(self, meta: dict) -> None:
        self.meta_file.parent.mkdir(parents=True, exist_ok=True)
        self.meta_file.write_text(json.dumps(meta, indent=2))

    def get_branch_info(self, name: str) -> Optional[dict]:
        """Get metadata for a branch."""
        meta = self._load_meta()
        return meta.get(name)

    def update_branch_counts(self, branch: str, session_count: int, memory_count: int) -> None:
        """Update session and memory counts for a branch."""
        meta = self._load_meta()
        if branch not in meta:
            meta[branch] = {
                "created_at": now_iso(),
                "session_count": 0,
                "memory_count": 0,
                "session_limit": 100,
                "memory_limit": 5000,
                "status": "active",
                "successor": None,
                "predecessor": None,
            }
        meta[branch]["session_count"] = session_count
        meta[branch]["memory_count"] = memory_count
        self._save_meta(meta)

    def get_limits(self) -> dict:
        """Get branch limits from config."""
        config_file = self.store_path / "config"
        if config_file.exists():
            try:
                config = json.loads(config_file.read_text())
                branches_config = config.get("branches", {})
                return {
                    "session_limit": branches_config.get("session_limit", 100),
                    "memory_limit": branches_config.get("memory_limit", 5000),
                    "time_limit_days": branches_config.get("time_limit_days", 90),
                    "naming_strategy": branches_config.get("naming_strategy", "sequential"),
                }
            except Exception:
                pass
        return {
            "session_limit": 100,
            "memory_limit": 5000,
            "time_limit_days": 90,
            "naming_strategy": "sequential",
        }

    def check_and_auto_create(self, branch: str) -> Optional[str]:
        """Check if branch hit limits and auto-create successor if needed.

        Returns the new branch name if created, None otherwise.
        """
        limits = self.get_limits()
        meta = self._load_meta()
        branch_info = meta.get(branch)

        if not branch_info:
            return None

        session_count = branch_info.get("session_count", 0)
        memory_count = branch_info.get("memory_count", 0)

        session_hit = session_count >= limits["session_limit"]
        memory_hit = memory_count >= limits["memory_limit"]

        if not session_hit and not memory_hit:
            return None

        if branch_info.get("successor"):
            return branch_info["successor"]

        new_name = self._generate_successor_name(branch, meta, limits["naming_strategy"])

        branch_info["status"] = "full"
        branch_info["successor"] = new_name

        meta[new_name] = {
            "created_at": now_iso(),
            "session_count": 0,
            "memory_count": 0,
            "session_limit": limits["session_limit"],
            "memory_limit": limits["memory_limit"],
            "status": "active",
            "predecessor": branch,
            "successor": None,
        }

        self._save_meta(meta)

        try:
            current_commit = get_branch(self.store_path, branch)
            set_branch(self.store_path, new_name, current_commit)
            set_head_to_branch(self.store_path, new_name)
        except Exception:
            pass

        return new_name

    def _generate_successor_name(self, current: str, meta: dict, strategy: str) -> str:
        if strategy == "sequential":
            base = current.split("-")[0]
            existing = [k for k in meta if k.startswith(base)]
            numbers = []
            for name in existing:
                parts = name.split("-")
                if len(parts) > 1:
                    try:
                        numbers.append(int(parts[-1]))
                    except ValueError:
                        pass
            next_num = max(numbers) + 1 if numbers else 2
            return f"{base}-{next_num}"
        else:
            from datetime import datetime, timezone

            return f"{current}-{datetime.now(timezone.utc).strftime('%Y-%m')}"

    def get_context_for_injection(self, branch: str, max_sessions: int = 20) -> list[str]:
        """Get memory IDs for context injection, traversing ALL predecessors.

        When a branch is young (< 50 sessions), it inherits context from
        the entire predecessor chain, not just the immediate predecessor.
        This means main-3 inherits from main-2, which inherits from main.
        """
        meta = self._load_meta()
        branch_info = meta.get(branch)

        memory_ids = []

        # Walk the entire predecessor chain
        current_branch = branch
        while True:
            info = meta.get(current_branch)
            if not info:
                break

            pred = info.get("predecessor")
            if not pred:
                break

            pred_info = meta.get(pred, {})
            # Only inherit from predecessor if it's not too large
            if pred_info.get("session_count", 0) < 50:
                session_file = self.store_path / "index" / "sessions.json"
                if session_file.exists():
                    try:
                        sessions = json.loads(session_file.read_text())
                        for sess_id, mem_ids in sessions.items():
                            if sess_id.startswith(pred):
                                memory_ids.extend(mem_ids[-max_sessions:])
                    except Exception:
                        pass

            current_branch = pred

        return memory_ids

    def get_all_branches_status(self) -> list[dict]:
        """Get status for all branches."""
        meta = self._load_meta()
        results = []

        for name, info in meta.items():
            session_pct = 0
            memory_pct = 0
            if info.get("session_limit", 100) > 0:
                session_pct = round(info.get("session_count", 0) / info["session_limit"] * 100)
            if info.get("memory_limit", 5000) > 0:
                memory_pct = round(info.get("memory_count", 0) / info["memory_limit"] * 100)

            results.append(
                {
                    "name": name,
                    "status": info.get("status", "active"),
                    "session_count": info.get("session_count", 0),
                    "memory_count": info.get("memory_count", 0),
                    "session_limit": info.get("session_limit", 100),
                    "memory_limit": info.get("memory_limit", 5000),
                    "session_pct": session_pct,
                    "memory_pct": memory_pct,
                    "predecessor": info.get("predecessor"),
                    "successor": info.get("successor"),
                    "created_at": info.get("created_at"),
                }
            )

        return results
