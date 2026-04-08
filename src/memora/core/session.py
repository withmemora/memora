"""Session lifecycle management for Memora v3.0.

Sessions are the fundamental unit replacing manual commits.
Open -> Accumulate memories -> Close -> Auto-commit

Session end is determined by:
1. Connection close (primary signal — client disconnects from proxy)
2. Configurable silence timeout (default 15 min, NOT 5)
3. Explicit close call

The timeout is a safety net, not the primary mechanism.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from memora.shared.models import Memory, Session, now_iso


class SessionManager:
    """Manage session lifecycle."""

    def __init__(self, store_path: Path, timeout_minutes: int = 15):
        self.store_path = store_path
        self.sessions_path = store_path / "sessions"
        self.active_path = self.sessions_path / "active"
        self.closed_path = self.sessions_path / "closed"
        self.timeout_minutes = timeout_minutes

    def open_session(self, branch: str, ollama_model: str = "") -> Session:
        """Open a new session."""
        now = now_iso()
        session = Session(
            id=Session.generate_id(),
            branch=branch,
            started_at=now,
            last_activity_at=now,  # Initialize with current time
            ollama_model=ollama_model,
        )
        self._write_active(session)
        return session

    def get_active_session(self) -> Optional[Session]:
        """Get the currently active session, if any."""
        if not self.active_path.exists():
            return None

        for f in self.active_path.glob("sess_*.json"):
            try:
                data = json.loads(f.read_text())
                return Session.from_dict(data)
            except Exception:
                continue
        return None

    def check_timeout(self) -> Optional[str]:
        """Check if the active session has exceeded the silence timeout.

        Returns the session_id if it has timed out, None otherwise.
        This is called periodically by the proxy to detect abandoned sessions.
        """
        session = self.get_active_session()
        if session is None:
            return None

        from datetime import datetime, timezone, timedelta

        # Use last_activity_at for timeout tracking, fall back to started_at for old sessions
        activity_time_str = session.last_activity_at or session.started_at
        activity_time = datetime.fromisoformat(activity_time_str)
        if activity_time.tzinfo is None:
            activity_time = activity_time.replace(tzinfo=timezone.utc)

        elapsed = datetime.now(timezone.utc) - activity_time
        if elapsed > timedelta(minutes=self.timeout_minutes):
            return session.id

        return None

    def touch_session(self, session_id: str) -> None:
        """Update the session's last_activity_at to now, resetting the timeout.

        Called on every proxy request to keep the session alive.
        This means the timeout is based on last activity, not start time.
        """
        session = self._load_session(session_id)
        if session is None:
            return
        session.last_activity_at = now_iso()
        self._write_session(session, self.active_path / f"{session_id}.json")

    def add_memory_to_session(self, session_id: str, memory_id: str) -> None:
        """Add a memory ID to the active session."""
        session = self._load_session(session_id)
        if session is None:
            return
        if memory_id not in session.memory_ids:
            session.memory_ids.append(memory_id)
            self._write_session(session, self.active_path / f"{session_id}.json")

    def add_file_to_session(self, session_id: str, filename: str) -> None:
        """Track a file ingested during this session."""
        session = self._load_session(session_id)
        if session is None:
            return
        if filename not in session.files_ingested:
            session.files_ingested.append(filename)
            self._write_session(session, self.active_path / f"{session_id}.json")

    def close_session(self, session_id: str) -> Optional[Session]:
        """Close a session and move it to closed/."""
        session = self._load_session(session_id)
        if session is None:
            return None

        session.ended_at = now_iso()

        active_file = self.active_path / f"{session_id}.json"
        if active_file.exists():
            active_file.unlink()

        self._write_session(session, self.closed_path / f"{session_id}.json")
        return session

    def list_sessions(
        self, include_active: bool = True, include_closed: bool = True
    ) -> list[Session]:
        """List all sessions."""
        sessions = []
        if include_active and self.active_path.exists():
            for f in self.active_path.glob("sess_*.json"):
                try:
                    data = json.loads(f.read_text())
                    sessions.append(Session.from_dict(data))
                except Exception:
                    continue
        if include_closed and self.closed_path.exists():
            for f in self.closed_path.glob("sess_*.json"):
                try:
                    data = json.loads(f.read_text())
                    sessions.append(Session.from_dict(data))
                except Exception:
                    continue
        return sorted(sessions, key=lambda s: s.started_at, reverse=True)

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a specific session by ID."""
        session = self._load_session(session_id)
        if session:
            return session
        closed_file = self.closed_path / f"{session_id}.json"
        if closed_file.exists():
            try:
                data = json.loads(closed_file.read_text())
                return Session.from_dict(data)
            except Exception:
                pass
        return None

    def generate_commit_message(self, session: Session, memories: list[Memory]) -> str:
        """Generate a descriptive commit message from actual memory content.

        Instead of "Session 12: 3 memories captured", produces something like:
        "Discussed Python preferences, file ingestion, friend Marcus at Stripe"

        Uses the first few words of each memory, truncated and joined.
        """
        if not memories:
            return "Session: no memories captured"

        topics = []
        for m in memories:
            content = m.content.strip()
            if not content:
                continue
            # Take first 6 words, strip common prefixes
            words = content.split()[:6]
            topic = " ".join(words)
            # Remove leading "User " or "User's " for brevity
            topic = topic.removeprefix("User ").removeprefix("user ")
            topic = topic.removeprefix("User's ").removeprefix("user's ")
            if topic and topic not in topics:
                topics.append(topic)

        if not topics:
            return f"Session: {len(memories)} memories captured"

        # Join up to 3 topics, truncate total to ~100 chars
        message = ", ".join(topics[:3])
        if len(message) > 100:
            message = message[:97] + "..."

        return message

    def _write_active(self, session: Session) -> None:
        self.active_path.mkdir(parents=True, exist_ok=True)
        self._write_session(session, self.active_path / f"{session.id}.json")

    def _write_session(self, session: Session, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(session.to_dict(), indent=2))

    def _load_session(self, session_id: str) -> Optional[Session]:
        active_file = self.active_path / f"{session_id}.json"
        if active_file.exists():
            try:
                data = json.loads(active_file.read_text())
                return Session.from_dict(data)
            except Exception:
                pass
        return None
