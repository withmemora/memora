"""Tests for session lifecycle v3.0.

This module tests:
- Session open, accumulate, close
- Session timeout detection
- Touch session (reset timeout)
- Session file management (active/ → closed/)
"""

from pathlib import Path

import pytest

from memora.core.session import SessionManager
from memora.shared.models import Session, now_iso


@pytest.fixture
def temp_store(tmp_path: Path) -> Path:
    """Create a temporary .memora directory."""
    store_path = tmp_path / ".memora"
    store_path.mkdir()
    return store_path


@pytest.fixture
def session_manager(temp_store: Path) -> SessionManager:
    """Create a SessionManager instance."""
    return SessionManager(temp_store, timeout_minutes=15)


class TestSessionCreation:
    """Test creating and opening sessions."""

    def test_open_session(self, session_manager: SessionManager):
        """Test opening a new session."""
        session = session_manager.open_session(branch="main", ollama_model="llama3.2:3b")

        assert session.id.startswith("sess_")
        assert session.branch == "main"
        assert session.ollama_model == "llama3.2:3b"
        assert session.ended_at is None
        assert session.memory_ids == []

    def test_session_saved_to_active(self, session_manager: SessionManager):
        """Test that new session is saved to sessions/active/."""
        session = session_manager.open_session(branch="main")

        active_file = session_manager.active_path / f"{session.id}.json"
        assert active_file.exists()

    def test_get_active_session(self, session_manager: SessionManager):
        """Test retrieving the active session."""
        opened = session_manager.open_session(branch="main", ollama_model="llama3")
        retrieved = session_manager.get_active_session()

        assert retrieved is not None
        assert retrieved.id == opened.id
        assert retrieved.branch == opened.branch

    def test_get_active_session_when_none(self, session_manager: SessionManager):
        """Test get_active_session returns None when no active session."""
        result = session_manager.get_active_session()

        assert result is None


class TestSessionAccumulation:
    """Test adding memories to session."""

    def test_add_memory_to_session(self, session_manager: SessionManager):
        """Test adding memory IDs to session."""
        session = session_manager.open_session(branch="main")

        session_manager.add_memory_to_session(session.id, "mem_abc123")
        updated = session_manager.get_active_session()

        assert updated is not None
        assert "mem_abc123" in updated.memory_ids

    def test_add_multiple_memories(self, session_manager: SessionManager):
        """Test accumulating multiple memories."""
        session = session_manager.open_session(branch="main")

        session_manager.add_memory_to_session(session.id, "mem_1")
        session_manager.add_memory_to_session(session.id, "mem_2")
        session_manager.add_memory_to_session(session.id, "mem_3")

        updated = session_manager.get_active_session()
        assert len(updated.memory_ids) == 3


class TestSessionClose:
    """Test closing sessions."""

    def test_close_session(self, session_manager: SessionManager):
        """Test closing an active session."""
        session = session_manager.open_session(branch="main")
        session_manager.add_memory_to_session(session.id, "mem_test")

        closed = session_manager.close_session(session.id)

        assert closed.ended_at is not None
        assert len(closed.memory_ids) == 1

    def test_closed_session_moved_to_closed_dir(self, session_manager: SessionManager):
        """Test that closed session is moved from active/ to closed/."""
        session = session_manager.open_session(branch="main")

        session_manager.close_session(session.id)

        # Should no longer be in active/
        active_file = session_manager.active_path / f"{session.id}.json"
        assert not active_file.exists()

        # Should be in closed/
        closed_file = session_manager.closed_path / f"{session.id}.json"
        assert closed_file.exists()

    def test_get_active_after_close_returns_none(self, session_manager: SessionManager):
        """Test that get_active_session returns None after closing."""
        session = session_manager.open_session(branch="main")
        session_manager.close_session(session.id)

        active = session_manager.get_active_session()
        assert active is None


class TestSessionTimeout:
    """Test session timeout detection."""

    def test_check_timeout_recent_session(self, session_manager: SessionManager):
        """Test that a recent session does not timeout."""
        session = session_manager.open_session(branch="main")

        timed_out_id = session_manager.check_timeout()

        assert timed_out_id is None

    def test_touch_session_resets_timeout(self, session_manager: SessionManager):
        """Test that touch_session resets the timeout clock."""
        session = session_manager.open_session(branch="main")

        # Touch the session (reset timer)
        session_manager.touch_session(session.id)

        # Should not be timed out
        timed_out_id = session_manager.check_timeout()
        assert timed_out_id is None


class TestSessionListing:
    """Test listing sessions."""

    def test_list_all_sessions(self, session_manager: SessionManager):
        """Test listing all sessions (active and closed)."""
        # Open and close some sessions
        sess1 = session_manager.open_session(branch="main")
        session_manager.close_session(sess1.id)

        sess2 = session_manager.open_session(branch="main")
        session_manager.close_session(sess2.id)

        sess3 = session_manager.open_session(branch="main")  # Still active

        all_sessions = session_manager.list_sessions()

        assert len(all_sessions) >= 3


class TestSessionFileIngestion:
    """Test tracking file ingestion in sessions."""

    def test_add_ingested_file(self, session_manager: SessionManager):
        """Test adding ingested files to session."""
        session = session_manager.open_session(branch="main")

        session_manager.add_file_to_session(session.id, "architecture.md")
        updated = session_manager.get_active_session()

        assert "architecture.md" in updated.files_ingested
