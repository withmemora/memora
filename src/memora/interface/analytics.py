"""Memory analytics and advanced query features.

This module provides advanced analytics for memory organization:
- Topic extraction and clustering
- Time-based analytics
- Memory growth tracking
- Conflict analysis
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from memora.shared.models import Fact, ContentType
from memora.core.store import ObjectStore


class MemoryAnalytics:
    """Advanced analytics for memory data."""

    def __init__(self, store: ObjectStore):
        """Initialize analytics.

        Args:
            store: ObjectStore instance
        """
        self.store = store

    def get_topics(self, limit: int = 20) -> List[Dict[str, any]]:
        """Extract top topics from memories.

        Topics are derived from entity and attribute combinations.

        Args:
            limit: Maximum number of topics to return

        Returns:
            List of topic dictionaries with counts
        """
        topic_counts = defaultdict(int)

        # Get all facts
        all_hashes = self.store.list_all_hashes()

        for fact_hash in all_hashes:
            try:
                fact = self.store.read_fact(fact_hash)
                # Create topic from entity + attribute
                topic = f"{fact.entity}/{fact.attribute}"
                topic_counts[topic] += 1
            except Exception:
                continue

        # Sort by count and return top N
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

        return [
            {
                "topic": topic,
                "count": count,
                "entity": topic.split("/")[0] if "/" in topic else topic,
                "attribute": topic.split("/")[1] if "/" in topic else "",
            }
            for topic, count in sorted_topics
        ]

    def get_memory_timeline(self, days: int = 30, granularity: str = "day") -> List[Dict[str, any]]:
        """Get memory extraction timeline.

        Args:
            days: Number of days to look back
            granularity: Time granularity ("hour", "day", "week")

        Returns:
            List of timeline entries with counts
        """
        now = datetime.utcnow()
        start_time = now - timedelta(days=days)

        # Initialize buckets
        timeline = defaultdict(int)

        # Get all facts
        all_hashes = self.store.list_all_hashes()

        for fact_hash in all_hashes:
            try:
                fact = self.store.read_fact(fact_hash)

                # Skip facts outside time range
                if fact.observed_at < start_time:
                    continue

                # Bucket by granularity
                if granularity == "hour":
                    bucket_key = fact.observed_at.strftime("%Y-%m-%d %H:00")
                elif granularity == "week":
                    # Get ISO week number
                    bucket_key = fact.observed_at.strftime("%Y-W%W")
                else:  # day
                    bucket_key = fact.observed_at.strftime("%Y-%m-%d")

                timeline[bucket_key] += 1

            except Exception:
                continue

        # Convert to sorted list
        sorted_timeline = sorted(timeline.items())

        return [{"time": time_key, "count": count} for time_key, count in sorted_timeline]

    def get_content_type_distribution(self) -> Dict[str, int]:
        """Get distribution of content types.

        Returns:
            Dictionary mapping content type to count
        """
        distribution = defaultdict(int)

        # Get all facts
        all_hashes = self.store.list_all_hashes()

        for fact_hash in all_hashes:
            try:
                fact = self.store.read_fact(fact_hash)
                distribution[fact.content_type.value] += 1
            except Exception:
                continue

        return dict(distribution)

    def get_source_statistics(self) -> List[Dict[str, any]]:
        """Get statistics by source.

        Returns:
            List of source statistics
        """
        source_counts = defaultdict(int)

        # Get all facts
        all_hashes = self.store.list_all_hashes()

        for fact_hash in all_hashes:
            try:
                fact = self.store.read_fact(fact_hash)
                # Extract source type (before colon if present)
                source_type = fact.source.split(":")[0]
                source_counts[source_type] += 1
            except Exception:
                continue

        # Sort by count
        sorted_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)

        return [{"source": source, "count": count} for source, count in sorted_sources]

    def get_confidence_distribution(self, bins: int = 5) -> List[Dict[str, any]]:
        """Get distribution of confidence scores.

        Args:
            bins: Number of bins for histogram

        Returns:
            List of confidence bin statistics
        """
        bin_size = 1.0 / bins
        bin_counts = defaultdict(int)

        # Get all facts
        all_hashes = self.store.list_all_hashes()

        for fact_hash in all_hashes:
            try:
                fact = self.store.read_fact(fact_hash)
                # Determine bin
                bin_index = min(int(fact.confidence / bin_size), bins - 1)
                bin_range = f"{bin_index * bin_size:.2f}-{(bin_index + 1) * bin_size:.2f}"
                bin_counts[bin_range] += 1
            except Exception:
                continue

        # Sort by bin range
        sorted_bins = sorted(bin_counts.items())

        return [{"confidence_range": bin_range, "count": count} for bin_range, count in sorted_bins]

    def search_by_topic_and_time(
        self,
        topic: Optional[str] = None,
        entity: Optional[str] = None,
        attribute: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Fact]:
        """Advanced search with multiple filters.

        Args:
            topic: Topic path (e.g., "user/name")
            entity: Entity name
            attribute: Attribute name
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum results

        Returns:
            List of matching facts
        """
        matching_facts = []

        # Get all facts
        all_hashes = self.store.list_all_hashes()

        for fact_hash in all_hashes:
            try:
                fact = self.store.read_fact(fact_hash)

                # Apply filters
                if topic:
                    expected_topic = f"{fact.entity}/{fact.attribute}"
                    if expected_topic.lower() != topic.lower():
                        continue

                if entity and fact.entity.lower() != entity.lower():
                    continue

                if attribute and fact.attribute.lower() != attribute.lower():
                    continue

                if start_time and fact.observed_at < start_time:
                    continue

                if end_time and fact.observed_at > end_time:
                    continue

                matching_facts.append(fact)

                # Limit results
                if len(matching_facts) >= limit:
                    break

            except Exception:
                continue

        return matching_facts

    def get_entity_summary(self, entity: str) -> Dict[str, any]:
        """Get summary statistics for an entity.

        Args:
            entity: Entity name

        Returns:
            Dictionary with entity statistics
        """
        entity_facts = []
        attributes = set()
        earliest = None
        latest = None

        # Get all facts
        all_hashes = self.store.list_all_hashes()

        for fact_hash in all_hashes:
            try:
                fact = self.store.read_fact(fact_hash)

                if fact.entity.lower() == entity.lower():
                    entity_facts.append(fact)
                    attributes.add(fact.attribute)

                    if earliest is None or fact.observed_at < earliest:
                        earliest = fact.observed_at

                    if latest is None or fact.observed_at > latest:
                        latest = fact.observed_at

            except Exception:
                continue

        return {
            "entity": entity,
            "total_facts": len(entity_facts),
            "unique_attributes": len(attributes),
            "attributes": sorted(list(attributes)),
            "earliest_fact": earliest.isoformat() if earliest else None,
            "latest_fact": latest.isoformat() if latest else None,
        }

    def get_memory_growth_rate(self, days: int = 30) -> Dict[str, any]:
        """Calculate memory growth rate.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with growth statistics
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(days=days)

        recent_count = 0
        total_count = 0

        # Get all facts
        all_hashes = self.store.list_all_hashes()

        for fact_hash in all_hashes:
            try:
                fact = self.store.read_fact(fact_hash)
                total_count += 1

                if fact.observed_at >= cutoff:
                    recent_count += 1

            except Exception:
                continue

        # Calculate rate
        facts_per_day = recent_count / days if days > 0 else 0

        return {
            "total_facts": total_count,
            "recent_facts": recent_count,
            "days_analyzed": days,
            "facts_per_day": round(facts_per_day, 2),
            "projected_monthly": round(facts_per_day * 30, 0),
        }
