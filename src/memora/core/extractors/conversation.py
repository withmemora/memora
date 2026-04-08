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
    Step 2: If no patterns match and text is substantial, create a summary memory
    Step 3: Deduplication check
    """
    print(f"[EXTRACT] extract_conversation_memories called with {len(text)} chars")
    sentences = _split_sentences(text)
    print(f"[EXTRACT] Split into {len(sentences)} sentences")
    memories: list[Memory] = []

    for idx, sentence in enumerate(sentences):
        print(f"[EXTRACT] Processing sentence {idx}: '{sentence[:60]}'")
        matched = _apply_patterns(sentence)
        print(f"[EXTRACT]   Patterns matched: {len(matched)}")
        for memory_content, confidence in matched:
            print(f"[EXTRACT]   Creating memory: {memory_content[:60]}... (conf={confidence})")
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

    print(f"[EXTRACT] Pattern matching found {len(memories)} memories")

    # Fallback: If no patterns matched and text is substantial, create a summary memory
    # This prevents the "no memories captured" problem when AI responses don't match patterns
    if not memories and text.strip() and len(text.strip()) > 20:
        print(f"[EXTRACT] No patterns matched, attempting fallback summary...")
        # Create a summary memory for substantial conversations that don't match patterns
        summary = _create_summary_memory(text)
        print(f"[EXTRACT] Summary generated: {summary}")
        if summary:
            mem = Memory(
                id=Memory.generate_id(),
                content=summary,
                memory_type=MemoryType.CONVERSATION,
                confidence=0.75,  # Lower confidence for automatic summaries
                source=MemorySource.OLLAMA_CHAT,
                session_id=session_id,
                branch=branch,
                turn_index=turn_index,
                created_at=now_iso(),
                updated_at=now_iso(),
                metadata={
                    "raw_turn": raw_turn or text[:200],
                    "llm_response_summary": llm_response_summary,
                    "summary": True,  # Mark this as auto-generated summary
                },
            )
            memories.append(mem)
            print(f"[EXTRACT] Added fallback summary memory")

    print(f"[EXTRACT] Returning {len(memories)} total memories")
    return memories


def _create_summary_memory(text: str) -> str | None:
    """Create a summary memory for text that doesn't match specific patterns.

    This is a fallback to prevent losing information from conversational turns
    that don't match pattern extraction rules.
    """
    text = text.strip()
    if not text or len(text) < 20:
        return None

    # For longer responses, create a summary statement
    # Keep it under 200 chars for readability
    if len(text) > 200:
        # Take first 2 sentences or first 200 chars, whichever is shorter
        sentences = text.split(". ")
        summary_text = ". ".join(sentences[:2]) if len(sentences) > 1 else text[:200]
        if not summary_text.endswith("."):
            summary_text += "."
        return f"AI discussed: {summary_text}"
    else:
        return f"AI discussed: {text}"


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
