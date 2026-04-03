"""New extraction pipeline for Memora v3.0.

Pipeline:
  Text -> Type Detector -> Type-Specific Extractor -> Memory String -> Graph Updater -> Index Updater -> Store
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

import spacy

from memora.core.extractors.code import extract_code_memories
from memora.core.extractors.conversation import extract_conversation_memories
from memora.core.extractors.document import extract_document_memory, extract_file_memory
from memora.core.type_detector import MemoryType, detect_type
from memora.shared.models import Memory, now_iso


def extract_memories(
    text: str,
    source: str = "ollama_chat",
    session_id: str = "",
    branch: str = "main",
    turn_index: int = 0,
    raw_turn: str = "",
    llm_response_summary: str = "",
    filename: str = "",
    file_type: str = "",
    nlp_model: str = "en_core_web_sm",
) -> tuple[list[Memory], list[dict]]:
    """Extract memories from text using the new pipeline.

    Returns:
        Tuple of (memories, ner_entities_for_graph)
    """
    text = text.strip()
    if not text:
        return [], []

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

    ner_entities = _extract_ner_for_graph(text, nlp_model)

    return memories, ner_entities


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


def _extract_ner_for_graph(text: str, nlp_model: str) -> list[dict]:
    """Run spaCy NER and return entities for graph building (NOT as memories)."""
    try:
        nlp = spacy.load(nlp_model)
    except OSError:
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
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]

    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
