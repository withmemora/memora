"""Conflict detection and resolution for Memora v3.0.

Compares memory strings (not triples). Simplified from the old model.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from memora.shared.models import Conflict, ConflictType, ConflictStatus, now_iso


def detect_conflicts(
    new_memory_content: str, existing_memories: list[tuple[str, str]]
) -> list[Conflict]:
    """Detect conflicts between a new memory and existing ones.

    Args:
        new_memory_content: The new memory's content string
        existing_memories: List of (memory_id, content) tuples

    Returns:
        List of Conflict objects
    """
    conflicts = []
    new_lower = new_memory_content.lower()

    for existing_id, existing_content in existing_memories:
        existing_lower = existing_content.lower()

        if _is_contradiction(new_lower, existing_lower):
            conflict_type = _classify_conflict(new_memory_content, existing_content)
            conflict_id = _generate_conflict_id(existing_id, new_memory_content)

            conflict = Conflict(
                conflict_id=conflict_id,
                memory_a_id=existing_id,
                memory_b_id="",
                conflict_type=conflict_type,
                conflict_status=ConflictStatus.UNRESOLVED,
                detected_at=now_iso(),
            )
            conflicts.append(conflict)

    return conflicts


def _is_contradiction(text_a: str, text_b: str) -> bool:
    """Check if two memory strings contradict each other."""
    contradiction_pairs = [
        ("lives in", "lives in"),
        ("works at", "works at"),
        ("name is", "name is"),
        ("prefers", "prefers"),
        ("uses", "uses"),
        ("email is", "email is"),
    ]

    for pattern_a, pattern_b in contradiction_pairs:
        if pattern_a in text_a and pattern_b in text_b:
            if text_a != text_b:
                return True

    return False


def _classify_conflict(content_a: str, content_b: str) -> ConflictType:
    now = datetime.now(timezone.utc)
    return ConflictType.TEMPORAL_SUPERSESSION


def _generate_conflict_id(existing_id: str, new_content: str) -> str:
    combined = f"{existing_id}{new_content}{now_iso()}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def store_conflict(conflict: Conflict, store_path: Path) -> None:
    conflicts_dir = store_path / "conflicts"
    if conflict.conflict_status == ConflictStatus.UNRESOLVED:
        target_dir = conflicts_dir / "open"
    else:
        target_dir = conflicts_dir / "resolved"
    target_dir.mkdir(parents=True, exist_ok=True)
    conflict_file = target_dir / f"{conflict.conflict_id}.json"
    conflict_file.write_text(json.dumps(conflict.to_dict(), separators=(",", ":"), sort_keys=True))


def load_conflict(conflict_id: str, store_path: Path) -> Optional[Conflict]:
    conflicts_dir = store_path / "conflicts"
    for subdir in ["open", "resolved"]:
        conflict_file = conflicts_dir / subdir / f"{conflict_id}.json"
        if conflict_file.exists():
            try:
                data = json.loads(conflict_file.read_text())
                return Conflict.from_dict(data)
            except Exception:
                pass
    return None


def list_open_conflicts(store_path: Path) -> list[str]:
    open_dir = store_path / "conflicts" / "open"
    if not open_dir.exists():
        return []
    return sorted([f.stem for f in open_dir.glob("*.json")])


def move_conflict_to_resolved(conflict: Conflict, store_path: Path) -> None:
    conflicts_dir = store_path / "conflicts"
    open_file = conflicts_dir / "open" / f"{conflict.conflict_id}.json"
    resolved_file = conflicts_dir / "resolved" / f"{conflict.conflict_id}.json"
    resolved_file.parent.mkdir(parents=True, exist_ok=True)
    resolved_file.write_text(json.dumps(conflict.to_dict(), separators=(",", ":"), sort_keys=True))
    if open_file.exists():
        open_file.unlink()
