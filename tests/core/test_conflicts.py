"""Tests for conflict detection and resolution."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from memora.core.conflicts import (
    detect_conflicts,
    classify_conflict,
    auto_resolve_conflict,
    store_conflict,
    load_conflict,
    list_open_conflicts,
    move_conflict_to_resolved,
    RecencyPolicy,
    ConfidencePolicy,
    SourcePriorityPolicy,
    ManualReviewPolicy,
)
from memora.shared.models import Fact, Conflict, ContentType, ConflictType, ConflictStatus


def test_detect_conflict_basic():
    """Detect conflict between two contradictory facts."""
    base_time = datetime.utcnow()

    # Same entity+attribute, different values
    fact1 = Fact(
        content="My name is John",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="name",
        value="John",
        source="conversation:session-001",
        observed_at=base_time,
        confidence=0.95,
    )

    fact2 = Fact(
        content="My name is Jane",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="name",
        value="Jane",
        source="conversation:session-001",  # Same source for DIRECT_CONTRADICTION
        observed_at=base_time + timedelta(hours=1),
        confidence=0.95,
    )

    conflicts = detect_conflicts(fact2, [fact1])

    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict.fact_a_hash == fact1.compute_hash()
    assert conflict.fact_b_hash == fact2.compute_hash()
    assert conflict.conflict_status == ConflictStatus.UNRESOLVED
    assert conflict.conflict_type == ConflictType.DIRECT_CONTRADICTION


def test_detect_no_conflict_different_entity():
    """No conflict when entities are different."""
    base_time = datetime.utcnow()

    fact1 = Fact(
        content="My name is John",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="name",
        value="John",
        source="conversation:session-001",
        observed_at=base_time,
        confidence=0.95,
    )

    fact2 = Fact(
        content="The project name is Jane",
        content_type=ContentType.PLAIN_TEXT,
        entity="project",  # Different entity
        attribute="name",
        value="Jane",
        source="conversation:session-002",
        observed_at=base_time + timedelta(hours=1),
        confidence=0.95,
    )

    conflicts = detect_conflicts(fact2, [fact1])
    assert len(conflicts) == 0


def test_detect_no_conflict_different_attribute():
    """No conflict when attributes are different."""
    base_time = datetime.utcnow()

    fact1 = Fact(
        content="My name is John",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="name",
        value="John",
        source="conversation:session-001",
        observed_at=base_time,
        confidence=0.95,
    )

    fact2 = Fact(
        content="My email is John",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="email",  # Different attribute
        value="John",
        source="conversation:session-002",
        observed_at=base_time + timedelta(hours=1),
        confidence=0.95,
    )

    conflicts = detect_conflicts(fact2, [fact1])
    assert len(conflicts) == 0


def test_detect_no_conflict_same_value():
    """No conflict when values are the same."""
    base_time = datetime.utcnow()

    fact1 = Fact(
        content="My name is John",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="name",
        value="John",
        source="conversation:session-001",
        observed_at=base_time,
        confidence=0.95,
    )

    fact2 = Fact(
        content="My name is John",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="name",
        value="John",  # Same value
        source="conversation:session-002",
        observed_at=base_time + timedelta(hours=1),
        confidence=0.95,
    )

    conflicts = detect_conflicts(fact2, [fact1])
    assert len(conflicts) == 0


def test_detect_conflict_case_insensitive_entity_attribute():
    """Conflict detection is case-insensitive for entity and attribute."""
    base_time = datetime.utcnow()

    fact1 = Fact(
        content="My name is John",
        content_type=ContentType.PLAIN_TEXT,
        entity="User",  # Uppercase
        attribute="Name",  # Uppercase
        value="John",
        source="conversation:session-001",
        observed_at=base_time,
        confidence=0.95,
    )

    fact2 = Fact(
        content="My name is Jane",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",  # Lowercase
        attribute="name",  # Lowercase
        value="Jane",
        source="conversation:session-002",
        observed_at=base_time + timedelta(hours=1),
        confidence=0.95,
    )

    conflicts = detect_conflicts(fact2, [fact1])
    assert len(conflicts) == 1


def test_classify_direct_contradiction():
    """Facts within 24h with different values = DIRECT_CONTRADICTION."""
    base_time = datetime.utcnow()

    fact1 = Fact(
        content="My name is John",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="name",
        value="John",
        source="conversation:session-001",
        observed_at=base_time,
        confidence=0.95,
    )

    fact2 = Fact(
        content="My name is Jane",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="name",
        value="Jane",
        source="conversation:session-001",  # Same source for DIRECT_CONTRADICTION
        observed_at=base_time + timedelta(hours=12),  # 12 hours later
        confidence=0.95,
    )

    conflict_type = classify_conflict(fact1, fact2)
    assert conflict_type == ConflictType.DIRECT_CONTRADICTION


def test_classify_temporal_supersession():
    """Facts 7+ days apart with different values = TEMPORAL_SUPERSESSION."""
    base_time = datetime.utcnow()

    fact1 = Fact(
        content="Deadline is March 31st",
        content_type=ContentType.PLAIN_TEXT,
        entity="project",
        attribute="deadline",
        value="March 31st",
        source="conversation:session-001",
        observed_at=base_time,
        confidence=0.90,
    )

    fact2 = Fact(
        content="Deadline is April 5th",
        content_type=ContentType.PLAIN_TEXT,
        entity="project",
        attribute="deadline",
        value="April 5th",
        source="conversation:session-002",
        observed_at=base_time + timedelta(days=8),  # 8 days later
        confidence=0.90,
    )

    conflict_type = classify_conflict(fact1, fact2)
    assert conflict_type == ConflictType.TEMPORAL_SUPERSESSION


def test_classify_source_conflict():
    """Different sources, same time, different values = SOURCE_CONFLICT."""
    base_time = datetime.utcnow()

    fact1 = Fact(
        content="Budget is $50,000",
        content_type=ContentType.PLAIN_TEXT,
        entity="project",
        attribute="budget",
        value="$50,000",
        source="email:manager@company.com",
        observed_at=base_time,
        confidence=0.85,
    )

    fact2 = Fact(
        content="Budget is $75,000",
        content_type=ContentType.PLAIN_TEXT,
        entity="project",
        attribute="budget",
        value="$75,000",
        source="slack:finance-team",  # Different source
        observed_at=base_time + timedelta(minutes=30),  # Same timeframe
        confidence=0.85,
    )

    conflict_type = classify_conflict(fact1, fact2)
    assert conflict_type == ConflictType.SOURCE_CONFLICT


def test_classify_uncertain():
    """Cannot classify = UNCERTAIN."""
    base_time = datetime.utcnow()

    fact1 = Fact(
        content="Location is New York",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="location",
        value="New York",
        source="conversation:session-001",
        observed_at=base_time,
        confidence=0.80,
    )

    fact2 = Fact(
        content="Location is San Francisco",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="location",
        value="San Francisco",
        source="conversation:session-001",  # Same source
        observed_at=base_time + timedelta(days=3),  # Between 1-7 days
        confidence=0.80,
    )

    conflict_type = classify_conflict(fact1, fact2)
    assert conflict_type == ConflictType.UNCERTAIN


def test_auto_resolve_recency():
    """RecencyPolicy resolves conflicts 7+ days apart."""
    base_time = datetime.utcnow()

    fact1 = Fact(
        content="Deadline is March 31st",
        content_type=ContentType.PLAIN_TEXT,
        entity="project",
        attribute="deadline",
        value="March 31st",
        source="conversation:session-001",
        observed_at=base_time,
        confidence=0.90,
    )

    fact2 = Fact(
        content="Deadline is April 5th",
        content_type=ContentType.PLAIN_TEXT,
        entity="project",
        attribute="deadline",
        value="April 5th",
        source="conversation:session-002",
        observed_at=base_time + timedelta(days=8),  # 8 days later
        confidence=0.90,
    )

    conflict = Conflict(
        conflict_id="test-conflict-id",
        fact_a_hash=fact1.compute_hash(),
        fact_b_hash=fact2.compute_hash(),
        conflict_type=ConflictType.TEMPORAL_SUPERSESSION,
        conflict_status=ConflictStatus.UNRESOLVED,
        detected_at=datetime.utcnow(),
        resolution_fact_hash=None,
        resolution_reason=None,
        resolved_at=None,
    )

    resolved = auto_resolve_conflict(conflict, fact1, fact2)

    assert resolved is not None
    assert resolved.conflict_status == ConflictStatus.AUTO_RESOLVED
    assert resolved.resolution_fact_hash == fact2.compute_hash()  # Newer fact wins
    assert resolved.resolution_reason is not None and "RecencyPolicy" in resolved.resolution_reason
    assert resolved.resolved_at is not None


def test_auto_resolve_confidence():
    """ConfidencePolicy resolves when confidence diff ≥ 0.3."""
    base_time = datetime.utcnow()

    fact1 = Fact(
        content="My name is John",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="name",
        value="John",
        source="conversation:session-001",
        observed_at=base_time,
        confidence=0.60,  # Lower confidence
    )

    fact2 = Fact(
        content="My name is Jane",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="name",
        value="Jane",
        source="conversation:session-002",
        observed_at=base_time + timedelta(hours=2),
        confidence=0.95,  # Higher confidence (diff = 0.35 ≥ 0.3)
    )

    conflict = Conflict(
        conflict_id="test-conflict-id",
        fact_a_hash=fact1.compute_hash(),
        fact_b_hash=fact2.compute_hash(),
        conflict_type=ConflictType.DIRECT_CONTRADICTION,
        conflict_status=ConflictStatus.UNRESOLVED,
        detected_at=datetime.utcnow(),
        resolution_fact_hash=None,
        resolution_reason=None,
        resolved_at=None,
    )

    resolved = auto_resolve_conflict(conflict, fact1, fact2)

    assert resolved is not None
    assert resolved.conflict_status == ConflictStatus.AUTO_RESOLVED
    assert resolved.resolution_fact_hash == fact2.compute_hash()  # Higher confidence wins
    assert (
        resolved.resolution_reason is not None and "ConfidencePolicy" in resolved.resolution_reason
    )


def test_auto_resolve_source_priority():
    """SourcePriorityPolicy resolves using configured priority list."""
    base_time = datetime.utcnow()

    fact1 = Fact(
        content="Budget is $50,000",
        content_type=ContentType.PLAIN_TEXT,
        entity="project",
        attribute="budget",
        value="$50,000",
        source="email:team@company.com",  # Lower priority
        observed_at=base_time,
        confidence=0.85,
    )

    fact2 = Fact(
        content="Budget is $75,000",
        content_type=ContentType.PLAIN_TEXT,
        entity="project",
        attribute="budget",
        value="$75,000",
        source="email:cfo@company.com",  # Higher priority
        observed_at=base_time + timedelta(minutes=10),
        confidence=0.85,
    )

    conflict = Conflict(
        conflict_id="test-conflict-id",
        fact_a_hash=fact1.compute_hash(),
        fact_b_hash=fact2.compute_hash(),
        conflict_type=ConflictType.SOURCE_CONFLICT,
        conflict_status=ConflictStatus.UNRESOLVED,
        detected_at=datetime.utcnow(),
        resolution_fact_hash=None,
        resolution_reason=None,
        resolved_at=None,
    )

    # Priority list: CFO has higher priority than team
    priority_list = ["email:team@company.com", "email:cfo@company.com"]

    resolved = auto_resolve_conflict(conflict, fact1, fact2, priority_list)

    assert resolved is not None
    assert resolved.conflict_status == ConflictStatus.AUTO_RESOLVED
    assert resolved.resolution_fact_hash == fact2.compute_hash()  # CFO source wins
    assert (
        resolved.resolution_reason is not None
        and "SourcePriorityPolicy" in resolved.resolution_reason
    )


def test_manual_review_needed():
    """Some conflicts cannot auto-resolve and need manual review."""
    base_time = datetime.utcnow()

    # Create conflict that doesn't meet any auto-resolution criteria
    fact1 = Fact(
        content="Location is New York",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="location",
        value="New York",
        source="conversation:session-001",
        observed_at=base_time,
        confidence=0.80,  # Small confidence diff
    )

    fact2 = Fact(
        content="Location is Boston",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="location",
        value="Boston",
        source="conversation:session-001",  # Same source
        observed_at=base_time + timedelta(days=3),  # Gap < 7 days
        confidence=0.85,  # Confidence diff < 0.3
    )

    conflict = Conflict(
        conflict_id="test-conflict-id",
        fact_a_hash=fact1.compute_hash(),
        fact_b_hash=fact2.compute_hash(),
        conflict_type=ConflictType.UNCERTAIN,
        conflict_status=ConflictStatus.UNRESOLVED,
        detected_at=datetime.utcnow(),
        resolution_fact_hash=None,
        resolution_reason=None,
        resolved_at=None,
    )

    resolved = auto_resolve_conflict(conflict, fact1, fact2)

    assert resolved is None  # Cannot auto-resolve


def test_recency_policy():
    """Test RecencyPolicy class directly."""
    base_time = datetime.utcnow()

    fact1 = Fact(
        content="Old value",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="test",
        value="old",
        source="conversation:session-001",
        observed_at=base_time,
        confidence=0.90,
    )

    fact2 = Fact(
        content="New value",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="test",
        value="new",
        source="conversation:session-002",
        observed_at=base_time + timedelta(days=10),  # 10 days later
        confidence=0.90,
    )

    conflict = Conflict(
        conflict_id="test-conflict-id",
        fact_a_hash=fact1.compute_hash(),
        fact_b_hash=fact2.compute_hash(),
        conflict_type=ConflictType.TEMPORAL_SUPERSESSION,
        conflict_status=ConflictStatus.UNRESOLVED,
        detected_at=datetime.utcnow(),
        resolution_fact_hash=None,
        resolution_reason=None,
        resolved_at=None,
    )

    policy = RecencyPolicy()
    resolved = policy.resolve(conflict, fact1, fact2)

    assert resolved is not None
    assert resolved.resolution_fact_hash == fact2.compute_hash()  # Newer wins


def test_recency_policy_insufficient_gap():
    """RecencyPolicy returns None when time gap < 7 days."""
    base_time = datetime.utcnow()

    fact1 = Fact(
        content="Value 1",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="test",
        value="value1",
        source="conversation:session-001",
        observed_at=base_time,
        confidence=0.90,
    )

    fact2 = Fact(
        content="Value 2",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="test",
        value="value2",
        source="conversation:session-002",
        observed_at=base_time + timedelta(days=3),  # Only 3 days
        confidence=0.90,
    )

    conflict = Conflict(
        conflict_id="test-conflict-id",
        fact_a_hash=fact1.compute_hash(),
        fact_b_hash=fact2.compute_hash(),
        conflict_type=ConflictType.UNCERTAIN,
        conflict_status=ConflictStatus.UNRESOLVED,
        detected_at=datetime.utcnow(),
        resolution_fact_hash=None,
        resolution_reason=None,
        resolved_at=None,
    )

    policy = RecencyPolicy()
    resolved = policy.resolve(conflict, fact1, fact2)

    assert resolved is None


def test_confidence_policy():
    """Test ConfidencePolicy class directly."""
    base_time = datetime.utcnow()

    fact1 = Fact(
        content="Low confidence value",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="test",
        value="low",
        source="conversation:session-001",
        observed_at=base_time,
        confidence=0.50,  # Low confidence
    )

    fact2 = Fact(
        content="High confidence value",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="test",
        value="high",
        source="conversation:session-002",
        observed_at=base_time + timedelta(hours=1),
        confidence=0.95,  # High confidence (diff = 0.45 ≥ 0.3)
    )

    conflict = Conflict(
        conflict_id="test-conflict-id",
        fact_a_hash=fact1.compute_hash(),
        fact_b_hash=fact2.compute_hash(),
        conflict_type=ConflictType.DIRECT_CONTRADICTION,
        conflict_status=ConflictStatus.UNRESOLVED,
        detected_at=datetime.utcnow(),
        resolution_fact_hash=None,
        resolution_reason=None,
        resolved_at=None,
    )

    policy = ConfidencePolicy()
    resolved = policy.resolve(conflict, fact1, fact2)

    assert resolved is not None
    assert resolved.resolution_fact_hash == fact2.compute_hash()  # Higher confidence wins


def test_confidence_policy_insufficient_diff():
    """ConfidencePolicy returns None when confidence diff < 0.3."""
    base_time = datetime.utcnow()

    fact1 = Fact(
        content="Value 1",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="test",
        value="value1",
        source="conversation:session-001",
        observed_at=base_time,
        confidence=0.80,
    )

    fact2 = Fact(
        content="Value 2",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="test",
        value="value2",
        source="conversation:session-002",
        observed_at=base_time + timedelta(hours=1),
        confidence=0.85,  # Diff = 0.05 < 0.3
    )

    conflict = Conflict(
        conflict_id="test-conflict-id",
        fact_a_hash=fact1.compute_hash(),
        fact_b_hash=fact2.compute_hash(),
        conflict_type=ConflictType.DIRECT_CONTRADICTION,
        conflict_status=ConflictStatus.UNRESOLVED,
        detected_at=datetime.utcnow(),
        resolution_fact_hash=None,
        resolution_reason=None,
        resolved_at=None,
    )

    policy = ConfidencePolicy()
    resolved = policy.resolve(conflict, fact1, fact2)

    assert resolved is None


def test_source_priority_policy():
    """Test SourcePriorityPolicy class directly."""
    base_time = datetime.utcnow()

    fact1 = Fact(
        content="Source 1 value",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="test",
        value="source1",
        source="low-priority-source",
        observed_at=base_time,
        confidence=0.85,
    )

    fact2 = Fact(
        content="Source 2 value",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="test",
        value="source2",
        source="high-priority-source",
        observed_at=base_time + timedelta(minutes=5),
        confidence=0.85,
    )

    conflict = Conflict(
        conflict_id="test-conflict-id",
        fact_a_hash=fact1.compute_hash(),
        fact_b_hash=fact2.compute_hash(),
        conflict_type=ConflictType.SOURCE_CONFLICT,
        conflict_status=ConflictStatus.UNRESOLVED,
        detected_at=datetime.utcnow(),
        resolution_fact_hash=None,
        resolution_reason=None,
        resolved_at=None,
    )

    priority_list = ["low-priority-source", "high-priority-source"]
    policy = SourcePriorityPolicy(priority_list)
    resolved = policy.resolve(conflict, fact1, fact2)

    assert resolved is not None
    assert resolved.resolution_fact_hash == fact2.compute_hash()  # High priority source wins


def test_source_priority_policy_sources_not_in_list():
    """SourcePriorityPolicy returns None when sources not in priority list."""
    base_time = datetime.utcnow()

    fact1 = Fact(
        content="Value 1",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="test",
        value="value1",
        source="unknown-source-1",
        observed_at=base_time,
        confidence=0.85,
    )

    fact2 = Fact(
        content="Value 2",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="test",
        value="value2",
        source="unknown-source-2",
        observed_at=base_time + timedelta(minutes=5),
        confidence=0.85,
    )

    conflict = Conflict(
        conflict_id="test-conflict-id",
        fact_a_hash=fact1.compute_hash(),
        fact_b_hash=fact2.compute_hash(),
        conflict_type=ConflictType.SOURCE_CONFLICT,
        conflict_status=ConflictStatus.UNRESOLVED,
        detected_at=datetime.utcnow(),
        resolution_fact_hash=None,
        resolution_reason=None,
        resolved_at=None,
    )

    priority_list = ["known-source-1", "known-source-2"]
    policy = SourcePriorityPolicy(priority_list)
    resolved = policy.resolve(conflict, fact1, fact2)

    assert resolved is None


def test_manual_review_policy():
    """Test ManualReviewPolicy class directly."""
    base_time = datetime.utcnow()

    fact1 = Fact(
        content="Value 1",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="test",
        value="value1",
        source="conversation:session-001",
        observed_at=base_time,
        confidence=0.85,
    )

    fact2 = Fact(
        content="Value 2",
        content_type=ContentType.PLAIN_TEXT,
        entity="user",
        attribute="test",
        value="value2",
        source="conversation:session-002",
        observed_at=base_time + timedelta(hours=1),
        confidence=0.85,
    )

    conflict = Conflict(
        conflict_id="test-conflict-id",
        fact_a_hash=fact1.compute_hash(),
        fact_b_hash=fact2.compute_hash(),
        conflict_type=ConflictType.DIRECT_CONTRADICTION,
        conflict_status=ConflictStatus.UNRESOLVED,
        detected_at=datetime.utcnow(),
        resolution_fact_hash=None,
        resolution_reason=None,
        resolved_at=None,
    )

    policy = ManualReviewPolicy()
    resolved = policy.resolve(conflict, fact1, fact2)

    assert resolved is None  # Always returns None


def test_store_and_load_conflict():
    """Test storing and loading conflicts to/from filesystem."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store_path = Path(tmp_dir)

        # Create a conflict
        base_time = datetime.utcnow()

        conflict = Conflict(
            conflict_id="test-conflict-12345",
            fact_a_hash="hash-a",
            fact_b_hash="hash-b",
            conflict_type=ConflictType.DIRECT_CONTRADICTION,
            conflict_status=ConflictStatus.UNRESOLVED,
            detected_at=base_time,
            resolution_fact_hash=None,
            resolution_reason=None,
            resolved_at=None,
        )

        # Store conflict
        store_conflict(conflict, store_path)

        # Verify file exists in open directory
        open_file = store_path / "conflicts" / "open" / "test-conflict-12345.json"
        assert open_file.exists()

        # Load conflict back
        loaded = load_conflict("test-conflict-12345", store_path)

        assert loaded is not None
        assert loaded.conflict_id == conflict.conflict_id
        assert loaded.fact_a_hash == conflict.fact_a_hash
        assert loaded.fact_b_hash == conflict.fact_b_hash
        assert loaded.conflict_type == conflict.conflict_type
        assert loaded.conflict_status == conflict.conflict_status


def test_list_open_conflicts():
    """Test listing open conflicts."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store_path = Path(tmp_dir)

        # Create multiple conflicts
        for i in range(3):
            conflict = Conflict(
                conflict_id=f"conflict-{i:03d}",
                fact_a_hash=f"hash-a-{i}",
                fact_b_hash=f"hash-b-{i}",
                conflict_type=ConflictType.DIRECT_CONTRADICTION,
                conflict_status=ConflictStatus.UNRESOLVED,
                detected_at=datetime.utcnow(),
                resolution_fact_hash=None,
                resolution_reason=None,
                resolved_at=None,
            )
            store_conflict(conflict, store_path)

        # List open conflicts
        open_conflicts = list_open_conflicts(store_path)

        assert len(open_conflicts) == 3
        assert "conflict-000" in open_conflicts
        assert "conflict-001" in open_conflicts
        assert "conflict-002" in open_conflicts


def test_move_conflict_to_resolved():
    """Test moving conflict from open to resolved."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store_path = Path(tmp_dir)

        # Create unresolved conflict
        conflict = Conflict(
            conflict_id="test-conflict-resolve",
            fact_a_hash="hash-a",
            fact_b_hash="hash-b",
            conflict_type=ConflictType.DIRECT_CONTRADICTION,
            conflict_status=ConflictStatus.UNRESOLVED,
            detected_at=datetime.utcnow(),
            resolution_fact_hash=None,
            resolution_reason=None,
            resolved_at=None,
        )

        # Store as open conflict
        store_conflict(conflict, store_path)

        # Verify it's in open directory
        open_file = store_path / "conflicts" / "open" / "test-conflict-resolve.json"
        assert open_file.exists()

        # Resolve the conflict
        conflict.conflict_status = ConflictStatus.AUTO_RESOLVED
        conflict.resolution_fact_hash = "hash-b"
        conflict.resolution_reason = "Test resolution"
        conflict.resolved_at = datetime.utcnow()

        # Move to resolved
        move_conflict_to_resolved(conflict, store_path)

        # Verify file moved
        assert not open_file.exists()
        resolved_file = store_path / "conflicts" / "resolved" / "test-conflict-resolve.json"
        assert resolved_file.exists()

        # Verify content is correct
        loaded = load_conflict("test-conflict-resolve", store_path)
        assert loaded is not None
        assert loaded.conflict_status == ConflictStatus.AUTO_RESOLVED
        assert loaded.resolution_fact_hash == "hash-b"


def test_load_nonexistent_conflict():
    """Test loading conflict that doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store_path = Path(tmp_dir)

        loaded = load_conflict("nonexistent-conflict", store_path)
        assert loaded is None


def test_list_open_conflicts_empty_directory():
    """Test listing open conflicts when directory doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store_path = Path(tmp_dir)

        # Don't create conflicts directory
        open_conflicts = list_open_conflicts(store_path)
        assert len(open_conflicts) == 0
