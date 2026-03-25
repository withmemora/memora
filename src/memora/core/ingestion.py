"""NLP ingestion pipeline for extracting facts from natural language text.

This module implements a 5-stage pipeline:
  1. Normalize text (strip, validate UTF-8, split sentences)
  2. Run spaCy NER (Named Entity Recognition)
  3. Apply custom Matcher rules for first-person patterns
  4. Assign confidence scores
  5. Deduplicate by hash
"""

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
    import re

    facts: list[Fact] = []
    observed_at = datetime.now(timezone.utc)
    sentence_lower = sentence.lower()

    # Rule 1: "My name is X" - extract everything after "is"
    if re.search(r"\bmy\s+name\s+is\s+", sentence_lower):
        match = re.search(r"\bmy\s+name\s+is\s+(.+?)(?:[.!?]|$)", sentence, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            facts.append(
                Fact(
                    content=sentence,
                    content_type=ContentType.TRIPLE,
                    entity="user",
                    attribute="name",
                    value=value,
                    source=source,
                    observed_at=observed_at,
                    confidence=0.95,
                )
            )

    # Rule 2: "I am X" / "I'm X" - extract everything after "am" or "I'm"
    if re.search(r"\bi\s+am\s+", sentence_lower) and not re.search(
        r"\bi\s+am\s+building\b", sentence_lower
    ):
        match = re.search(r"\bi\s+am\s+(.+?)(?:[.!?]|$)", sentence, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            facts.append(
                Fact(
                    content=sentence,
                    content_type=ContentType.TRIPLE,
                    entity="user",
                    attribute="identity",
                    value=value,
                    source=source,
                    observed_at=observed_at,
                    confidence=0.95,
                )
            )
    elif re.search(r"\bi'm\s+", sentence_lower) and not re.search(
        r"\bi'm\s+building\b", sentence_lower
    ):
        match = re.search(r"\bi'm\s+(.+?)(?:[.!?]|$)", sentence, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            facts.append(
                Fact(
                    content=sentence,
                    content_type=ContentType.TRIPLE,
                    entity="user",
                    attribute="identity",
                    value=value,
                    source=source,
                    observed_at=observed_at,
                    confidence=0.95,
                )
            )

    # Rule 3: "I live in X"
    if re.search(r"\bi\s+live\s+in\s+", sentence_lower):
        match = re.search(r"\bi\s+live\s+in\s+(.+?)(?:[.!?]|$)", sentence, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            facts.append(
                Fact(
                    content=sentence,
                    content_type=ContentType.TRIPLE,
                    entity="user",
                    attribute="location",
                    value=value,
                    source=source,
                    observed_at=observed_at,
                    confidence=0.92,
                )
            )

    # Rule 4: "My email is X"
    if re.search(r"\bmy\s+email\s+is\s+", sentence_lower):
        # Use specific email pattern instead of generic (.+?) to avoid stopping at .com
        match = re.search(r"\bmy\s+email\s+is\s+(\S+@\S+\.\S+)", sentence, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            facts.append(
                Fact(
                    content=sentence,
                    content_type=ContentType.TRIPLE,
                    entity="user",
                    attribute="email",
                    value=value,
                    source=source,
                    observed_at=observed_at,
                    confidence=0.95,
                )
            )

    # Rule 5: "I work at X"
    if re.search(r"\bi\s+work\s+at\s+", sentence_lower):
        match = re.search(r"\bi\s+work\s+at\s+(.+?)(?:[.!?]|$)", sentence, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            facts.append(
                Fact(
                    content=sentence,
                    content_type=ContentType.TRIPLE,
                    entity="user",
                    attribute="employer",
                    value=value,
                    source=source,
                    observed_at=observed_at,
                    confidence=0.95,
                )
            )

    # Rule 6: "The deadline is X"
    if re.search(r"\bthe\s+deadline\s+is\s+", sentence_lower):
        match = re.search(r"\bthe\s+deadline\s+is\s+(.+?)(?:[.!?]|$)", sentence, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            facts.append(
                Fact(
                    content=sentence,
                    content_type=ContentType.DATE_VALUE,
                    entity="current_project",
                    attribute="deadline",
                    value=value,
                    source=source,
                    observed_at=observed_at,
                    confidence=0.90,
                )
            )

    # Rule 7: "I prefer X"
    if re.search(r"\bi\s+prefer\s+", sentence_lower):
        match = re.search(r"\bi\s+prefer\s+(.+?)(?:[.!?]|$)", sentence, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            facts.append(
                Fact(
                    content=sentence,
                    content_type=ContentType.PREFERENCE,
                    entity="user",
                    attribute="preference",
                    value=value,
                    source=source,
                    observed_at=observed_at,
                    confidence=0.90,
                )
            )

    # Rule 8: "My project is X"
    if re.search(r"\bmy\s+project\s+is\s+", sentence_lower):
        match = re.search(r"\bmy\s+project\s+is\s+(.+?)(?:[.!?]|$)", sentence, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            facts.append(
                Fact(
                    content=sentence,
                    content_type=ContentType.TRIPLE,
                    entity="user",
                    attribute="current_project",
                    value=value,
                    source=source,
                    observed_at=observed_at,
                    confidence=0.88,
                )
            )

    # Rule 9: "I am building X" / "I'm building X"
    if re.search(r"\bi\s+am\s+building\s+", sentence_lower):
        match = re.search(r"\bi\s+am\s+building\s+(.+?)(?:[.!?]|$)", sentence, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            facts.append(
                Fact(
                    content=sentence,
                    content_type=ContentType.TRIPLE,
                    entity="user",
                    attribute="current_project",
                    value=value,
                    source=source,
                    observed_at=observed_at,
                    confidence=0.88,
                )
            )
    elif re.search(r"\bi'm\s+building\s+", sentence_lower):
        match = re.search(r"\bi'm\s+building\s+(.+?)(?:[.!?]|$)", sentence, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            facts.append(
                Fact(
                    content=sentence,
                    content_type=ContentType.TRIPLE,
                    entity="user",
                    attribute="current_project",
                    value=value,
                    source=source,
                    observed_at=observed_at,
                    confidence=0.88,
                )
            )

    # Rule 10: "X is my goal"
    if re.search(r"\bis\s+my\s+goal", sentence_lower):
        match = re.search(r"^(.+?)\s+is\s+my\s+goal", sentence, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            facts.append(
                Fact(
                    content=sentence,
                    content_type=ContentType.TRIPLE,
                    entity="user",
                    attribute="goal",
                    value=value,
                    source=source,
                    observed_at=observed_at,
                    confidence=0.88,
                )
            )

    return facts


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


# Improved spaCy NLP processing
