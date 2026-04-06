"""Enhanced tokenization for Memora search with basic stemming."""

import re
from typing import list, set

# Common English stop words
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "will",
    "with",
    "the",
    "this",
    "but",
    "they",
    "have",
    "had",
    "what",
    "said",
    "each",
    "which",
    "their",
    "time",
    "would",
    "there",
    "we",
    "when",
    "your",
    "can",
    "said",
    "get",
    "may",
    "use",
    "her",
    "than",
    "call",
    "who",
    "did",
    "its",
    "now",
    "find",
    "long",
    "down",
    "way",
    "been",
    "could",
    "people",
    "my",
    "made",
}


def basic_stem(word: str) -> str:
    """Apply basic stemming rules to reduce word variations."""
    word = word.lower()

    # Handle common suffixes
    if len(word) > 4:
        # Remove -ing, -ed, -er, -est, -ly, -tion, -ness, -ment
        if word.endswith("ing") and len(word) > 6:
            word = word[:-3]
        elif word.endswith("ed") and len(word) > 5:
            word = word[:-2]
        elif word.endswith("er") and len(word) > 5:
            word = word[:-2]
        elif word.endswith("est") and len(word) > 6:
            word = word[:-3]
        elif word.endswith("ly") and len(word) > 5:
            word = word[:-2]
        elif word.endswith("tion") and len(word) > 7:
            word = word[:-4] + "t"  # conversion -> convert
        elif word.endswith("ness") and len(word) > 7:
            word = word[:-4]
        elif word.endswith("ment") and len(word) > 7:
            word = word[:-4]
        elif word.endswith("ies") and len(word) > 6:
            word = word[:-3] + "y"  # studies -> study
        elif word.endswith("s") and len(word) > 4:
            word = word[:-1]  # removes plural -s

    return word


def enhanced_tokenize(text: str, enable_stemming: bool = True) -> list[str]:
    """Enhanced tokenization with optional stemming."""
    if not text:
        return []

    # Convert to lowercase and split on word boundaries
    text = text.lower()

    # Extract alphanumeric tokens (preserving programming terms like "python3", "c++")
    tokens = re.findall(r"\b[a-zA-Z0-9][a-zA-Z0-9_\-\+]*[a-zA-Z0-9]\b|\b[a-zA-Z]+\b", text)

    # Filter out stop words and very short tokens
    filtered_tokens = []
    for token in tokens:
        if len(token) >= 2 and token not in STOP_WORDS:
            if enable_stemming:
                token = basic_stem(token)
            filtered_tokens.append(token)

    return filtered_tokens


def tokenize_for_search(query: str) -> list[str]:
    """Tokenize search queries with stemming enabled."""
    return enhanced_tokenize(query, enable_stemming=True)


def tokenize_for_indexing(content: str) -> set[str]:
    """Tokenize content for indexing (returns unique tokens)."""
    tokens = enhanced_tokenize(content, enable_stemming=True)
    return set(tokens)  # Remove duplicates


def calculate_token_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts based on shared tokens."""
    tokens1 = set(enhanced_tokenize(text1))
    tokens2 = set(enhanced_tokenize(text2))

    if not tokens1 and not tokens2:
        return 1.0
    if not tokens1 or not tokens2:
        return 0.0

    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))

    return intersection / union if union > 0 else 0.0
