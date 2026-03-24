"""High-performance indexing system for Memora fact storage.

This module provides efficient fact indexing with:
  1. Multi-dimensional indices (entity, attribute, value, entity+attribute)
  2. Integration with performance caching layer
  3. Fast conflict detection through indexed lookups
  4. Query optimization for common access patterns
"""

import time
from typing import Dict, List, Set, Optional, Tuple, Iterator
from datetime import datetime, timezone
from pathlib import Path
import threading

from memora.shared.models import Fact, ConflictType
from memora.core.performance import PerformanceLayer, timed_query
from memora.shared.exceptions import ObjectNotFoundError


class ConflictDetector:
    """Optimized conflict detection using indexed fact lookups."""

    def __init__(self, performance_layer: PerformanceLayer):
        """Initialize conflict detector.

        Args:
            performance_layer: Performance layer for fast fact access
        """
        self.perf = performance_layer

    def detect_conflicts(
        self, new_fact: Fact, existing_facts: List[Tuple[str, Fact]]
    ) -> List[Tuple[str, ConflictType]]:
        """Detect conflicts between new fact and existing facts.

        Args:
            new_fact: New fact to check for conflicts
            existing_facts: List of (hash, fact) tuples to check against

        Returns:
            List of (fact_hash, conflict_type) tuples for conflicting facts
        """
        conflicts = []

        # Find facts with same entity+attribute for targeted conflict detection
        candidate_hashes = self.perf.find_facts_by_entity_attribute(
            new_fact.entity, new_fact.attribute
        )

        for fact_hash, existing_fact in existing_facts:
            if fact_hash not in candidate_hashes:
                continue  # Skip facts that can't conflict

            conflict_type = self._check_fact_conflict(new_fact, existing_fact)
            if conflict_type:
                conflicts.append((fact_hash, conflict_type))

        return conflicts

    def _check_fact_conflict(self, fact1: Fact, fact2: Fact) -> Optional[ConflictType]:
        """Check if two facts conflict and return conflict type.

        Args:
            fact1: First fact
            fact2: Second fact

        Returns:
            ConflictType if conflict exists, None otherwise
        """
        # Only facts with same entity+attribute can conflict
        if fact1.entity != fact2.entity or fact1.attribute != fact2.attribute:
            return None

        # Same value - no conflict
        if fact1.value == fact2.value:
            return None

        # Direct contradiction - different values for same entity+attribute
        if fact1.value != fact2.value:
            # Check temporal supersession
            time_diff = abs((fact1.observed_at - fact2.observed_at).total_seconds())
            if time_diff > 3600:  # More than 1 hour apart
                return ConflictType.TEMPORAL_SUPERSESSION

            # Check source conflict
            if fact1.source != fact2.source:
                return ConflictType.SOURCE_CONFLICT

            # Direct contradiction if same time period and source
            return ConflictType.DIRECT_CONTRADICTION

        return None


class FactIndexManager:
    """Manager for fact indices with performance optimization."""

    def __init__(self, performance_layer: PerformanceLayer):
        """Initialize index manager.

        Args:
            performance_layer: Performance layer for caching
        """
        self.perf = performance_layer
        self.conflict_detector = ConflictDetector(performance_layer)
        self._lock = threading.RLock()

    @timed_query
    def add_fact(self, fact: Fact, fact_hash: str) -> None:
        """Add fact to indices and cache.

        Args:
            fact: Fact to add
            fact_hash: Hash of the fact
        """
        with self._lock:
            self.perf.cache_fact(fact_hash, fact)

    @timed_query
    def remove_fact(self, fact: Fact, fact_hash: str) -> None:
        """Remove fact from indices and cache.

        Args:
            fact: Fact to remove
            fact_hash: Hash of the fact
        """
        with self._lock:
            self.perf.invalidate_fact(fact_hash, fact)

    @timed_query
    def get_fact(self, fact_hash: str) -> Optional[Fact]:
        """Get fact from cache/index.

        Args:
            fact_hash: Hash of the fact

        Returns:
            Fact object or None if not found
        """
        return self.perf.get_fact(fact_hash)

    @timed_query
    def query_by_entity(self, entity: str) -> Set[str]:
        """Find all facts for a specific entity.

        Args:
            entity: Entity name to search for

        Returns:
            Set of fact hashes
        """
        return self.perf.find_facts_by_entity(entity)

    @timed_query
    def query_by_attribute(self, attribute: str) -> Set[str]:
        """Find all facts for a specific attribute.

        Args:
            attribute: Attribute name to search for

        Returns:
            Set of fact hashes
        """
        return self.perf.find_facts_by_attribute(attribute)

    @timed_query
    def query_by_entity_attribute(self, entity: str, attribute: str) -> Set[str]:
        """Find all facts for a specific entity-attribute pair.

        Args:
            entity: Entity name
            attribute: Attribute name

        Returns:
            Set of fact hashes
        """
        return self.perf.find_facts_by_entity_attribute(entity, attribute)

    @timed_query
    def detect_conflicts_for_fact(
        self, new_fact: Fact, existing_facts: List[Tuple[str, Fact]]
    ) -> List[Tuple[str, ConflictType]]:
        """Detect conflicts for a new fact against existing facts.

        Args:
            new_fact: New fact to check
            existing_facts: Existing facts to check against

        Returns:
            List of conflicting fact hashes and conflict types
        """
        return self.conflict_detector.detect_conflicts(new_fact, existing_facts)

    def get_index_statistics(self) -> Dict[str, any]:
        """Get comprehensive index and performance statistics.

        Returns:
            Dictionary with statistics
        """
        return self.perf.get_performance_stats()


class QueryOptimizer:
    """Optimize queries using indices and caching."""

    def __init__(self, index_manager: FactIndexManager):
        """Initialize query optimizer.

        Args:
            index_manager: Index manager for fact access
        """
        self.index_manager = index_manager
        self.perf = index_manager.perf

    def optimize_entity_query(self, entity: str) -> str:
        """Create optimized query key for entity searches.

        Args:
            entity: Entity to search for

        Returns:
            Optimized query key for caching
        """
        return f"entity:{entity}"

    def optimize_attribute_query(self, attribute: str) -> str:
        """Create optimized query key for attribute searches.

        Args:
            attribute: Attribute to search for

        Returns:
            Optimized query key for caching
        """
        return f"attribute:{attribute}"

    def optimize_ea_query(self, entity: str, attribute: str) -> str:
        """Create optimized query key for entity-attribute searches.

        Args:
            entity: Entity name
            attribute: Attribute name

        Returns:
            Optimized query key for caching
        """
        return f"ea:{entity}:{attribute}"

    @timed_query
    def cached_entity_query(self, entity: str) -> Set[str]:
        """Execute cached entity query.

        Args:
            entity: Entity to search for

        Returns:
            Set of fact hashes
        """
        query_key = self.optimize_entity_query(entity)

        # Check query cache first
        cached_result = self.perf.query_cache.get(query_key)
        if cached_result is not None:
            return cached_result

        # Execute query
        result = self.index_manager.query_by_entity(entity)

        # Cache result
        self.perf.query_cache.put(query_key, result)

        return result

    @timed_query
    def cached_attribute_query(self, attribute: str) -> Set[str]:
        """Execute cached attribute query.

        Args:
            attribute: Attribute to search for

        Returns:
            Set of fact hashes
        """
        query_key = self.optimize_attribute_query(attribute)

        cached_result = self.perf.query_cache.get(query_key)
        if cached_result is not None:
            return cached_result

        result = self.index_manager.query_by_attribute(attribute)
        self.perf.query_cache.put(query_key, result)

        return result

    @timed_query
    def cached_entity_attribute_query(self, entity: str, attribute: str) -> Set[str]:
        """Execute cached entity-attribute query.

        Args:
            entity: Entity name
            attribute: Attribute name

        Returns:
            Set of fact hashes
        """
        query_key = self.optimize_ea_query(entity, attribute)

        cached_result = self.perf.query_cache.get(query_key)
        if cached_result is not None:
            return cached_result

        result = self.index_manager.query_by_entity_attribute(entity, attribute)
        self.perf.query_cache.put(query_key, result)

        return result

    def invalidate_entity_cache(self, entity: str) -> None:
        """Invalidate cached queries for an entity.

        Args:
            entity: Entity that was modified
        """
        # Invalidate entity-specific queries
        entity_key = self.optimize_entity_query(entity)
        self.perf.query_cache.invalidate_pattern(entity_key)

        # Invalidate entity-attribute queries
        self.perf.query_cache.invalidate_pattern(f"ea:{entity}:")


class MemoryIndex:
    """Main indexing interface combining all indexing components."""

    def __init__(
        self,
        fact_cache_size: int = 2000,
        object_cache_size: int = 1000,
        query_cache_size: int = 500,
    ):
        """Initialize memory index.

        Args:
            fact_cache_size: Size of fact cache
            object_cache_size: Size of object cache
            query_cache_size: Size of query cache
        """
        self.performance_layer = PerformanceLayer(
            fact_cache_size=fact_cache_size,
            object_cache_size=object_cache_size,
            query_cache_size=query_cache_size,
        )
        self.index_manager = FactIndexManager(self.performance_layer)
        self.query_optimizer = QueryOptimizer(self.index_manager)

    def add_fact(self, fact: Fact, fact_hash: str) -> None:
        """Add fact to index with cache invalidation.

        Args:
            fact: Fact to add
            fact_hash: Hash of the fact
        """
        self.index_manager.add_fact(fact, fact_hash)
        self.query_optimizer.invalidate_entity_cache(fact.entity)

    def remove_fact(self, fact: Fact, fact_hash: str) -> None:
        """Remove fact from index with cache invalidation.

        Args:
            fact: Fact to remove
            fact_hash: Hash of the fact
        """
        self.index_manager.remove_fact(fact, fact_hash)
        self.query_optimizer.invalidate_entity_cache(fact.entity)

    def find_facts_by_entity(self, entity: str) -> Set[str]:
        """Find facts by entity using optimized caching.

        Args:
            entity: Entity to search for

        Returns:
            Set of fact hashes
        """
        return self.query_optimizer.cached_entity_query(entity)

    def find_facts_by_attribute(self, attribute: str) -> Set[str]:
        """Find facts by attribute using optimized caching.

        Args:
            attribute: Attribute to search for

        Returns:
            Set of fact hashes
        """
        return self.query_optimizer.cached_attribute_query(attribute)

    def find_facts_by_entity_attribute(self, entity: str, attribute: str) -> Set[str]:
        """Find facts by entity-attribute pair using optimized caching.

        Args:
            entity: Entity name
            attribute: Attribute name

        Returns:
            Set of fact hashes
        """
        return self.query_optimizer.cached_entity_attribute_query(entity, attribute)

    def get_fact(self, fact_hash: str) -> Optional[Fact]:
        """Get fact from cache.

        Args:
            fact_hash: Hash of the fact

        Returns:
            Fact object or None if not found
        """
        return self.index_manager.get_fact(fact_hash)

    def detect_conflicts_for_fact(
        self, new_fact: Fact, existing_facts: List[Tuple[str, Fact]]
    ) -> List[Tuple[str, ConflictType]]:
        """Detect conflicts for a fact using optimized lookups.

        Args:
            new_fact: New fact to check
            existing_facts: Existing facts to check against

        Returns:
            List of conflicting fact hashes and conflict types
        """
        return self.index_manager.detect_conflicts_for_fact(new_fact, existing_facts)

    def get_statistics(self) -> Dict[str, any]:
        """Get comprehensive index statistics.

        Returns:
            Statistics dictionary
        """
        return self.index_manager.get_index_statistics()

    def clear_caches(self) -> None:
        """Clear all caches for debugging/testing."""
        self.performance_layer.clear_all_caches()

# Performance optimization enhancements