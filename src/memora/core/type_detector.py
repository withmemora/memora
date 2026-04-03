"""Detect memory type from input text."""

from __future__ import annotations

import re

from memora.shared.models import MemoryType


def detect_type(text: str, source_hint: str = "") -> MemoryType:
    """Detect the type of memory from input text.

    Priority order:
    1. Code blocks or def/class patterns -> CODE
    2. File ingestion with filename -> DOCUMENT or FILE
    3. Ollama proxy (conversational) -> CONVERSATION
    4. Default -> CONVERSATION
    """
    if _is_code(text):
        return MemoryType.CODE

    if source_hint.startswith("file_ingestion") or source_hint.startswith("file:"):
        if _is_document(text):
            return MemoryType.DOCUMENT
        return MemoryType.FILE

    return MemoryType.CONVERSATION


def _is_code(text: str) -> bool:
    if "```" in text:
        return True
    if re.search(r"\bdef\s+\w+\s*\(", text):
        return True
    if re.search(r"\bclass\s+\w+", text):
        return True
    if re.search(r"\bfunction\s+\w+\s*\(", text):
        return True
    if re.search(r"\bconst\s+\w+\s*=\s*\(", text):
        return True
    if re.search(r"\blet\s+\w+\s*=\s*\(", text):
        return True
    if re.search(r"\bSELECT\s+.+\bFROM\b", text, re.IGNORECASE):
        return True
    if re.search(r"^\s*#!/", text, re.MULTILINE):
        return True
    return False


def _is_document(text: str) -> bool:
    if len(text) > 500:
        return True
    if re.search(r"^#{1,6}\s+", text, re.MULTILINE):
        return True
    if text.count("\n") > 10:
        return True
    return False
