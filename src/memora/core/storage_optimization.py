# Memory-optimized fact storage
"""
Optimized storage formats to reduce memory overhead while maintaining functionality.
"""

import json
import zlib
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from ..shared.models import Fact, ContentType


@dataclass
class CompactFact:
    """Memory-optimized fact representation."""

    # Core fields (required)
    e: str  # entity (shortened)
    a: str  # attribute (shortened)
    v: str  # value (shortened)
    c: float  # confidence (shortened)
    t: int  # timestamp as unix timestamp (shortened)

    # Optional fields (only stored if different from defaults)
    ct: Optional[int] = None  # content_type as int (0=PLAIN_TEXT, 1=TRIPLE, etc)
    s: Optional[str] = None  # source (shortened)
    fc: Optional[str] = None  # full_content (shortened) - only if different from value

    def to_fact(self) -> Fact:
        """Convert back to full Fact object."""
        content_types = [
            ContentType.PLAIN_TEXT,
            ContentType.TRIPLE,
            ContentType.DATE_VALUE,
            ContentType.PREFERENCE,
        ]

        return Fact(
            content=self.fc or self.v,  # Use full content or fallback to value
            content_type=content_types[self.ct] if self.ct is not None else ContentType.PLAIN_TEXT,
            entity=self.e,
            attribute=self.a,
            value=self.v,
            source=self.s or "unknown",
            observed_at=datetime.fromtimestamp(self.t),
            confidence=self.c,
        )

    @classmethod
    def from_fact(cls, fact: Fact) -> "CompactFact":
        """Create compact fact from full fact."""
        content_type_map = {
            ContentType.PLAIN_TEXT: 0,
            ContentType.TRIPLE: 1,
            ContentType.DATE_VALUE: 2,
            ContentType.PREFERENCE: 3,
        }

        # Only store full content if it differs significantly from value
        full_content = None
        if fact.content != fact.value and len(fact.content) > len(fact.value) * 1.2:
            full_content = fact.content

        return cls(
            e=fact.entity,
            a=fact.attribute,
            v=fact.value,
            c=fact.confidence,
            t=int(fact.observed_at.timestamp()),
            ct=content_type_map.get(fact.content_type, 0)
            if fact.content_type != ContentType.PLAIN_TEXT
            else None,
            s=fact.source if fact.source != "unknown" else None,
            fc=full_content,
        )


class OptimizedFactStorage:
    """Optimized storage layer for facts with compression and deduplication."""

    def __init__(self):
        # String interning for common values
        self.entity_intern: Dict[str, int] = {}
        self.attribute_intern: Dict[str, int] = {}
        self.source_intern: Dict[str, int] = {}
        self.next_intern_id = 1

        # Compression stats
        self.compression_stats = {"original_size": 0, "compressed_size": 0, "facts_stored": 0}

    def store_fact_optimized(self, fact: Fact) -> Tuple[str, bytes]:
        """Store fact with maximum compression."""
        # Create compact representation
        compact = CompactFact.from_fact(fact)

        # Apply string interning for common fields
        compact.e = self._intern_string(compact.e, self.entity_intern)
        compact.a = self._intern_string(compact.a, self.attribute_intern)
        if compact.s:
            compact.s = self._intern_string(compact.s, self.source_intern)

        # Serialize to compact JSON
        data = {"e": compact.e, "a": compact.a, "v": compact.v, "c": compact.c, "t": compact.t}

        # Only add optional fields if they exist
        if compact.ct is not None:
            data["ct"] = compact.ct
        if compact.s is not None:
            data["s"] = compact.s
        if compact.fc is not None:
            data["fc"] = compact.fc

        # Compact JSON (no spaces)
        json_bytes = json.dumps(data, separators=(",", ":")).encode("utf-8")

        # Compress with zlib
        compressed = zlib.compress(json_bytes, level=9)  # Max compression

        # Update stats
        self.compression_stats["original_size"] += len(json_bytes)
        self.compression_stats["compressed_size"] += len(compressed)
        self.compression_stats["facts_stored"] += 1

        # Generate hash from original fact (for consistency)
        fact_hash = fact.compute_hash()

        return fact_hash, compressed

    def load_fact_optimized(self, compressed_data: bytes) -> Fact:
        """Load and decompress fact."""
        # Decompress
        json_bytes = zlib.decompress(compressed_data)
        data = json.loads(json_bytes.decode("utf-8"))

        # Reverse string interning
        data["e"] = self._reverse_intern(data["e"], self.entity_intern)
        data["a"] = self._reverse_intern(data["a"], self.attribute_intern)
        if "s" in data:
            data["s"] = self._reverse_intern(data["s"], self.source_intern)

        # Reconstruct compact fact
        compact = CompactFact(**data)

        # Convert back to full fact
        return compact.to_fact()

    def _intern_string(self, string: str, intern_dict: Dict[str, int]) -> str:
        """Intern common strings to reduce storage."""
        if len(string) < 8:  # Don't intern very short strings
            return string

        if string in intern_dict:
            return f"@{intern_dict[string]}"  # Reference to interned string
        else:
            intern_dict[string] = self.next_intern_id
            result = f"@{self.next_intern_id}"
            self.next_intern_id += 1
            return result

    def _reverse_intern(self, value: str, intern_dict: Dict[str, int]) -> str:
        """Reverse string interning."""
        if not value.startswith("@"):
            return value

        intern_id = int(value[1:])
        for string, id_val in intern_dict.items():
            if id_val == intern_id:
                return string
        return value  # Fallback if not found

    def get_compression_ratio(self) -> float:
        """Get current compression ratio."""
        if self.compression_stats["original_size"] == 0:
            return 1.0
        return self.compression_stats["compressed_size"] / self.compression_stats["original_size"]

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get detailed storage statistics."""
        ratio = self.get_compression_ratio()
        savings = (1 - ratio) * 100

        return {
            "facts_stored": self.compression_stats["facts_stored"],
            "original_size_bytes": self.compression_stats["original_size"],
            "compressed_size_bytes": self.compression_stats["compressed_size"],
            "compression_ratio": f"{ratio:.2f}",
            "space_savings_percent": f"{savings:.1f}%",
            "interned_entities": len(self.entity_intern),
            "interned_attributes": len(self.attribute_intern),
            "interned_sources": len(self.source_intern),
        }


def analyze_storage_efficiency(facts: List[Fact]) -> Dict[str, Any]:
    """Analyze storage efficiency for a collection of facts."""
    original_storage = OptimizedFactStorage()

    total_original_size = 0
    total_optimized_size = 0

    for fact in facts:
        # Calculate original size (full JSON)
        original_dict = {
            "content": fact.content,
            "content_type": fact.content_type.value,
            "entity": fact.entity,
            "attribute": fact.attribute,
            "value": fact.value,
            "source": fact.source,
            "observed_at": fact.observed_at.isoformat(),
            "confidence": fact.confidence,
        }
        original_json = json.dumps(original_dict, separators=(",", ":")).encode("utf-8")
        total_original_size += len(original_json)

        # Calculate optimized size
        _, optimized_data = original_storage.store_fact_optimized(fact)
        total_optimized_size += len(optimized_data)

    compression_ratio = (
        total_optimized_size / total_original_size if total_original_size > 0 else 1.0
    )
    space_savings = (1 - compression_ratio) * 100

    return {
        "total_facts": len(facts),
        "original_size_bytes": total_original_size,
        "optimized_size_bytes": total_optimized_size,
        "compression_ratio": compression_ratio,
        "space_savings_percent": space_savings,
        "average_original_size": total_original_size / len(facts) if facts else 0,
        "average_optimized_size": total_optimized_size / len(facts) if facts else 0,
    }


# Example usage and testing
def test_storage_optimization():
    """Test storage optimization with realistic data."""
    from ..shared.models import ContentType

    # Create sample facts
    facts = [
        Fact(
            content="My deadline is March 31st for the AI project",
            content_type=ContentType.PLAIN_TEXT,
            entity="current_project",
            attribute="deadline",
            value="March 31st",
            source="conversation:session-001:message-15",
            observed_at=datetime.utcnow(),
            confidence=0.90,
        ),
        Fact(
            content="My name is Arun Kumar",
            content_type=ContentType.PLAIN_TEXT,
            entity="user",
            attribute="name",
            value="Arun Kumar",
            source="conversation:session-001:message-3",
            observed_at=datetime.utcnow(),
            confidence=0.95,
        ),
        Fact(
            content="I am building Memora for FOSS HACK 26",
            content_type=ContentType.PLAIN_TEXT,
            entity="user",
            attribute="current_project",
            value="Memora",
            source="conversation:session-001:message-3",
            observed_at=datetime.utcnow(),
            confidence=0.88,
        ),
    ]

    # Analyze efficiency
    stats = analyze_storage_efficiency(facts)

    print("Storage Optimization Analysis:")
    print(f"Facts: {stats['total_facts']}")
    print(f"Original size: {stats['original_size_bytes']} bytes")
    print(f"Optimized size: {stats['optimized_size_bytes']} bytes")
    print(f"Compression ratio: {stats['compression_ratio']:.2f}")
    print(f"Space savings: {stats['space_savings_percent']:.1f}%")
    print(
        f"Average fact size: {stats['average_original_size']:.1f} → {stats['average_optimized_size']:.1f} bytes"
    )

    return stats


if __name__ == "__main__":
    test_storage_optimization()

# Storage compression improvements