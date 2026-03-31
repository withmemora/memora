"""Object serialization and hashing for Memora.

This module implements the canonical serialization protocol:
1. Object -> dict (via to_dict())
2. JSON with sorted keys (separators=(',',':'), sort_keys=True)
3. UTF-8 encoding
4. zlib compression (level 6)
5. SHA-256 hash

All objects in Memora follow this protocol for deterministic hashing
and content-addressable storage.
"""

import hashlib
import json
import zlib

from memora.shared.exceptions import HashMismatchError
from memora.shared.models import Fact, MemoryCommit, MemoryTree


def hash_bytes(data: bytes) -> str:
    """Compute SHA-256 hash of raw bytes.

    Args:
        data: Raw bytes to hash

    Returns:
        64-character hex string (SHA-256)
    """
    return hashlib.sha256(data).hexdigest()


def hash_object(obj_dict: dict) -> str:
    """Hash a dictionary using canonical JSON serialization.

    Sorts keys alphabetically, uses compact separators, encodes to UTF-8,
    then computes SHA-256. This ensures identical dicts always produce
    identical hashes regardless of key insertion order.

    Args:
        obj_dict: Dictionary to hash

    Returns:
        64-character hex string (SHA-256)
    """
    json_str = json.dumps(obj_dict, separators=(",", ":"), sort_keys=True)
    json_bytes = json_str.encode("utf-8")
    return hash_bytes(json_bytes)


def hash_fact(fact: Fact) -> str:
    """Compute hash of a Fact using only semantic identity fields.

    Hash is computed from: content_type + entity.lower() + attribute.lower() + value
    EXCLUDED: content, source, observed_at, confidence

    This means the same fact from different sources/times will have the same hash,
    enabling deduplication across sources.

    Args:
        fact: Fact object to hash

    Returns:
        64-character hex string (SHA-256)
    """
    # Build hash input from semantic identity fields only
    hash_input = (
        f"{fact.content_type.value}{fact.entity.lower()}{fact.attribute.lower()}{fact.value}"
    )
    return hash_bytes(hash_input.encode("utf-8"))


def serialize_fact(fact: Fact) -> tuple[bytes, str]:
    """Serialize a Fact to compressed bytes.

    Uses the canonical serialization protocol. The hash is computed
    using hash_fact() (semantic identity only), not hash_object().

    Args:
        fact: Fact to serialize

    Returns:
        Tuple of (compressed_bytes, hash_string)
    """
    # Convert to dict
    fact_dict = fact.to_dict()

    # Canonical JSON serialization
    json_str = json.dumps(fact_dict, separators=(",", ":"), sort_keys=True)
    json_bytes = json_str.encode("utf-8")

    # Compress with zlib level 6
    compressed = zlib.compress(json_bytes, level=6)

    # Compute hash from semantic identity fields only
    fact_hash = hash_fact(fact)

    return compressed, fact_hash


def serialize_tree(tree: MemoryTree) -> tuple[bytes, str]:
    """Serialize a MemoryTree to compressed bytes.

    Sorts entries by name before serializing to ensure deterministic output.

    Args:
        tree: MemoryTree to serialize

    Returns:
        Tuple of (compressed_bytes, hash_string)
    """
    # Convert to dict
    tree_dict = tree.to_dict()

    # Sort entries by name for determinism
    if "entries" in tree_dict:
        tree_dict["entries"] = sorted(tree_dict["entries"], key=lambda e: e["name"])

    # Canonical JSON serialization
    json_str = json.dumps(tree_dict, separators=(",", ":"), sort_keys=True)
    json_bytes = json_str.encode("utf-8")

    # Compress with zlib level 6
    compressed = zlib.compress(json_bytes, level=6)

    # Compute hash of compressed data
    tree_hash = hash_bytes(compressed)

    return compressed, tree_hash


def serialize_commit(commit: MemoryCommit) -> tuple[bytes, str]:
    """Serialize a MemoryCommit to compressed bytes.

    Args:
        commit: MemoryCommit to serialize

    Returns:
        Tuple of (compressed_bytes, hash_string)
    """
    # Convert to dict
    commit_dict = commit.to_dict()

    # Canonical JSON serialization
    json_str = json.dumps(commit_dict, separators=(",", ":"), sort_keys=True)
    json_bytes = json_str.encode("utf-8")

    # Compress with zlib level 6
    compressed = zlib.compress(json_bytes, level=6)

    # Compute hash of compressed data
    commit_hash = hash_bytes(compressed)

    return compressed, commit_hash


def deserialize_fact(data: bytes) -> Fact:
    """Deserialize compressed bytes back to a Fact object.

    Args:
        data: Compressed bytes (zlib)

    Returns:
        Reconstructed Fact object

    Raises:
        zlib.error: If decompression fails
        json.JSONDecodeError: If JSON parsing fails
    """
    # Decompress
    json_bytes = zlib.decompress(data)
    json_str = json_bytes.decode("utf-8")

    # Parse JSON
    fact_dict = json.loads(json_str)

    # Reconstruct Fact using from_dict
    return Fact.from_dict(fact_dict)


def deserialize_tree(data: bytes) -> MemoryTree:
    """Deserialize compressed bytes back to a MemoryTree object.

    Args:
        data: Compressed bytes (zlib)

    Returns:
        Reconstructed MemoryTree object

    Raises:
        zlib.error: If decompression fails
        json.JSONDecodeError: If JSON parsing fails
    """
    # Decompress
    json_bytes = zlib.decompress(data)
    json_str = json_bytes.decode("utf-8")

    # Parse JSON
    tree_dict = json.loads(json_str)

    # Reconstruct MemoryTree using from_dict
    return MemoryTree.from_dict(tree_dict)


def deserialize_commit(data: bytes) -> MemoryCommit:
    """Deserialize compressed bytes back to a MemoryCommit object.

    Args:
        data: Compressed bytes (zlib)

    Returns:
        Reconstructed MemoryCommit object

    Raises:
        zlib.error: If decompression fails
        json.JSONDecodeError: If JSON parsing fails
    """
    # Decompress
    json_bytes = zlib.decompress(data)
    json_str = json_bytes.decode("utf-8")

    # Parse JSON
    commit_dict = json.loads(json_str)

    # Reconstruct MemoryCommit using from_dict
    return MemoryCommit.from_dict(commit_dict)


def verify_hash(data: bytes, expected_hash: str) -> None:
    """Verify that compressed data matches expected hash.

    Recomputes SHA-256 of the data and compares to expected hash.
    This detects corruption or tampering.

    Args:
        data: Compressed bytes to verify
        expected_hash: Expected SHA-256 hash (64-char hex)

    Raises:
        HashMismatchError: If computed hash doesn't match expected
    """
    actual_hash = hash_bytes(data)

    if actual_hash != expected_hash:
        raise HashMismatchError(
            f"Hash mismatch: expected {expected_hash[:8]}..., got {actual_hash[:8]}..."
        )
