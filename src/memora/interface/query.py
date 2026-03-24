"""Retrieval strategies for memory queries.

This module implements five retrieval strategies for finding relevant facts
in response to user queries. It automatically detects the best strategy or
allows manual strategy selection.

NOTE: This implementation provides basic functionality without full indexing.
Full indexing support will be added when Phase 3 and 4 are implemented.
"""

import math
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from memora.shared.models import Fact, QueryResult
from memora.core.store import ObjectStore


def smart_recall(
    query: str, store_path: Path, store: ObjectStore, strategy: str = "auto"
) -> QueryResult:
    """Smart fact retrieval using best strategy for query.

    Strategies:
    - "entity": Name, "I", "my", "me" → entity filtering
    - "topic": Topic path keywords → attribute filtering
    - "temporal": "last week", "recently" → time range filtering
    - "keyword": General query → scan fact values
    - "auto": Detect best strategy automatically

    Args:
        query: User query string
        store_path: Path to .memora directory
        store: ObjectStore instance
        strategy: Strategy to use ("auto", "entity", "topic", "temporal", "keyword")

    Returns:
        QueryResult with ranked facts
    """
    start_time = time.time()

    # Determine strategy
    if strategy == "auto":
        strategy = _detect_strategy(query)

    # Execute retrieval
    facts = []
    if strategy == "entity":
        entity_name = _extract_entity_name(query)
        if entity_name:
            facts = retrieve_by_entity(entity_name, store)
    elif strategy == "topic":
        topic_path = _extract_topic_path(query)
        if topic_path:
            facts = retrieve_by_topic(topic_path, store)
    elif strategy == "temporal":
        start_date, end_date = _extract_time_range(query)
        if start_date and end_date:
            facts = retrieve_by_time(start_date, end_date, store)
    elif strategy == "keyword":
        facts = retrieve_by_keyword(query, store)

    # Rank facts by relevance
    ranked_facts = rank_facts(facts)

    # Create result
    query_time = time.time() - start_time
    fact_tuples = [(fact.compute_hash(), fact) for fact in ranked_facts]

    return QueryResult(
        facts=fact_tuples,
        query_time=query_time,
        branch="main",  # TODO: Get current branch from refs
        total_found=len(facts),
    )


def retrieve_by_entity(name: str, store: ObjectStore) -> list[Fact]:
    """Retrieve facts by entity name.

    Args:
        name: Entity name to search for
        store: ObjectStore instance

    Returns:
        List of facts for the entity
    """
    facts = []

    # Get all fact hashes (simplified approach without indexing)
    all_hashes = store.list_all_hashes()

    # Filter by entity name
    for fact_hash in all_hashes:
        try:
            fact = store.read_fact(fact_hash)
            if fact.entity.lower() == name.lower():
                facts.append(fact)
        except Exception:
            # Skip corrupted or missing facts
            continue

    return facts


def retrieve_by_topic(path: str, store: ObjectStore) -> list[Fact]:
    """Retrieve facts by topic path.

    Args:
        path: Topic path to search for (e.g., "personal/name", "project/deadline")
        store: ObjectStore instance

    Returns:
        List of facts under the topic path
    """
    facts = []

    # Extract attribute from topic path (e.g., "personal/name" -> "name")
    if "/" in path:
        _, attribute = path.split("/", 1)
    else:
        attribute = path

    # Get all fact hashes
    all_hashes = store.list_all_hashes()

    # Filter by attribute
    for fact_hash in all_hashes:
        try:
            fact = store.read_fact(fact_hash)
            if fact.attribute.lower() == attribute.lower():
                facts.append(fact)
        except Exception:
            # Skip corrupted or missing facts
            continue

    return facts


def retrieve_by_time(start: str, end: str, store: ObjectStore) -> list[Fact]:
    """Retrieve facts in time range.

    Args:
        start: Start time as ISO string
        end: End time as ISO string
        store: ObjectStore instance

    Returns:
        List of facts in time range
    """
    facts = []

    # Parse time range
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
    except ValueError:
        return facts

    # Get all fact hashes
    all_hashes = store.list_all_hashes()

    # Filter by entity name
    for fact_hash in all_hashes:
        try:
            fact = store.read_fact(fact_hash)
            if start_dt <= fact.observed_at <= end_dt:
                facts.append(fact)
        except Exception:
            # Skip corrupted or missing facts
            continue

    return facts


def retrieve_by_keyword(keyword: str, store: ObjectStore) -> list[Fact]:
    """Scan all facts for keyword matches.

    Args:
        keyword: Keyword to search for in fact values
        store: ObjectStore instance

    Returns:
        List of facts containing keyword
    """
    facts = []
    keyword_lower = keyword.lower()

    # Get all fact hashes
    all_hashes = store.list_all_hashes()

    # Filter by time range
    for fact_hash in all_hashes:
        try:
            fact = store.read_fact(fact_hash)

            # Check if keyword appears in fact value or content
            if (
                keyword_lower in fact.value.lower()
                or keyword_lower in fact.content.lower()
                or keyword_lower in fact.attribute.lower()
                or keyword_lower in fact.entity.lower()
            ):
                facts.append(fact)
        except Exception:
            # Skip corrupted or missing facts
            continue

    return facts


def rank_facts(facts: list[Fact]) -> list[Fact]:
    """Rank facts by relevance score.

    Formula (from CLAUDE.md):
    score = (confidence × 0.6) + (recency × 0.4)

    Recency formula:
    recency = exp(-age_days / 30)
    yesterday ≈ 1.0, 60 days ≈ 0.13

    Args:
        facts: List of facts to rank

    Returns:
        List of facts sorted by relevance score (highest first)
    """
    if not facts:
        return facts

    now = datetime.utcnow()
    scored_facts = []

    for fact in facts:
        # Calculate age in days
        age = now - fact.observed_at
        age_days = age.total_seconds() / (24 * 3600)

        # Calculate recency score: exp(-age_days / 30)
        recency = math.exp(-age_days / 30.0)

        # Calculate overall score: (confidence × 0.6) + (recency × 0.4)
        score = (fact.confidence * 0.6) + (recency * 0.4)

        scored_facts.append((score, fact))

    # Sort by score (highest first)
    scored_facts.sort(key=lambda x: x[0], reverse=True)

    return [fact for score, fact in scored_facts]


def _detect_strategy(query: str) -> str:
    """Automatically detect best retrieval strategy for query.

    Args:
        query: User query string

    Returns:
        Strategy name ("entity", "topic", "temporal", "keyword")
    """
    query_lower = query.lower()

    # Temporal indicators: time references (check first - more specific)
    temporal_patterns = [
        r"\b(last|recent|yesterday|today|this|when|ago|before|after)\b",
        r"\b(week|month|year|day|hour|minute)\b",
        r"\b(morning|afternoon|evening|night)\b",
        r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b",
    ]

    for pattern in temporal_patterns:
        if re.search(pattern, query_lower):
            return "temporal"

    # Topic indicators: project/work related terms (check second)
    topic_patterns = [
        r"\b(project|work|task|goal|deadline|budget)\b",
        r"\b(building|creating|working on)\b",
        r"\b(company|job|office|team)\b",
    ]

    for pattern in topic_patterns:
        if re.search(pattern, query_lower):
            return "topic"

    # Entity indicators: first/second person, names (check last - most general)
    entity_patterns = [
        r"\b(i|my|me|myself)\b",
        r"\b(who am i|what is my|my name)\b",
        r"\b(user|person|self)\b",
    ]

    for pattern in entity_patterns:
        if re.search(pattern, query_lower):
            return "entity"

    # Default to keyword search
    return "keyword"


def _extract_entity_name(query: str) -> Optional[str]:
    """Extract entity name from entity-focused query.

    Args:
        query: User query string

    Returns:
        Entity name or None
    """
    query_lower = query.lower()

    # Check for user-related pronouns with word boundaries
    user_patterns = [r"\bi\b", r"\bmy\b", r"\bme\b", r"\bmyself\b"]
    if any(re.search(pattern, query_lower) for pattern in user_patterns):
        return "user"

    # Check for project-related terms with word boundaries
    if re.search(r"\bproject\b", query_lower):
        return "current_project"

    # TODO: Add more sophisticated entity extraction
    return "user"  # Default to user entity


def _extract_topic_path(query: str) -> Optional[str]:
    """Extract topic path from topic-focused query.

    Args:
        query: User query string

    Returns:
        Topic path or None
    """
    query_lower = query.lower()

    # Check for specific combinations first (more specific patterns)
    if re.search(r"\bproject\b.*\bdeadline\b", query_lower) or re.search(
        r"\bdeadline\b.*\bproject\b", query_lower
    ):
        return "project/deadline"
    if re.search(r"\bproject\b.*\bbudget\b", query_lower) or re.search(
        r"\bbudget\b.*\bproject\b", query_lower
    ):
        return "project/budget"

    # Map individual keywords to topic paths
    topic_mappings = {
        r"\bname\b": "personal/name",
        r"\bemail\b": "personal/email",
        r"\blocation\b": "personal/location",
        r"\bproject\b": "personal/current_project",
        r"\bdeadline\b": "project/deadline",
        r"\bbudget\b": "project/budget",
        r"\bgoal\b": "personal/goal",
    }

    for pattern, topic_path in topic_mappings.items():
        if re.search(pattern, query_lower):
            return topic_path

    return None


def _extract_time_range(query: str) -> tuple[Optional[str], Optional[str]]:
    """Extract time range from temporal query.

    Args:
        query: User query string

    Returns:
        Tuple of (start_iso, end_iso) or (None, None)
    """
    query_lower = query.lower()
    now = datetime.utcnow()

    # Handle relative time expressions
    if "last week" in query_lower or "past week" in query_lower:
        end_time = now
        start_time = now - timedelta(days=7)
        return start_time.isoformat(), end_time.isoformat()

    if "last month" in query_lower or "past month" in query_lower:
        end_time = now
        start_time = now - timedelta(days=30)
        return start_time.isoformat(), end_time.isoformat()

    if "yesterday" in query_lower:
        yesterday = now - timedelta(days=1)
        start_time = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start_time.isoformat(), end_time.isoformat()

    if "today" in query_lower:
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = now
        return start_time.isoformat(), end_time.isoformat()

    if "recent" in query_lower or "recently" in query_lower:
        end_time = now
        start_time = now - timedelta(days=7)  # Last week for "recent"
        return start_time.isoformat(), end_time.isoformat()

    # TODO: Add more sophisticated time parsing
    return None, None
