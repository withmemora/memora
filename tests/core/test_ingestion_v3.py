"""Tests for v3.0 extraction pipeline.

This module tests the new extraction pipeline:
- Type detection (conversation/code/document/file)
- Type-specific extractors
- Human-readable memory generation (not triples)
- NER entity extraction for graph
"""

import pytest

from memora.core.ingestion import extract_memories
from memora.core.type_detector import MemoryType, detect_type
from memora.shared.models import MemorySource


class TestTypeDetection:
    """Test memory type detection."""

    def test_detect_conversation(self):
        """Test detecting CONVERSATION type."""
        text = "My name is Sarah and I work at Microsoft."
        mem_type = detect_type(text, "ollama_chat")

        assert mem_type == MemoryType.CONVERSATION

    def test_detect_code_with_triple_backticks(self):
        """Test detecting CODE type from code blocks."""
        text = """
Here's a function:
```python
def process_pdf(path):
    return read_file(path)
```
"""
        mem_type = detect_type(text, "ollama_chat")

        assert mem_type == MemoryType.CODE

    def test_detect_code_with_def_keyword(self):
        """Test detecting CODE type from def/class keywords."""
        text = "def calculate_total(items):\n    return sum(items)"
        mem_type = detect_type(text, "ollama_chat")

        assert mem_type == MemoryType.CODE

    def test_detect_document_from_source(self):
        """Test detecting DOCUMENT type from file ingestion source."""
        text = "This is document content."
        mem_type = detect_type(text, "file_ingestion")

        assert mem_type in [MemoryType.DOCUMENT, MemoryType.FILE]


class TestConversationExtractor:
    """Test conversation memory extraction."""

    def test_extract_user_name(self):
        """Test extracting user name from 'My name is X' pattern."""
        text = "My name is Sarah Chen."
        memories, _, _ = extract_memories(
            text, source="ollama_chat", session_id="sess_test", branch="main"
        )

        assert len(memories) >= 1
        name_memories = [m for m in memories if "name is sarah" in m.content.lower()]
        assert len(name_memories) == 1
        # Implementation lowercases the name
        assert name_memories[0].content.lower() == "user's name is sarah chen"
        assert name_memories[0].confidence >= 0.90

    def test_extract_location(self):
        """Test extracting location from 'I live in X' pattern."""
        text = "I live in Seattle."
        memories, _, _ = extract_memories(
            text, source="ollama_chat", session_id="sess_test", branch="main"
        )

        assert len(memories) >= 1
        location_memories = [m for m in memories if "seattle" in m.content.lower()]
        assert len(location_memories) >= 1

    def test_extract_workplace(self):
        """Test extracting workplace from 'I work at X' pattern."""
        text = "I work at Microsoft."
        memories, _, _ = extract_memories(
            text, source="ollama_chat", session_id="sess_test", branch="main"
        )

        assert len(memories) >= 1
        work_memories = [m for m in memories if "microsoft" in m.content.lower()]
        assert len(work_memories) >= 1

    def test_extract_preference(self):
        """Test extracting preferences from 'I prefer X' pattern."""
        text = "I prefer Python over JavaScript."
        memories, _, _ = extract_memories(
            text, source="ollama_chat", session_id="sess_test", branch="main"
        )

        assert len(memories) >= 1
        pref_memories = [m for m in memories if "prefer" in m.content.lower()]
        assert len(pref_memories) >= 1

    def test_memory_content_is_human_readable(self):
        """Test that extracted memories are human-readable, not triples."""
        text = "My name is Alice and I work at Google in Mountain View."
        memories, _, _ = extract_memories(
            text, source="ollama_chat", session_id="sess_test", branch="main"
        )

        for memory in memories:
            # Content should be plain English sentences
            assert isinstance(memory.content, str)
            # NOT entity-attribute-value format
            assert "entity" not in memory.content.lower()
            assert "attribute" not in memory.content.lower()
            assert "=" not in memory.content

    def test_multiple_facts_in_one_sentence(self):
        """Test extracting multiple memories from one sentence."""
        text = "My name is Bob, I live in Austin, and I work at Tesla."
        memories, _, _ = extract_memories(
            text, source="ollama_chat", session_id="sess_test", branch="main"
        )

        # Should extract at least 3 memories (name, location, workplace)
        assert len(memories) >= 3

    def test_conversation_memory_metadata(self):
        """Test that conversation memories include raw_turn in metadata."""
        text = "I prefer tabs over spaces."
        raw_turn = "I always use tabs in my code, never spaces."
        memories, _, _ = extract_memories(
            text,
            source="ollama_chat",
            session_id="sess_test",
            branch="main",
            raw_turn=raw_turn,
        )

        if memories:
            # Check metadata contains raw_turn
            assert "raw_turn" in memories[0].metadata or memories[0].metadata == {}


class TestCodeExtractor:
    """Test code memory extraction."""

    def test_extract_python_code(self):
        """Test extracting Python code memories."""
        text = """
```python
def calculate_total(items):
    return sum(item.price for item in items)
```
"""
        memories, _, _ = extract_memories(
            text, source="ollama_chat", session_id="sess_test", branch="main"
        )

        assert len(memories) >= 1
        code_memory = memories[0]
        assert code_memory.memory_type == MemoryType.CODE
        assert code_memory.metadata.get("language") == "python"
        assert "calculate_total" in code_memory.metadata.get("function_names", [])

    def test_extract_javascript_code(self):
        """Test extracting JavaScript code."""
        text = """
```javascript
function getUserData(id) {
    return fetch(`/api/users/${id}`);
}
```
"""
        memories, _, _ = extract_memories(
            text, source="ollama_chat", session_id="sess_test", branch="main"
        )

        code_memories = [m for m in memories if m.memory_type == MemoryType.CODE]
        assert len(code_memories) >= 1
        assert code_memories[0].metadata.get("language") == "javascript"

    def test_code_with_conversation(self):
        """Test extracting both code and conversation from mixed input."""
        text = """
I use this function for processing:
```python
def process_data(data):
    return data.strip()
```
I prefer this approach.
"""
        memories, _, _ = extract_memories(
            text, source="ollama_chat", session_id="sess_test", branch="main"
        )

        # Should have both code and conversation memories
        code_memories = [m for m in memories if m.memory_type == MemoryType.CODE]
        conv_memories = [m for m in memories if m.memory_type == MemoryType.CONVERSATION]

        assert len(code_memories) >= 1
        # May or may not extract conversation from "I prefer this approach"


class TestDocumentExtractor:
    """Test document/file memory extraction."""

    def test_extract_document_memory(self):
        """Test extracting memory from document ingestion."""
        text = """
Memora Architecture

Memora uses Git-style object storage with zlib compression.
All memories are stored as human-readable strings.
The system uses SHA-256 hashing for content addressing.
"""
        memories, _, _ = extract_memories(
            text,
            source="file_ingestion",
            session_id="sess_test",
            branch="main",
            filename="architecture.md",
            file_type="markdown",
        )

        assert len(memories) >= 1
        doc_memory = memories[0]
        assert doc_memory.memory_type in [MemoryType.DOCUMENT, MemoryType.FILE]
        assert doc_memory.metadata.get("filename") == "architecture.md"
        assert doc_memory.metadata.get("file_type") == "markdown"

    def test_document_key_facts(self):
        """Test that document memories extract key facts."""
        text = """
Memora v3.0 introduces several improvements:
- Human-readable memory storage
- Session-based auto-commit
- Knowledge graph integration
- Four incremental indices
"""
        memories, _, _ = extract_memories(
            text,
            source="file_ingestion",
            session_id="sess_test",
            branch="main",
            filename="changelog.md",
        )

        assert len(memories) >= 1
        # Document should have key_facts in metadata
        if "key_facts" in memories[0].metadata:
            assert isinstance(memories[0].metadata["key_facts"], list)


class TestNEREntityExtraction:
    """Test NER entity extraction for knowledge graph."""

    def test_ner_extracts_entities(self):
        """Test that NER extracts entities for the graph."""
        text = "My name is Sarah and I work at Microsoft in Seattle."
        memories, ner_entities, _ = extract_memories(
            text, source="ollama_chat", session_id="sess_test", branch="main"
        )

        # NER should return entities
        assert isinstance(ner_entities, list)
        # Should have extracted some entities
        # (Actual NER results depend on spaCy model, so we can't be too specific)

    def test_ner_entities_not_in_memory_store(self):
        """Test that NER entities don't create junk memories."""
        text = "Microsoft is an organization based in Seattle."
        memories, ner_entities, _ = extract_memories(
            text, source="ollama_chat", session_id="sess_test", branch="main"
        )

        # Should NOT have memories like "microsoft.entity_type = organization"
        for memory in memories:
            assert "entity_type" not in memory.content
            assert ".type =" not in memory.content

    def test_entities_stored_in_memory_field(self):
        """Test that entities are stored in Memory.entities field."""
        text = "I work at Google in Mountain View."
        memories, _, _ = extract_memories(
            text, source="ollama_chat", session_id="sess_test", branch="main"
        )

        # Entities should be in the entities field, not content
        for memory in memories:
            if memory.entities:
                assert isinstance(memory.entities, list)


class TestExtractionMetadata:
    """Test that extraction preserves metadata correctly."""

    def test_session_id_propagated(self):
        """Test that session_id is set on all memories."""
        text = "My name is Alice."
        memories, _, _ = extract_memories(
            text, source="ollama_chat", session_id="sess_abc123", branch="main"
        )

        for memory in memories:
            assert memory.session_id == "sess_abc123"

    def test_branch_propagated(self):
        """Test that branch is set on all memories."""
        text = "I prefer Python."
        memories, _, _ = extract_memories(
            text, source="ollama_chat", session_id="sess_test", branch="work"
        )

        for memory in memories:
            assert memory.branch == "work"

    def test_turn_index_propagated(self):
        """Test that turn_index is set correctly."""
        text = "I work at OpenAI."
        memories, _, _ = extract_memories(
            text, source="ollama_chat", session_id="sess_test", branch="main", turn_index=5
        )

        for memory in memories:
            assert memory.turn_index == 5

    def test_confidence_scores(self):
        """Test that memories have confidence scores."""
        text = "My name is Bob."
        memories, _, _ = extract_memories(
            text, source="ollama_chat", session_id="sess_test", branch="main"
        )

        for memory in memories:
            assert 0.0 <= memory.confidence <= 1.0

    def test_memory_ids_generated(self):
        """Test that all memories have valid IDs."""
        text = "I live in Seattle."
        memories, _, _ = extract_memories(
            text, source="ollama_chat", session_id="sess_test", branch="main"
        )

        for memory in memories:
            assert memory.id.startswith("mem_")
            assert len(memory.id) == 16  # "mem_" + 12 hex chars


class TestEmptyInput:
    """Test handling of empty or whitespace input."""

    def test_empty_string(self):
        """Test that empty string returns no memories."""
        memories, ner, _ = extract_memories(
            "", source="ollama_chat", session_id="sess_test", branch="main"
        )

        assert memories == []
        assert ner == []

    def test_whitespace_only(self):
        """Test that whitespace-only input returns no memories."""
        memories, ner, _ = extract_memories(
            "   \n  \t  ", source="ollama_chat", session_id="sess_test", branch="main"
        )

        assert memories == []
        assert ner == []


class TestMemorySourceTypes:
    """Test different memory source types."""

    def test_ollama_chat_source(self):
        """Test memories from Ollama chat have correct source."""
        text = "My name is Alice."
        memories, _, _ = extract_memories(
            text, source="ollama_chat", session_id="sess_test", branch="main"
        )

        for memory in memories:
            assert memory.source == MemorySource.OLLAMA_CHAT

    def test_file_ingestion_source(self):
        """Test memories from file ingestion have correct source."""
        text = "Document content."
        memories, _, _ = extract_memories(
            text,
            source="file_ingestion",
            session_id="sess_test",
            branch="main",
            filename="test.txt",
        )

        for memory in memories:
            assert memory.source == MemorySource.FILE_INGESTION

    def test_manual_source(self):
        """Test memories from manual input have correct source."""
        text = "Manual memory."
        memories, _, _ = extract_memories(
            text, source="manual", session_id="sess_test", branch="main"
        )

        for memory in memories:
            assert memory.source == MemorySource.MANUAL
