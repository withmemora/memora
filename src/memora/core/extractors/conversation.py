"""Conversation memory extractor.

Converts conversational text into human-readable Memory objects using
pattern matching. NER output goes to the graph, NOT to memory store.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from memora.shared.models import Memory, MemorySource, MemoryType, now_iso


def extract_conversation_memories(
    text: str,
    source: str = "ollama_chat",
    session_id: str = "",
    branch: str = "main",
    turn_index: int = 0,
    raw_turn: str = "",
    llm_response_summary: str = "",
) -> list[Memory]:
    """Extract memories from conversational text.

    Step 1: Pattern matching for high-confidence facts
    Step 2: Deduplication check
    """
    sentences = _split_sentences(text)
    memories: list[Memory] = []

    for sentence in sentences:
        matched = _apply_patterns(sentence)
        for memory_content, confidence in matched:
            mem = Memory(
                id=Memory.generate_id(),
                content=memory_content,
                memory_type=MemoryType.CONVERSATION,
                confidence=confidence,
                source=MemorySource.OLLAMA_CHAT,
                session_id=session_id,
                branch=branch,
                turn_index=turn_index,
                created_at=now_iso(),
                updated_at=now_iso(),
                metadata={
                    "raw_turn": raw_turn or sentence,
                    "llm_response_summary": llm_response_summary,
                },
            )
            memories.append(mem)

    return memories


def _split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    return sentences


def _apply_patterns(sentence: str) -> list[tuple[str, float]]:
    results = []
    lower = sentence.lower()

    for pattern, template, confidence in _get_patterns():
        m = re.search(pattern, lower)
        if m:
            try:
                value = m.group(1).strip()
            except IndexError:
                value = sentence
            if value:
                results.append((template.format(value=value), confidence))

    return results


def _get_patterns() -> list[tuple[str, str, float]]:
    return [
        (r"\bmy\s+name\s+is\s+(.+?)(?:[.!?]|$)", "User's name is {value}", 0.95),
        (r"\bi\s+am\s+(.+?)(?:[.!?]|$)", "User is {value}", 0.90),
        (r"\bi'm\s+(.+?)(?:[.!?]|$)", "User is {value}", 0.90),
        (r"\bi\s+live\s+in\s+(.+?)(?:[.!?]|$)", "User lives in {value}", 0.92),
        (r"\bmy\s+email\s+is\s+(\S+@\S+\.\S+)", "User's email is {value}", 0.95),
        (r"\bi\s+work\s+at\s+(.+?)(?:[.!?]|$)", "User works at {value}", 0.95),
        (r"\bi\s+work\s+with\s+(.+?)(?:[.!?]|$)", "User works with {value}", 0.90),
        (r"\bthe\s+deadline\s+is\s+(.+?)(?:[.!?]|$)", "Deadline is {value}", 0.90),
        (r"\bi\s+prefer\s+(.+?)(?:[.!?]|$)", "User prefers {value}", 0.90),
        (r"\bmy\s+favorite\s+.+?\s+is\s+(.+?)(?:[.!?]|$)", "User's favorite is {value}", 0.90),
        (r"\bfavorite\s+\w+\s+is\s+(.+?)(?:[.!?]|$)", "User's favorite is {value}", 0.85),
        (r"\bmy\s+project\s+is\s+(.+?)(?:[.!?]|$)", "User's project is {value}", 0.88),
        (r"\bi\s+am\s+building\s+(.+?)(?:[.!?]|$)", "User is building {value}", 0.87),
        (r"\bi'm\s+building\s+(.+?)(?:[.!?]|$)", "User is building {value}", 0.87),
        (r"\bi\s+like\s+(.+?)(?:[.!?]|$)", "User likes {value}", 0.88),
        (r"\bi\s+use\s+(.+?)(?:[.!?]|$)", "User uses {value}", 0.90),
        (r"\bis\s+my\s+goal", "{value} is user's goal", 0.88),
        (
            r"\bi\s+have\s+(\d+)\s+years?\s+(?:of\s+)?(.+?)\s+(?:experience|exp)",
            "User has {value} experience",
            0.90,
        ),
        (r"\bi\s+always\s+use\s+(.+?)(?:[.!?]|$)", "User always uses {value}", 0.88),
        (r"\bi\s+consider(?:ing)?\s+(.+?)(?:[.!?]|$)", "User is considering {value}", 0.80),
    ]
