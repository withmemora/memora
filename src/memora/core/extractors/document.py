"""Document and file memory extractor."""

from __future__ import annotations

from memora.shared.models import Memory, MemorySource, MemoryType, now_iso


def extract_document_memory(
    text: str,
    filename: str,
    file_type: str,
    source: str = "file_ingestion",
    session_id: str = "",
    branch: str = "main",
) -> list[Memory]:
    """Create a Document memory from an ingested file."""
    key_facts = _extract_key_facts(text)
    word_count = len(text.split())
    excerpt = text[:500] if len(text) > 500 else text

    content = (
        f"Document: {filename} - {'; '.join(key_facts[:5])}"
        if key_facts
        else f"Document ingested: {filename}"
    )

    mem = Memory(
        id=Memory.generate_id(),
        content=content,
        memory_type=MemoryType.DOCUMENT,
        confidence=0.85,
        source=MemorySource.FILE_INGESTION,
        session_id=session_id,
        branch=branch,
        turn_index=0,
        created_at=now_iso(),
        updated_at=now_iso(),
        metadata={
            "filename": filename,
            "file_type": file_type,
            "key_facts": key_facts,
            "word_count": word_count,
            "raw_excerpt": excerpt,
        },
    )
    return [mem]


def extract_file_memory(
    text: str,
    filename: str,
    file_type: str,
    source: str = "file_ingestion",
    session_id: str = "",
    branch: str = "main",
) -> list[Memory]:
    """Create a File memory from a small ingested file."""
    line_count = text.count("\n") + 1
    raw_content = text if len(text) < 5000 else text[:5000] + "... (truncated)"

    content = f"File ingested: {filename} ({line_count} lines)"

    mem = Memory(
        id=Memory.generate_id(),
        content=content,
        memory_type=MemoryType.FILE,
        confidence=0.85,
        source=MemorySource.FILE_INGESTION,
        session_id=session_id,
        branch=branch,
        turn_index=0,
        created_at=now_iso(),
        updated_at=now_iso(),
        metadata={
            "filename": filename,
            "file_type": file_type,
            "line_count": line_count,
            "raw_content": raw_content,
        },
    )
    return [mem]


def _extract_key_facts(text: str) -> list[str]:
    """Extract 3-5 key facts from document text."""
    import re

    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip() and len(s.strip()) > 20]

    facts = []
    for sentence in sentences[:5]:
        if len(sentence) < 200:
            facts.append(sentence)

    return facts[:5]
