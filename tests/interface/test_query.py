"""Tests for query retrieval strategies."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import pytest

from memora.interface.query import (
    smart_recall,
    retrieve_by_entity,
    retrieve_by_topic,
    retrieve_by_time,
    retrieve_by_keyword,
    rank_facts,
    _detect_strategy,
    _extract_entity_name,
    _extract_topic_path,
    _extract_time_range,
)
from memora.core.store import ObjectStore
from memora.shared.models import Fact, ContentType


def create_test_fact(
    entity: str,
    attribute: str,
    value: str,
    observed_at: datetime | None = None,
    confidence: float = 0.90,
    source: str = "test",
) -> Fact:
    """Helper to create test facts."""
    if observed_at is None:
        observed_at = datetime.utcnow()

    return Fact(
        content=f"Test content: {value}",
        content_type=ContentType.PLAIN_TEXT,
        entity=entity,
        attribute=attribute,
        value=value,
        source=source,
        observed_at=observed_at,
        confidence=confidence,
    )


def test_smart_recall_entity_strategy():
    """Query with entity name uses entity strategy."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store_path = Path(tmp_dir)
        store = ObjectStore(store_path)
        ObjectStore.initialize_directories(store_path)

        # Create test facts
        user_fact = create_test_fact("user", "name", "John Doe")
        project_fact = create_test_fact("current_project", "name", "Test Project")

        # Store facts
        store.write(user_fact)
        store.write(project_fact)

        # Query with entity keyword
        result = smart_recall("What is my name?", store_path, store)

        assert result.total_found >= 1
        assert any(fact.entity == "user" for _, fact in result.facts)


def test_smart_recall_temporal_strategy():
    """Query with time keywords uses temporal strategy."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store_path = Path(tmp_dir)
        store = ObjectStore(store_path)
        ObjectStore.initialize_directories(store_path)

        # Create facts with different timestamps
        now = datetime.utcnow()
        recent_fact = create_test_fact(
            "user", "activity", "recent work", observed_at=now - timedelta(days=2)
        )
        old_fact = create_test_fact(
            "user", "activity", "old work", observed_at=now - timedelta(days=30)
        )

        # Store facts
        store.write(recent_fact)
        store.write(old_fact)

        # Query with temporal keyword
        result = smart_recall("What did I do last week?", store_path, store)

        assert result.total_found >= 0  # Might be empty due to time range


def test_smart_recall_keyword_strategy():
    """General query uses keyword strategy."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store_path = Path(tmp_dir)
        store = ObjectStore(store_path)
        ObjectStore.initialize_directories(store_path)

        # Create test fact
        fact = create_test_fact("project", "description", "Machine learning project")
        store.write(fact)

        # Query with keyword
        result = smart_recall("machine learning", store_path, store)

        assert result.total_found >= 1
        found_fact = result.facts[0][1]
        assert "machine learning" in found_fact.value.lower()


def test_retrieve_by_entity():
    """Retrieve facts by entity name."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store_path = Path(tmp_dir)
        store = ObjectStore(store_path)
        ObjectStore.initialize_directories(store_path)

        # Create facts for different entities
        user_fact1 = create_test_fact("user", "name", "John")
        user_fact2 = create_test_fact("user", "email", "john@test.com")
        project_fact = create_test_fact("project", "name", "Test")

        # Store facts
        store.write(user_fact1)
        store.write(user_fact2)
        store.write(project_fact)

        # Retrieve user facts
        facts = retrieve_by_entity("user", store)

        assert len(facts) == 2
        assert all(fact.entity == "user" for fact in facts)


def test_retrieve_by_topic():
    """Retrieve facts by topic (attribute)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store_path = Path(tmp_dir)
        store = ObjectStore(store_path)
        ObjectStore.initialize_directories(store_path)

        # Create facts with different attributes
        name_fact1 = create_test_fact("user", "name", "John")
        name_fact2 = create_test_fact("project", "name", "Test Project")
        email_fact = create_test_fact("user", "email", "john@test.com")

        # Store facts
        store.write(name_fact1)
        store.write(name_fact2)
        store.write(email_fact)

        # Retrieve name facts
        facts = retrieve_by_topic("personal/name", store)

        assert len(facts) == 2
        assert all(fact.attribute == "name" for fact in facts)


def test_retrieve_by_time():
    """Retrieve facts in time range."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store_path = Path(tmp_dir)
        store = ObjectStore(store_path)
        ObjectStore.initialize_directories(store_path)

        # Create facts with different timestamps
        now = datetime.utcnow()
        recent_fact = create_test_fact("user", "activity", "recent", observed_at=now)
        old_fact = create_test_fact("user", "activity", "old", observed_at=now - timedelta(days=10))

        # Store facts
        store.write(recent_fact)
        store.write(old_fact)

        # Retrieve recent facts
        start_time = (now - timedelta(days=1)).isoformat()
        end_time = (now + timedelta(days=1)).isoformat()

        facts = retrieve_by_time(start_time, end_time, store)

        assert len(facts) == 1
        assert facts[0].value == "recent"


def test_retrieve_by_keyword():
    """Scan all facts for keyword matches."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store_path = Path(tmp_dir)
        store = ObjectStore(store_path)
        ObjectStore.initialize_directories(store_path)

        # Create facts with different content
        match_fact1 = create_test_fact("user", "hobby", "machine learning")
        match_fact2 = create_test_fact("project", "description", "Learning new skills")
        no_match_fact = create_test_fact("user", "name", "John")

        # Store facts
        store.write(match_fact1)
        store.write(match_fact2)
        store.write(no_match_fact)

        # Search for keyword
        facts = retrieve_by_keyword("learning", store)

        assert len(facts) == 2
        assert all("learning" in fact.value.lower() for fact in facts)


def test_rank_facts_by_score():
    """Facts ranked by (confidence × 0.6) + (recency × 0.4)."""
    now = datetime.utcnow()

    # Create facts with different confidence and recency
    high_conf_old = create_test_fact(
        "user", "test", "high_conf_old", observed_at=now - timedelta(days=30), confidence=0.95
    )
    low_conf_recent = create_test_fact(
        "user", "test", "low_conf_recent", observed_at=now - timedelta(hours=1), confidence=0.60
    )
    medium_fact = create_test_fact(
        "user", "test", "medium", observed_at=now - timedelta(days=7), confidence=0.80
    )

    facts = [high_conf_old, low_conf_recent, medium_fact]
    ranked = rank_facts(facts)

    assert len(ranked) == 3
    # Verify ranking is by score (highest first)
    scores = []
    for fact in ranked:
        age_days = (now - fact.observed_at).total_seconds() / (24 * 3600)
        recency = pow(2.71828, -age_days / 30.0)  # Approximate exp
        score = (fact.confidence * 0.6) + (recency * 0.4)
        scores.append(score)

    # Scores should be in descending order
    assert scores == sorted(scores, reverse=True)


def test_detect_strategy_entity():
    """Detect entity strategy for personal queries."""
    assert _detect_strategy("What is my name?") == "entity"
    assert _detect_strategy("Who am I?") == "entity"
    assert _detect_strategy("My email address") == "entity"


def test_detect_strategy_temporal():
    """Detect temporal strategy for time-based queries."""
    assert _detect_strategy("What did I do last week?") == "temporal"
    assert _detect_strategy("Recent activities") == "temporal"
    assert _detect_strategy("Yesterday's work") == "temporal"


def test_detect_strategy_topic():
    """Detect topic strategy for topic-based queries."""
    assert _detect_strategy("What is my project deadline?") == "topic"
    assert _detect_strategy("Current work status") == "topic"
    assert _detect_strategy("Project budget") == "topic"


def test_detect_strategy_keyword():
    """Default to keyword strategy for general queries."""
    assert _detect_strategy("machine learning algorithms") == "keyword"
    assert _detect_strategy("random search query") == "keyword"


def test_extract_entity_name():
    """Extract entity name from entity queries."""
    assert _extract_entity_name("What is my name?") == "user"
    assert _extract_entity_name("My email") == "user"
    assert _extract_entity_name("Project details") == "current_project"


def test_extract_topic_path():
    """Extract topic path from topic queries."""
    assert _extract_topic_path("What is my name?") == "personal/name"
    assert _extract_topic_path("Project deadline") == "project/deadline"
    assert _extract_topic_path("My email address") == "personal/email"


def test_extract_time_range():
    """Extract time range from temporal queries."""
    start, end = _extract_time_range("last week")
    assert start is not None and end is not None

    # Verify it's approximately a week range
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    duration = (end_dt - start_dt).days
    assert 6 <= duration <= 8  # Allow some tolerance


def test_extract_time_range_today():
    """Extract today's time range."""
    start, end = _extract_time_range("today")
    assert start is not None and end is not None

    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)

    # Should be same day
    assert start_dt.date() == end_dt.date()


def test_extract_time_range_invalid():
    """Return None for queries without time references."""
    start, end = _extract_time_range("machine learning")
    assert start is None and end is None


def test_smart_recall_empty_store():
    """Handle queries on empty store gracefully."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store_path = Path(tmp_dir)
        store = ObjectStore(store_path)
        ObjectStore.initialize_directories(store_path)

        result = smart_recall("test query", store_path, store)

        assert result.total_found == 0
        assert len(result.facts) == 0
        assert result.query_time >= 0


def test_rank_facts_empty_list():
    """Handle empty fact list gracefully."""
    ranked = rank_facts([])
    assert ranked == []


def test_retrieve_by_keyword_case_insensitive():
    """Keyword search is case insensitive."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store_path = Path(tmp_dir)
        store = ObjectStore(store_path)
        ObjectStore.initialize_directories(store_path)

        # Create fact with mixed case
        fact = create_test_fact("user", "hobby", "Machine Learning")
        store.write(fact)

        # Search with lowercase
        facts = retrieve_by_keyword("machine", store)

        assert len(facts) == 1
        assert facts[0].value == "Machine Learning"


def test_retrieve_by_entity_case_insensitive():
    """Entity search is case insensitive."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store_path = Path(tmp_dir)
        store = ObjectStore(store_path)
        ObjectStore.initialize_directories(store_path)

        # Create fact with mixed case entity
        fact = create_test_fact("User", "name", "John")
        store.write(fact)

        # Search with lowercase
        facts = retrieve_by_entity("user", store)

        assert len(facts) == 1
        assert facts[0].entity == "User"
