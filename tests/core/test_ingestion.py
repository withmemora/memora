"""Tests for NLP ingestion pipeline."""

import pytest

from memora.core.ingestion import (
    assign_confidence,
    extract_facts,
    normalize_attribute,
    normalize_text,
)
from memora.shared.models import ContentType


def test_normalize_text_basic() -> None:
    """TEST 1: Normalize and split text into sentences."""
    text = "  Hello world.  This is a test.  "
    sentences = normalize_text(text)

    assert len(sentences) == 2
    assert sentences[0] == "Hello world."
    assert sentences[1] == "This is a test."


def test_normalize_text_empty() -> None:
    """TEST 2: Empty text returns empty list."""
    assert normalize_text("") == []
    assert normalize_text("   ") == []


def test_normalize_text_multiple_sentences() -> None:
    """TEST 3: Split multiple sentences correctly."""
    text = "First sentence. Second sentence! Third sentence?"
    sentences = normalize_text(text)

    assert len(sentences) == 3
    assert "First sentence" in sentences[0]
    assert "Second sentence" in sentences[1]
    assert "Third sentence" in sentences[2]


def test_extract_facts_user_name() -> None:
    """TEST 4: Extract user name from 'My name is X' pattern."""
    facts = extract_facts("My name is Arun Kumar")

    # Should extract name from custom rule, might also extract NER facts
    assert len(facts) >= 1
    name_facts = [f for f in facts if f.attribute == "name" and f.entity == "user"]
    assert len(name_facts) == 1
    assert name_facts[0].entity == "user"
    assert name_facts[0].attribute == "name"
    assert name_facts[0].value == "Arun Kumar"
    assert name_facts[0].confidence == 0.95
    assert name_facts[0].content_type == ContentType.TRIPLE


def test_extract_facts_user_identity() -> None:
    """TEST 5: Extract user identity from 'I am X' pattern."""
    # Test "I am"
    facts1 = extract_facts("I am a software engineer")
    assert len(facts1) == 1
    assert facts1[0].entity == "user"
    assert facts1[0].attribute == "identity"
    assert "software engineer" in facts1[0].value
    assert facts1[0].confidence == 0.95

    # Test "I'm"
    facts2 = extract_facts("I'm a developer")
    assert len(facts2) == 1
    assert facts2[0].entity == "user"
    assert facts2[0].attribute == "identity"
    assert "developer" in facts2[0].value


def test_extract_facts_user_location() -> None:
    """TEST 6: Extract user location from 'I live in X' pattern."""
    facts = extract_facts("I live in San Francisco")

    assert len(facts) >= 1
    # Find the location fact from custom rules
    location_facts = [f for f in facts if f.attribute == "location"]
    assert len(location_facts) >= 1
    assert location_facts[0].entity == "user"
    assert "San Francisco" in location_facts[0].value
    assert location_facts[0].confidence == 0.92


def test_extract_facts_user_email() -> None:
    """TEST 7: Extract user email from 'My email is X' pattern."""
    facts = extract_facts("My email is arun@example.com")

    assert len(facts) >= 1
    email_facts = [f for f in facts if f.attribute == "email"]
    assert len(email_facts) >= 1
    assert email_facts[0].entity == "user"
    assert "arun@example.com" in email_facts[0].value
    assert email_facts[0].confidence == 0.95


def test_extract_facts_user_employer() -> None:
    """TEST 8: Extract user employer from 'I work at X' pattern."""
    facts = extract_facts("I work at Google")

    assert len(facts) >= 1
    employer_facts = [f for f in facts if f.attribute == "employer"]
    assert len(employer_facts) >= 1
    assert employer_facts[0].entity == "user"
    assert "Google" in employer_facts[0].value
    assert employer_facts[0].confidence == 0.95


def test_extract_facts_project_deadline() -> None:
    """TEST 9: Extract project deadline from 'The deadline is X' pattern."""
    facts = extract_facts("The deadline is March 31st")

    assert len(facts) >= 1
    deadline_facts = [f for f in facts if f.attribute == "deadline"]
    assert len(deadline_facts) >= 1
    assert deadline_facts[0].entity == "current_project"
    assert "March 31st" in deadline_facts[0].value
    assert deadline_facts[0].confidence == 0.90
    assert deadline_facts[0].content_type == ContentType.DATE_VALUE


def test_extract_facts_user_preference() -> None:
    """TEST 10: Extract user preference from 'I prefer X' pattern."""
    facts = extract_facts("I prefer Python over Java")

    assert len(facts) >= 1
    pref_facts = [f for f in facts if f.attribute == "preference"]
    assert len(pref_facts) >= 1
    assert pref_facts[0].entity == "user"
    assert "Python" in pref_facts[0].value
    assert pref_facts[0].confidence == 0.90
    assert pref_facts[0].content_type == ContentType.PREFERENCE


def test_extract_facts_user_project() -> None:
    """TEST 11: Extract user project from 'My project is X' pattern."""
    facts = extract_facts("My project is Memora")

    assert len(facts) >= 1
    project_facts = [f for f in facts if f.attribute == "current_project"]
    assert len(project_facts) >= 1
    assert project_facts[0].entity == "user"
    assert "Memora" in project_facts[0].value
    assert project_facts[0].confidence == 0.88


def test_extract_facts_user_building() -> None:
    """TEST 12: Extract what user is building from 'I am building X' pattern."""
    # Test "I am building"
    facts1 = extract_facts("I am building a memory system")
    assert len(facts1) >= 1
    building_facts = [f for f in facts1 if f.attribute == "current_project"]
    assert len(building_facts) >= 1
    assert "memory system" in building_facts[0].value
    assert building_facts[0].confidence == 0.88

    # Test "I'm building"
    facts2 = extract_facts("I'm building an AI app")
    assert len(facts2) >= 1
    building_facts2 = [f for f in facts2 if f.attribute == "current_project"]
    assert len(building_facts2) >= 1
    assert "AI app" in building_facts2[0].value


def test_extract_facts_user_goal() -> None:
    """TEST 13: Extract user goal from 'X is my goal' pattern."""
    facts = extract_facts("Winning the hackathon is my goal")

    assert len(facts) >= 1
    goal_facts = [f for f in facts if f.attribute == "goal"]
    assert len(goal_facts) >= 1
    assert goal_facts[0].entity == "user"
    assert "Winning the hackathon" in goal_facts[0].value
    assert goal_facts[0].confidence == 0.88


def test_extract_facts_multiple_in_one_text() -> None:
    """TEST 14: Extract multiple facts from complex text."""
    text = "My name is Arun and I live in India. I work at TechCorp."

    facts = extract_facts(text)

    # Should extract at least name, location, and employer
    assert len(facts) >= 3

    # Check for name
    name_facts = [f for f in facts if f.attribute == "name"]
    assert len(name_facts) >= 1
    assert "Arun" in name_facts[0].value

    # Check for location
    location_facts = [f for f in facts if f.attribute == "location"]
    assert len(location_facts) >= 1
    assert "India" in location_facts[0].value

    # Check for employer
    employer_facts = [f for f in facts if f.attribute == "employer"]
    assert len(employer_facts) >= 1
    assert "TechCorp" in employer_facts[0].value


def test_extract_facts_deduplication() -> None:
    """TEST 15: Same fact extracted twice should deduplicate by hash."""
    # Say the same thing twice in separate sentences
    text = "My name is Arun. My name is Arun."

    facts = extract_facts(text)

    # Should extract one user name fact (custom rule)
    # The same custom rule should deduplicate
    name_facts = [f for f in facts if f.attribute == "name" and f.entity == "user"]
    assert len(name_facts) == 1

    # However, facts with different entities but same value are different facts
    # (e.g., user.name="Arun" vs mentioned_location.name="Arun")
    # This is correct behavior - different semantic meaning


def test_extract_facts_with_custom_source() -> None:
    """TEST 16: Facts should include custom source provenance."""
    facts = extract_facts("My name is Test", source="test:session-123")

    assert len(facts) >= 1
    assert facts[0].source == "test:session-123"


def test_normalize_attribute_email() -> None:
    """TEST 17: Normalize email attribute aliases."""
    assert normalize_attribute("email_address") == "email"
    assert normalize_attribute("contact email") == "email"
    assert normalize_attribute("contact_email") == "email"
    assert normalize_attribute("e-mail") == "email"


def test_normalize_attribute_name() -> None:
    """TEST 18: Normalize name attribute aliases."""
    assert normalize_attribute("full name") == "name"
    assert normalize_attribute("full_name") == "name"
    assert normalize_attribute("fullname") == "name"


def test_normalize_attribute_location() -> None:
    """TEST 19: Normalize location attribute aliases."""
    assert normalize_attribute("city") == "location"
    assert normalize_attribute("address") == "location"
    assert normalize_attribute("where i live") == "location"
    assert normalize_attribute("place") == "location"


def test_normalize_attribute_deadline() -> None:
    """TEST 20: Normalize deadline attribute aliases."""
    assert normalize_attribute("due date") == "deadline"
    assert normalize_attribute("due_date") == "deadline"
    assert normalize_attribute("duedate") == "deadline"
    assert normalize_attribute("due") == "deadline"


def test_normalize_attribute_project() -> None:
    """TEST 21: Normalize project attribute aliases."""
    assert normalize_attribute("current project") == "current_project"
    assert normalize_attribute("project") == "current_project"
    assert normalize_attribute("current_project") == "current_project"


def test_normalize_attribute_no_alias() -> None:
    """TEST 22: Non-aliased attributes return lowercase version."""
    assert normalize_attribute("custom_field") == "custom_field"
    assert normalize_attribute("UPPERCASE") == "uppercase"
    assert normalize_attribute("  Spaced  ") == "spaced"


def test_assign_confidence_first_person() -> None:
    """TEST 23: First-person matcher extractions get 0.95 confidence."""
    assert assign_confidence("first_person_matcher") == 0.95


def test_assign_confidence_named_entity() -> None:
    """TEST 24: Named entity extractions get 0.85 confidence."""
    assert assign_confidence("named_entity") == 0.85


def test_assign_confidence_contextual() -> None:
    """TEST 25: Contextual inferences get 0.60 confidence."""
    assert assign_confidence("contextual") == 0.60


def test_assign_confidence_ambiguous() -> None:
    """TEST 26: Ambiguous parses get 0.45 confidence."""
    assert assign_confidence("ambiguous") == 0.45


def test_assign_confidence_default() -> None:
    """TEST 27: Unknown extraction types default to 0.45."""
    assert assign_confidence("unknown_type") == 0.45
    assert assign_confidence("") == 0.45


def test_extract_facts_preserves_timestamps() -> None:
    """TEST 28: All facts from same extraction have same timestamp."""
    text = "My name is Arun and I live in India"
    facts = extract_facts(text)

    assert len(facts) >= 2

    # All facts should have timestamps within a few milliseconds of each other
    timestamps = [f.observed_at for f in facts]
    time_diff = max(timestamps) - min(timestamps)
    assert time_diff.total_seconds() < 1.0  # Within 1 second


def test_extract_facts_case_insensitive() -> None:
    """TEST 29: Pattern matching should be case-insensitive."""
    # Lowercase
    facts1 = extract_facts("my name is arun")
    assert len(facts1) >= 1

    # Mixed case
    facts2 = extract_facts("MY NAME IS ARUN")
    assert len(facts2) >= 1

    # Title case
    facts3 = extract_facts("My Name Is Arun")
    assert len(facts3) >= 1


def test_extract_facts_empty_text() -> None:
    """TEST 30: Empty text returns empty fact list."""
    assert extract_facts("") == []
    assert extract_facts("   ") == []
    assert extract_facts("\n\n") == []
