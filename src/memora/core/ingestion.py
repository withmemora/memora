"""New extraction pipeline for Memora v3.1.

Pipeline:
  Text -> Security Filter -> Type Detector -> Type-Specific Extractor -> Memory String -> Graph Updater -> Index Updater -> Store
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
import logging
import warnings

from memora.core.extractors.code import extract_code_memories
from memora.core.extractors.conversation import extract_conversation_memories
from memora.core.extractors.document import extract_document_memory, extract_file_memory
from memora.core.type_detector import MemoryType, detect_type
from memora.core.security_filter import filter_sensitive_content, scan_for_sensitive_content
from memora.shared.models import Memory, now_iso

logger = logging.getLogger(__name__)


def load_nlp():
    """Load spaCy model with graceful degradation."""
    try:
        import spacy

        return spacy.load("en_core_web_sm")
    except OSError:
        # spaCy installed but model not downloaded
        warnings.warn(
            "spaCy model 'en_core_web_sm' not found. "
            "NER disabled — graph will not be populated. "
            "Pattern extraction still works. "
            "Run: python -m spacy download en_core_web_sm"
        )
        return None
    except ImportError:
        warnings.warn("spaCy not installed. NER disabled.")
        return None


def extract_memories(
    text: str,
    source: str = "ollama_chat",
    session_id: str = "",
    branch: str = "main",
    turn_index: int = 0,
    nlp_model: str = "en_core_web_sm",
    filename: str | None = None,
    file_type: str | None = None,
    raw_turn: str | None = None,
    llm_response_summary: str | None = None,
    skip_security_filter: bool = False,
) -> tuple[list[Memory], list[dict], list[str]]:
    """Extract memories from text.

    Returns:
        Tuple of (memories, ner_entities_for_graph, security_warnings)
    """
    text = text.strip()
    if not text:
        return [], [], []

    # SECURITY FILTER - Critical first step
    security_warnings = []
    if not skip_security_filter:
        has_sensitive, detected_types = scan_for_sensitive_content(text)
        if has_sensitive:
            filtered_text, redacted_types = filter_sensitive_content(text)
            security_warnings = [f"Filtered {', '.join(redacted_types)} from content"]
            logger.warning(f"Sensitive content filtered: {redacted_types}")
            text = filtered_text

            # Also filter raw_turn if provided
            if raw_turn:
                raw_turn, _ = filter_sensitive_content(raw_turn)

    memory_type = detect_type(text, source)

    if memory_type == MemoryType.CODE:
        memories = _extract_code(text, source, session_id, branch, turn_index)
    elif memory_type == MemoryType.DOCUMENT:
        memories = extract_document_memory(
            text, filename or "document", file_type or "text", source, session_id, branch
        )
    elif memory_type == MemoryType.FILE:
        memories = extract_file_memory(
            text, filename or "file", file_type or "text", source, session_id, branch
        )
    else:
        memories = extract_conversation_memories(
            text, source, session_id, branch, turn_index, raw_turn or text, llm_response_summary
        )

    # Use graceful NLP loading for NER
    nlp = load_nlp()
    ner_entities = _extract_ner_for_graph(text, nlp)

    return memories, ner_entities, security_warnings


def _extract_code(
    text: str, source: str, session_id: str, branch: str, turn_index: int
) -> list[Memory]:
    code_memories = extract_code_memories(text, source, session_id, branch, turn_index)

    conversation_parts = _remove_code_blocks(text)
    if conversation_parts.strip():
        conv_memories = extract_conversation_memories(
            conversation_parts, source, session_id, branch, turn_index
        )
        code_memories.extend(conv_memories)

    return code_memories


def _remove_code_blocks(text: str) -> str:
    return re.sub(r"```[\s\S]*?```", "", text)


def _extract_ner_for_graph(text: str, nlp) -> list[dict]:
    """Run spaCy NER and return entities for graph building (NOT as memories)."""
    if nlp is None:
        # spaCy not available, return empty list
        return []

    doc = nlp(text)
    entities = []

    for ent in doc.ents:
        entity_type_map = {
            "PERSON": "person",
            "ORG": "organization",
            "GPE": "location",
            "DATE": "date",
            "PRODUCT": "technology",
            "WORK_OF_ART": "project",
        }
        graph_type = entity_type_map.get(ent.label_, "concept")

        entities.append(
            {
                "name": ent.text,
                "type": graph_type,
                "label": ent.label_,
            }
        )

    return entities


def normalize_text(text: str) -> list[str]:
    """Normalize and split text into sentences (kept for backward compat)."""
    text = text.strip()
    if not text:
        return []

    # Use graceful loading for spaCy
    nlp = load_nlp()
    if nlp is None:
        # Fallback: simple sentence splitting
        import re

        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]

    # Use spaCy for proper sentence segmentation
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
