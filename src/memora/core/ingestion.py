"""NLP ingestion pipeline for extracting facts from natural language text.

This module implements a 5-stage pipeline:
  1. Normalize text (strip, validate UTF-8, split sentences)
  2. Run spaCy NER (Named Entity Recognition)
  3. Apply custom Matcher rules for first-person patterns
  4. Assign confidence scores
  5. Deduplicate by hash
"""

import re
from datetime import datetime, timezone
from typing import Any

import spacy
from spacy.tokens import Doc

from memora.shared.models import ContentType, Fact
from memora.core.advanced_extraction import extract_advanced_facts


def extract_facts(
    text: str, source: str = "conversation", nlp_model: str = "en_core_web_sm"
) -> list[Fact]:
    """Extract facts from natural language text.

    Pipeline:
      1. Normalize text (strip, validate UTF-8)
      2. Load spaCy model
      3. Run basic custom patterns (high confidence)
      4. Run NER extraction (medium confidence)
      5. Run advanced extraction (contextual, relationships)
      6. Assign confidence scores
      7. Deduplicate by hash

    Args:
        text: Natural language text to analyze
        source: Provenance string (e.g., "conversation:session-001")
        nlp_model: spaCy model name (default: en_core_web_sm)

    Returns:
        List of extracted Fact objects
    """
    # Stage 1: Normalize text
    sentences = normalize_text(text)
    if not sentences:
        return []

    # Stage 2: Load spaCy model
    nlp = spacy.load(nlp_model)

    # Stage 3-5: Process each sentence
    all_facts: list[Fact] = []

    for sentence in sentences:
        doc = nlp(sentence)

        # Apply custom Matcher rules (high confidence)
        custom_facts = apply_custom_rules(nlp, doc, sentence, source)
        all_facts.extend(custom_facts)

        # Extract from NER entities (medium confidence)
        entity_facts = extract_from_entities(doc, sentence, source)
        all_facts.extend(entity_facts)

    # Stage 6: Advanced extraction on full text
    advanced_facts = extract_advanced_facts(text, source, nlp_model)
    all_facts.extend(advanced_facts)

    # Stage 6.5: Extract code snippets
    code_facts = extract_code_facts(text, source)
    all_facts.extend(code_facts)

    # Stage 7: Deduplicate by hash
    seen_hashes: set[str] = set()
    unique_facts: list[Fact] = []

    for fact in all_facts:
        fact_hash = fact.compute_hash()
        if fact_hash not in seen_hashes:
            seen_hashes.add(fact_hash)
            unique_facts.append(fact)

    return unique_facts


def normalize_text(text: str) -> list[str]:
    """Normalize and split text into sentences.

    Args:
        text: Raw input text

    Returns:
        List of normalized sentences
    """
    # Strip whitespace
    text = text.strip()

    # Validate UTF-8 (Python strings are already UTF-8)
    if not text:
        return []

    # Use spaCy for sentence splitting (more accurate than simple split)
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)

    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    return sentences


def apply_custom_rules(nlp: Any, doc: Doc, sentence: str, source: str) -> list[Fact]:
    """Apply custom Matcher rules for first-person patterns.

    Rules (from CLAUDE.md):
      - "My name is X" → (user, name, X, confidence=0.95)
      - "I am X" / "I'm X" → (user, identity, X, confidence=0.95)
      - "I live in X" → (user, location, X, confidence=0.92)
      - "My email is X" → (user, email, X, confidence=0.95)
      - "I work at X" → (user, employer, X, confidence=0.95)
      - "The deadline is X" → (current_project, deadline, X, confidence=0.90)
      - "I prefer X" → (user, preference, X, confidence=0.90)
      - "My project is X" → (user, current_project, X, confidence=0.88)
      - "I am building X" → (user, current_project, X, confidence=0.88)
      - "X is my goal" → (user, goal, X, confidence=0.88)

    Args:
        nlp: spaCy language model
        doc: spaCy Doc object
        sentence: Original sentence text
        source: Provenance string

    Returns:
        List of extracted Fact objects
    """
    facts: list[Fact] = []
    observed_at = datetime.now(timezone.utc)

    # Use pattern matching approach to reduce complexity
    pattern_rules = _get_pattern_rules()

    for rule in pattern_rules:
        fact = _apply_pattern_rule(rule, sentence, source, observed_at)
        if fact:
            facts.append(fact)

    return facts


def _get_pattern_rules() -> list[dict]:
    """Get all pattern rules for fact extraction."""
    return [
        {
            "pattern": r"\bmy\s+name\s+is\s+",
            "extract_pattern": r"\bmy\s+name\s+is\s+(.+?)(?:[.!?]|$)",
            "entity": "user",
            "attribute": "name",
            "content_type": ContentType.TRIPLE,
            "confidence": 0.95,
        },
        {
            "pattern": r"\bi\s+am\s+",
            "exclude_pattern": r"\bi\s+am\s+building\b",
            "extract_pattern": r"\bi\s+am\s+(.+?)(?:[.!?]|$)",
            "entity": "user",
            "attribute": "identity",
            "content_type": ContentType.TRIPLE,
            "confidence": 0.95,
        },
        {
            "pattern": r"\bi'm\s+",
            "exclude_pattern": r"\bi'm\s+building\b",
            "extract_pattern": r"\bi'm\s+(.+?)(?:[.!?]|$)",
            "entity": "user",
            "attribute": "identity",
            "content_type": ContentType.TRIPLE,
            "confidence": 0.95,
        },
        {
            "pattern": r"\bi\s+live\s+in\s+",
            "extract_pattern": r"\bi\s+live\s+in\s+(.+?)(?:[.!?]|$)",
            "entity": "user",
            "attribute": "location",
            "content_type": ContentType.TRIPLE,
            "confidence": 0.92,
        },
        {
            "pattern": r"\bmy\s+email\s+is\s+",
            "extract_pattern": r"\bmy\s+email\s+is\s+(\S+@\S+\.\S+)",
            "entity": "user",
            "attribute": "email",
            "content_type": ContentType.TRIPLE,
            "confidence": 0.95,
        },
        {
            "pattern": r"\bi\s+work\s+at\s+",
            "extract_pattern": r"\bi\s+work\s+at\s+(.+?)(?:[.!?]|$)",
            "entity": "user",
            "attribute": "employer",
            "content_type": ContentType.TRIPLE,
            "confidence": 0.95,
        },
        {
            "pattern": r"\bthe\s+deadline\s+is\s+",
            "extract_pattern": r"\bthe\s+deadline\s+is\s+(.+?)(?:[.!?]|$)",
            "entity": "current_project",
            "attribute": "deadline",
            "content_type": ContentType.DATE_VALUE,
            "confidence": 0.90,
        },
        {
            "pattern": r"\bi\s+prefer\s+",
            "extract_pattern": r"\bi\s+prefer\s+(.+?)(?:[.!?]|$)",
            "entity": "user",
            "attribute": "preference",
            "content_type": ContentType.PREFERENCE,
            "confidence": 0.90,
        },
        {
            "pattern": r"\bmy\s+project\s+is\s+",
            "extract_pattern": r"\bmy\s+project\s+is\s+(.+?)(?:[.!?]|$)",
            "entity": "user",
            "attribute": "current_project",
            "content_type": ContentType.TRIPLE,
            "confidence": 0.88,
        },
        {
            "pattern": r"\bi\s+am\s+building\s+",
            "extract_pattern": r"\bi\s+am\s+building\s+(.+?)(?:[.!?]|$)",
            "entity": "user",
            "attribute": "current_project",
            "content_type": ContentType.TRIPLE,
            "confidence": 0.88,
        },
        {
            "pattern": r"\bi'm\s+building\s+",
            "extract_pattern": r"\bi'm\s+building\s+(.+?)(?:[.!?]|$)",
            "entity": "user",
            "attribute": "current_project",
            "content_type": ContentType.TRIPLE,
            "confidence": 0.88,
        },
        {
            "pattern": r"\bis\s+my\s+goal",
            "extract_pattern": r"^(.+?)\s+is\s+my\s+goal",
            "entity": "user",
            "attribute": "goal",
            "content_type": ContentType.TRIPLE,
            "confidence": 0.88,
        },
        {
            "pattern": r"\bis\s+a\s+project\b",
            "extract_pattern": r"^([A-Z][a-zA-Z]+)\s+is\s+a\s+project",
            "entity": "user",
            "attribute": "current_project",
            "content_type": ContentType.TRIPLE,
            "confidence": 0.85,
        },
        {
            "pattern": r"\bis\s+a\s+\w+\s+app\b",
            "extract_pattern": r"^([A-Z][a-zA-Z]+)\s+is\s+a\s+[\w\s]+app",
            "entity": "user",
            "attribute": "current_project",
            "content_type": ContentType.TRIPLE,
            "confidence": 0.85,
        },
    ]


def _apply_pattern_rule(
    rule: dict, sentence: str, source: str, observed_at: datetime
) -> Fact | None:
    """Apply a single pattern rule and return a Fact if matched."""
    import re

    sentence_lower = sentence.lower()

    # Check if pattern matches
    if not re.search(rule["pattern"], sentence_lower):
        return None

    # Check if exclude pattern matches (for rules that have exclusions)
    if "exclude_pattern" in rule and re.search(rule["exclude_pattern"], sentence_lower):
        return None

    # Extract the value using the extraction pattern
    match = re.search(rule["extract_pattern"], sentence, re.IGNORECASE)
    if not match:
        return None

    value = match.group(1).strip()
    if not value:
        return None

    return Fact(
        content=sentence,
        content_type=rule["content_type"],
        entity=rule["entity"],
        attribute=rule["attribute"],
        value=value,
        source=source,
        observed_at=observed_at,
        confidence=rule["confidence"],
    )


def extract_from_entities(doc: Doc, sentence: str, source: str) -> list[Fact]:
    """Extract facts from spaCy NER entities.

    Args:
        doc: spaCy Doc object
        sentence: Original sentence text
        source: Provenance string

    Returns:
        List of extracted Fact objects
    """
    facts: list[Fact] = []
    observed_at = datetime.now(timezone.utc)

    for ent in doc.ents:
        # Map spaCy entity types to our attributes
        if ent.label_ == "PERSON":
            # Third-party mention of a person
            facts.append(
                Fact(
                    content=sentence,
                    content_type=ContentType.TRIPLE,
                    entity=ent.text.lower().replace(" ", "_"),
                    attribute="entity_type",
                    value="person",
                    source=source,
                    observed_at=observed_at,
                    confidence=0.85,
                )
            )

        elif ent.label_ == "ORG":
            # Organization mention
            facts.append(
                Fact(
                    content=sentence,
                    content_type=ContentType.TRIPLE,
                    entity=ent.text.lower().replace(" ", "_"),
                    attribute="entity_type",
                    value="organization",
                    source=source,
                    observed_at=observed_at,
                    confidence=0.85,
                )
            )

        elif ent.label_ == "GPE":  # Geo-political entity (city, country)
            facts.append(
                Fact(
                    content=sentence,
                    content_type=ContentType.TRIPLE,
                    entity="mentioned_location",
                    attribute="name",
                    value=ent.text,
                    source=source,
                    observed_at=observed_at,
                    confidence=0.85,
                )
            )

        elif ent.label_ == "DATE":
            # Date mention (could be deadline, birthday, etc.)
            facts.append(
                Fact(
                    content=sentence,
                    content_type=ContentType.DATE_VALUE,
                    entity="mentioned_date",
                    attribute="value",
                    value=ent.text,
                    source=source,
                    observed_at=observed_at,
                    confidence=0.70,  # Lower confidence - needs context
                )
            )

    return facts


def normalize_attribute(attr: str) -> str:
    """Normalize attribute aliases to canonical names.

    Aliases (from CLAUDE.md):
      "email_address", "contact email" → "email"
      "full name", "full_name" → "name"
      "city", "address", "where i live" → "location"
      "due date", "due_date" → "deadline"
      "current project", "project" → "current_project"

    Args:
        attr: Attribute string to normalize

    Returns:
        Normalized attribute name
    """
    attr_lower = attr.lower().strip()

    # Email aliases
    if attr_lower in ["email_address", "contact email", "contact_email", "e-mail"]:
        return "email"

    # Name aliases
    if attr_lower in ["full name", "full_name", "fullname"]:
        return "name"

    # Location aliases
    if attr_lower in ["city", "address", "where i live", "place", "residence"]:
        return "location"

    # Deadline aliases
    if attr_lower in ["due date", "due_date", "duedate", "due"]:
        return "deadline"

    # Project aliases
    if attr_lower in ["current project", "project", "current_project"]:
        return "current_project"

    # Return as-is if no alias match
    return attr_lower


def assign_confidence(extraction_type: str) -> float:
    """Assign confidence score based on extraction type.

    Scores (from CLAUDE.md):
      - Direct first-person (Matcher): 0.95
      - Third-party about named entity: 0.85
      - Contextual inference: 0.60
      - Ambiguous parse: 0.45

    Args:
        extraction_type: Type of extraction method used

    Returns:
        Confidence score (0.0 to 1.0)
    """
    confidence_map = {
        "first_person_matcher": 0.95,
        "named_entity": 0.85,
        "contextual": 0.60,
        "ambiguous": 0.45,
    }

    return confidence_map.get(extraction_type, 0.45)  # Default to ambiguous


def extract_code_facts(text: str, source: str) -> list[Fact]:
    """Extract code snippets from text (for conversations with AI).

    Detects code blocks in various formats:
    - Triple backtick code blocks (```language ... ```)
    - Inline code (`code`)
    - Common code patterns

    Args:
        text: Text potentially containing code snippets
        source: Provenance string

    Returns:
        List of Fact objects representing code snippets
    """
    facts: list[Fact] = []
    observed_at = datetime.now(timezone.utc)

    # Extract code blocks with language specification
    code_block_pattern = r"```(\w+)?\n(.*?)\n```"
    code_blocks = re.findall(code_block_pattern, text, re.DOTALL)

    for i, (language, code) in enumerate(code_blocks):
        if code.strip():
            lang = language.lower() if language else "unknown"
            fact = Fact(
                content=text,
                content_type=ContentType.CODE_SNIPPET,
                entity="user_code",
                attribute=f"{lang}_code_block",
                value=code.strip(),
                source=source,
                observed_at=observed_at,
                confidence=0.90,
            )
            facts.append(fact)

    # Extract function definitions (Python-specific as main focus)
    python_func_pattern = r"def\s+(\w+)\s*\([^)]*\):"
    python_funcs = re.findall(python_func_pattern, text)

    for func_name in python_funcs:
        fact = Fact(
            content=text,
            content_type=ContentType.CODE_SNIPPET,
            entity="user_code",
            attribute="python_function",
            value=func_name,
            source=source,
            observed_at=observed_at,
            confidence=0.85,
        )
        facts.append(fact)

    # Extract class definitions (Python)
    python_class_pattern = r"class\s+(\w+)"
    python_classes = re.findall(python_class_pattern, text)

    for class_name in python_classes:
        fact = Fact(
            content=text,
            content_type=ContentType.CODE_SNIPPET,
            entity="user_code",
            attribute="python_class",
            value=class_name,
            source=source,
            observed_at=observed_at,
            confidence=0.85,
        )
        facts.append(fact)

    return facts


# Improved spaCy NLP processing
