"""Garbage collection for Memora to clean up orphaned objects and old data."""

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Set, Dict, List

logger = logging.getLogger(__name__)


class GarbageCollector:
    """Manages cleanup of orphaned objects, old sessions, and resolved conflicts."""

    def __init__(self, store_path: Path):
        self.store_path = Path(store_path)
        self.memora_path = self.store_path / ".memora"

    def collect_garbage(
        self,
        clean_orphaned_objects: bool = True,
        clean_old_sessions: bool = True,
        clean_resolved_conflicts: bool = True,
        archive_sessions: bool = True,
        session_retention_days: int = 90,
        session_archive_days: int = 30,
        conflict_retention_days: int = 30,
    ) -> Dict[str, int]:
        """Run garbage collection with specified options.

        Returns: Dict with counts of cleaned items
        """
        results = {
            "orphaned_objects": 0,
            "old_sessions": 0,
            "archived_sessions": 0,
            "resolved_conflicts": 0,
            "bytes_freed": 0,
        }

        if clean_orphaned_objects:
            results["orphaned_objects"], freed_bytes = self._clean_orphaned_objects()
            results["bytes_freed"] += freed_bytes

        if archive_sessions:
            results["archived_sessions"], freed_bytes = self.archive_old_sessions(session_archive_days)
            results["bytes_freed"] += freed_bytes

        if clean_old_sessions:
            results["old_sessions"], freed_bytes = self._clean_old_sessions(session_retention_days)
            results["bytes_freed"] += freed_bytes

        if clean_resolved_conflicts:
            results["resolved_conflicts"], freed_bytes = self._clean_resolved_conflicts(
                conflict_retention_days
            )
            results["bytes_freed"] += freed_bytes

        logger.info(f"Garbage collection completed: {results}")
        return results

    def _clean_orphaned_objects(self) -> tuple[int, int]:
        """Remove objects not referenced by any branch or active session."""
        objects_dir = self.memora_path / "objects"
        if not objects_dir.exists():
            return 0, 0

        # Collect all referenced object hashes
        referenced_hashes = set()

        # Get hashes from all branch commits
        refs_dir = self.memora_path / "refs" / "heads"
        if refs_dir.exists():
            for branch_file in refs_dir.iterdir():
                if branch_file.is_file():
                    commit_hash = branch_file.read_text().strip()
                    if commit_hash:
                        referenced_hashes.update(self._get_commit_tree_hashes(commit_hash))

        # Get hashes from active sessions
        active_sessions_dir = self.memora_path / "sessions" / "active"
        if active_sessions_dir.exists():
            for session_file in active_sessions_dir.iterdir():
                if session_file.suffix == ".json":
                    try:
                        session_data = json.loads(session_file.read_text())
                        memory_ids = session_data.get("memory_ids", [])
                        # Convert memory IDs to object hashes (would need store access)
                        # This is a simplified version
                        referenced_hashes.update(memory_ids)
                except Exception:
                    continue

        return cleaned_count, bytes_freed

    def archive_old_sessions(self, keep_days: int = 30) -> tuple[int, int]:
        """Consolidate old sessions into monthly archive files.
        
        Sessions older than keep_days are consolidated into monthly archives to reduce
        file count in sessions/closed/ directory.
        
        Before: sessions/closed/sess_001.json, sess_002.json, ... sess_500.json
        After:  sessions/closed/sess_100.json ... sess_150.json (recent 30 days)
                sessions/archive/2026-03.json (all March sessions consolidated)
                sessions/archive/2026-02.json (all February sessions consolidated)
        
        Args:
            keep_days: Keep individual session files for this many days
            
        Returns:
            Tuple of (archived_count, bytes_freed)
        """
        closed_dir = self.memora_path / "sessions" / "closed"
        archive_dir = self.memora_path / "sessions" / "archive"
        
        if not closed_dir.exists():
            return 0, 0
        
        archive_dir.mkdir(parents=True, exist_ok=True)
        cutoff = datetime.now() - timedelta(days=keep_days)
        
        sessions_by_month = defaultdict(list)
        archived_count = 0
        bytes_freed = 0
        
        for session_file in closed_dir.glob("sess_*.json"):
            try:
                session = json.loads(session_file.read_text())
                ended_at_str = session.get("ended_at")
                if not ended_at_str:
                    continue
                
                ended_at = datetime.fromisoformat(ended_at_str.replace("Z", "+00:00"))
                if ended_at < cutoff:
                    month_key = ended_at.strftime("%Y-%m")
                    sessions_by_month[month_key].append(session)
                    bytes_freed += session_file.stat().st_size
                    session_file.unlink()  # Delete individual file
                    archived_count += 1
            except Exception as e:
                logger.warning(f"Failed to process session {session_file.name}: {e}")
                continue
        
        # Write consolidated monthly archives
        for month, sessions in sessions_by_month.items():
            archive_file = archive_dir / f"{month}.json"
            # Append to existing archive or create new
            existing = []
            if archive_file.exists():
                try:
                    existing = json.loads(archive_file.read_text())
                except Exception:
                    existing = []
            
            combined = existing + sessions
            archive_file.write_text(json.dumps(combined, indent=2))
        
        logger.info(f"Archived {archived_count} sessions into {len(sessions_by_month)} monthly files")
        return archived_count, bytes_freed


    def _clean_resolved_conflicts(self, retention_days: int) -> tuple[int, int]:
        """Remove resolved conflicts older than retention period."""
        resolved_conflicts_dir = self.memora_path / "conflicts" / "resolved"
        if not resolved_conflicts_dir.exists():
            return 0, 0

        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cleaned_count = 0
        bytes_freed = 0

        for conflict_file in resolved_conflicts_dir.iterdir():
            if conflict_file.suffix == ".json":
                try:
                    conflict_data = json.loads(conflict_file.read_text())
                    resolved_at_str = conflict_data.get("resolved_at")
                    if resolved_at_str:
                        resolved_at = datetime.fromisoformat(resolved_at_str.replace("Z", "+00:00"))
                        if resolved_at < cutoff_date:
                            bytes_freed += conflict_file.stat().st_size
                            conflict_file.unlink()
                            cleaned_count += 1
                except Exception:
                    continue

        return cleaned_count, bytes_freed

    def _get_commit_tree_hashes(self, commit_hash: str) -> Set[str]:
        """Get all object hashes referenced by a commit tree (simplified)."""
        # This would need full implementation to traverse commit -> tree -> memory objects
        # For now, return the commit hash itself
        return {commit_hash}

    def get_storage_stats(self) -> Dict[str, any]:
        """Get storage statistics for monitoring."""
        stats = {
            "total_objects": 0,
            "total_size_bytes": 0,
            "active_sessions": 0,
            "closed_sessions": 0,
            "open_conflicts": 0,
            "resolved_conflicts": 0,
        }

        # Count objects
        objects_dir = self.memora_path / "objects"
        if objects_dir.exists():
            for prefix_dir in objects_dir.iterdir():
                if prefix_dir.is_dir():
                    for obj_file in prefix_dir.iterdir():
                        if obj_file.is_file():
                            stats["total_objects"] += 1
                            stats["total_size_bytes"] += obj_file.stat().st_size

        # Count sessions
        active_dir = self.memora_path / "sessions" / "active"
        if active_dir.exists():
            stats["active_sessions"] = len(list(active_dir.glob("*.json")))

        closed_dir = self.memora_path / "sessions" / "closed"
        if closed_dir.exists():
            stats["closed_sessions"] = len(list(closed_dir.glob("*.json")))

        # Count conflicts
        open_conflicts_dir = self.memora_path / "conflicts" / "open"
        if open_conflicts_dir.exists():
            stats["open_conflicts"] = len(list(open_conflicts_dir.glob("*.json")))

        resolved_conflicts_dir = self.memora_path / "conflicts" / "resolved"
        if resolved_conflicts_dir.exists():
            stats["resolved_conflicts"] = len(list(resolved_conflicts_dir.glob("*.json")))

        return stats


def run_maintenance(
    store_path: Path, aggressive: bool = False, dry_run: bool = False
) -> Dict[str, any]:
    """Run maintenance tasks on a Memora store.

    Args:
        store_path: Path to the Memora data directory
        aggressive: Enable more aggressive cleanup (shorter retention periods)
        dry_run: Show what would be cleaned without actually deleting

    Returns:
        Dict with maintenance results
    """
    gc = GarbageCollector(store_path)

    # Get stats before cleanup
    before_stats = gc.get_storage_stats()

    if dry_run:
        logger.info("DRY RUN - no files will be deleted")
        return {"dry_run": True, "before": before_stats}

    # Set retention periods based on aggressive flag
    session_retention = 30 if aggressive else 90
    conflict_retention = 7 if aggressive else 30

    # Run garbage collection
    gc_results = gc.collect_garbage(
        session_retention_days=session_retention, conflict_retention_days=conflict_retention
    )

    # Get stats after cleanup
    after_stats = gc.get_storage_stats()

    return {
        "before": before_stats,
        "after": after_stats,
        "cleaned": gc_results,
        "aggressive": aggressive,
    }
