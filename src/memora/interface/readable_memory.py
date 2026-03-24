"""Human-readable memory interface for Memora conversational memory.

This solves the key visibility problem: users need to SEE their memories!

Mem0's solution: Store structured facts internally but display as readable "memory" strings:
- Backend: entity="user", attribute="preference", value="Python programming"
- Frontend: "User prefers Python programming"
- User sees: readable text they can search/filter
- System gets: structured data for conflict detection
"""

from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import json
from pathlib import Path

from memora.shared.models import Fact, ContentType
from memora.core.engine import CoreEngine


@dataclass
class MemoryFilter:
    """Filter criteria for searching memories."""

    text: Optional[str] = None
    category: Optional[str] = None
    entity: Optional[str] = None
    confidence_min: float = 0.0
    confidence_max: float = 1.0
    source: Optional[str] = None


@dataclass
class ReadableMemory:
    """Human-readable memory representation for user interface."""

    # User-facing fields
    id: str  # Short readable ID (mem_abc123)
    memory: str  # Human-readable memory text
    created_at: str  # ISO timestamp
    updated_at: str  # ISO timestamp
    branch: str  # Which branch this memory belongs to

    # Metadata for filtering/search
    entities: List[str]  # ["user", "techcorp"]
    categories: List[str]  # ["preference", "work", "personal"]
    confidence: float  # 0.0-1.0
    source: str  # "conversation", "import", etc.

    # Optional evolution tracking
    evolution_count: int = 0  # How many times this memory evolved
    last_evolution: Optional[str] = None  # When it last changed

    # Internal reference (hidden from user)
    fact_hash: str = ""  # Link to internal fact storage

    def to_display_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for user display (hide internal fields)."""
        display = asdict(self)
        # Remove internal fields
        display.pop("fact_hash", None)
        return display

    def matches_search(self, search_text: str) -> bool:
        """Check if memory matches search text."""
        search_lower = search_text.lower()
        return any(
            search_lower in text.lower()
            for text in [
                self.memory,
                " ".join(self.entities),
                " ".join(self.categories),
                self.source,
            ]
        )


class MemoryReadabilityEngine:
    """Converts structured facts into human-readable memory strings."""

    def __init__(self):
        # Templates for different fact types
        self.templates = {
            # Personal information
            ("user", "name"): "User's name is {value}",
            ("user", "email"): "User's email is {value}",
            ("user", "location"): "User lives in {value}",
            ("user", "employer"): "User works at {value}",
            ("user", "job_title"): "User's job title is {value}",
            # Preferences and skills
            ("user", "preference"): "User prefers {value}",
            ("user", "dislikes"): "User dislikes {value}",
            ("user", "programming_language"): "User knows {value} programming",
            ("user", "tool_used"): "User uses {value}",
            ("user", "skill"): "User has {value} skills",
            # Projects and work
            ("user", "current_project"): "User is working on {value}",
            ("user", "past_experience"): "User previously worked on {value}",
            ("user", "future_plan"): "User plans to {value}",
            ("user", "goal"): "User's goal is {value}",
            # Relationships
            ("user", "works_with"): "User works with {value}",
            ("user", "reports_to"): "User reports to {value}",
            ("user", "manages"): "User manages {value}",
            # Temporal facts
            ("current_project", "deadline"): "Project deadline is {value}",
            ("mentioned_date", "value"): "Important date: {value}",
        }

        # Category mappings
        self.category_map = {
            "name": ["personal", "identity"],
            "email": ["personal", "contact"],
            "location": ["personal", "location"],
            "employer": ["work", "current"],
            "job_title": ["work", "role"],
            "preference": ["preference", "personal"],
            "dislikes": ["preference", "personal"],
            "programming_language": ["skill", "technical"],
            "tool_used": ["tool", "technical"],
            "current_project": ["work", "current", "project"],
            "past_experience": ["work", "history", "experience"],
            "future_plan": ["goal", "future"],
            "goal": ["goal", "future"],
            "works_with": ["relationship", "work"],
            "reports_to": ["relationship", "work", "management"],
            "manages": ["relationship", "work", "management"],
            "deadline": ["project", "schedule"],
        }

    def fact_to_readable_memory(self, fact: Fact) -> ReadableMemory:
        """Convert a structured fact to human-readable memory."""

        # Generate human-readable text
        template_key = (fact.entity, fact.attribute)
        template = self.templates.get(template_key, "{entity} has {attribute}: {value}")

        memory_text = template.format(
            entity=fact.entity, attribute=fact.attribute, value=fact.value
        )

        # Extract entities (things mentioned in the fact)
        entities = [fact.entity]
        if fact.entity == "user" and fact.attribute in ["works_with", "reports_to", "manages"]:
            entities.append(fact.value.lower().replace(" ", "_"))

        # Map to categories
        categories = self.category_map.get(fact.attribute, ["general"])

        # Add content type as category
        content_type_map = {
            ContentType.TRIPLE: "factual",
            ContentType.PREFERENCE: "preference",
            ContentType.DATE_VALUE: "temporal",
            ContentType.PLAIN_TEXT: "general",
        }
        categories.append(content_type_map.get(fact.content_type, "general"))

        # Generate readable ID
        readable_id = f"mem_{fact.compute_hash()[:8]}"

        return ReadableMemory(
            id=readable_id,
            memory=memory_text,
            created_at=fact.observed_at.isoformat(),
            updated_at=fact.observed_at.isoformat(),
            branch="main",  # Will be set by caller
            entities=entities,
            categories=list(set(categories)),  # Remove duplicates
            confidence=fact.confidence,
            source=fact.source,
            fact_hash=fact.compute_hash(),
        )

    def update_memory_with_evolution(
        self, original_memory: ReadableMemory, new_fact: Fact
    ) -> ReadableMemory:
        """Update memory text to show evolution."""

        # Create new memory from new fact
        new_memory = self.fact_to_readable_memory(new_fact)

        # Update text to show evolution
        if original_memory.evolution_count == 0:
            # First evolution - show change
            new_memory.memory = f"{new_memory.memory} (updated from: {original_memory.memory})"
        else:
            # Multiple evolutions - just show current + count
            new_memory.memory = (
                f"{new_memory.memory} (evolved {original_memory.evolution_count + 1}x)"
            )

        # Update metadata
        new_memory.id = original_memory.id  # Keep same ID
        new_memory.evolution_count = original_memory.evolution_count + 1
        new_memory.last_evolution = datetime.now(timezone.utc).isoformat()
        new_memory.updated_at = new_fact.observed_at.isoformat()

        return new_memory


class ReadableMemoryManager:
    """Manages human-readable memory interface on top of conversational memory."""

    def __init__(self, memory_root: Path):
        """Initialize readable memory manager."""
        self.memory_root = memory_root
        self.core_engine = CoreEngine()

        # Initialize store if it doesn't exist, otherwise open it
        try:
            self.core_engine.open_store(memory_root)
        except Exception:
            # Store doesn't exist, initialize it
            self.core_engine.init_store(memory_root)
            self.core_engine.open_store(memory_root)

        self.readability_engine = MemoryReadabilityEngine()

        # Cache of readable memories by fact hash
        self.readable_cache: Dict[str, ReadableMemory] = {}

        # Memory ID to fact hash mapping
        self.id_mapping: Dict[str, str] = {}

        # Session tracking (simplified implementation)
        self.sessions: Dict[str, str] = {}  # session_id -> branch_name

    def start_conversation(self, branch_name: str = "main") -> str:
        """Start conversation and return session ID."""
        # Create session ID
        import uuid

        session_id = str(uuid.uuid4())[:8]

        # Switch to branch if needed
        try:
            self.core_engine.switch_branch(branch_name)
        except:
            # Branch doesn't exist, create it
            try:
                self.core_engine.create_branch(branch_name)
                self.core_engine.switch_branch(branch_name)
            except:
                pass  # Use current branch

        self.sessions[session_id] = branch_name
        return session_id

    def add_message(
        self, session_id: str, message: str, source: str = "conversation"
    ) -> Dict[str, Any]:
        """Add message and return readable memory insights."""

        # Get session info
        branch_name = self.sessions.get(session_id, "main")

        # Switch to session branch
        try:
            self.core_engine.switch_branch(branch_name)
        except:
            pass

        # Extract facts from message using core engine
        extracted_facts = self.core_engine.ingest_text(message, source, "user")

        # Commit if we have facts
        if extracted_facts:
            self.core_engine.commit(f"Added memories from {source}", "user")

        # Convert facts to readable memories
        new_memories = []
        evolved_memories = []

        for fact_hash, fact in extracted_facts:
            # Check if this fact evolved an existing memory
            evolved = False
            for existing_hash, cached_memory in self.readable_cache.items():
                if (
                    cached_memory.entities
                    and len(cached_memory.entities) > 0
                    and cached_memory.entities[0] == fact.entity
                    and fact.attribute in cached_memory.categories
                ):
                    # This is an evolution
                    updated_memory = self.readability_engine.update_memory_with_evolution(
                        cached_memory, fact
                    )
                    self.readable_cache[fact_hash] = updated_memory
                    evolved_memories.append(updated_memory)
                    evolved = True
                    break

            if not evolved:
                # New memory
                readable_memory = self.readability_engine.fact_to_readable_memory(fact)
                readable_memory.branch = branch_name

                self.readable_cache[fact_hash] = readable_memory
                self.id_mapping[readable_memory.id] = fact_hash
                new_memories.append(readable_memory)

        return {
            "new_memories": [m.to_display_dict() for m in new_memories],
            "evolved_memories": [m.to_display_dict() for m in evolved_memories],
            "memories_created": len(new_memories),
            "memories_evolved": len(evolved_memories),
        }

    def search_memories(
        self,
        session_id: str,
        search_text: str = None,
        category: str = None,
        entity: str = None,
        confidence_min: float = 0.0,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search memories with human-readable results."""

        # Load all memories from core engine if cache is empty
        if not self.readable_cache:
            self._populate_cache_from_engine()

        results = []

        # Apply filters
        for fact_hash, memory in self.readable_cache.items():
            # Text search
            if search_text and not memory.matches_search(search_text):
                continue

            # Category filter
            if category and category not in memory.categories:
                continue

            # Entity filter
            if entity and entity not in memory.entities:
                continue

            # Confidence filter
            if memory.confidence < confidence_min:
                continue

            results.append(memory.to_display_dict())

        # Sort by recency
        results.sort(key=lambda x: x["updated_at"], reverse=True)

        return results[:limit]

    def _populate_cache_from_engine(self):
        """Populate cache with memories from core engine."""
        try:
            all_facts = self.core_engine.get_all_facts()
            for fact_hash, fact in all_facts:
                if fact_hash not in self.readable_cache:
                    readable_memory = self.readability_engine.fact_to_readable_memory(fact)
                    readable_memory.branch = self.core_engine.get_current_branch() or "main"
                    self.readable_cache[fact_hash] = readable_memory
                    self.id_mapping[readable_memory.id] = fact_hash
        except Exception:
            pass  # Continue with empty cache

    def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get specific memory by its readable ID."""
        fact_hash = self.id_mapping.get(memory_id)
        if fact_hash and fact_hash in self.readable_cache:
            return self.readable_cache[fact_hash].to_display_dict()
        return None

    def list_memories_by_category(self, session_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """List memories organized by categories."""
        categorized = {}

        for memory in self.readable_cache.values():
            for category in memory.categories:
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append(memory.to_display_dict())

        # Sort each category by recency
        for category in categorized:
            categorized[category].sort(key=lambda x: x["updated_at"], reverse=True)

        return categorized

    def get_memory_timeline(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chronological timeline of memories."""
        timeline = list(self.readable_cache.values())
        timeline.sort(key=lambda m: m.created_at)

        return [m.to_display_dict() for m in timeline]

    def export_readable_memories(self, session_id: str, format: str = "json") -> str:
        """Export memories in human-readable format."""
        memories = [m.to_display_dict() for m in self.readable_cache.values()]

        if format == "json":
            return json.dumps(
                {
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                    "total_memories": len(memories),
                    "memories": memories,
                },
                indent=2,
            )

        elif format == "text":
            lines = [f"Memory Export - {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
            lines.append("=" * 50)

            for memory in sorted(memories, key=lambda x: x["created_at"]):
                lines.append(f"[{memory['created_at'][:10]}] {memory['memory']}")
                if memory["categories"]:
                    lines.append(f"  Categories: {', '.join(memory['categories'])}")
                lines.append("")

            return "\n".join(lines)

        return "Unsupported format"


class ReadableMemoryCLI:
    """User-friendly CLI interface for readable memories."""

    def __init__(self, memory_manager: ReadableMemoryManager):
        """Initialize CLI with memory manager."""
        self.memory_manager = memory_manager
        self.current_session = None

    def start_session(self, branch_name: str = "main"):
        """Start a new memory session."""
        self.current_session = self.memory_manager.start_conversation(branch_name)
        print(f"🧠 Started memory session on branch '{branch_name}'")
        print("💡 Try: 'My name is Alex', 'I prefer Python', 'search python'")

    def add_thought(self, thought: str):
        """Add a user thought/statement to memory."""
        if not self.current_session:
            print("❌ Start a session first with: start")
            return

        # Extract facts from thought
        from memora.core.ingestion import extract_facts

        facts = extract_facts(thought)

        # Add to memory
        result = self.memory_manager.add_message(
            self.current_session, thought, "Understood!", facts
        )

        # Show results
        if result["new_memories"]:
            print(f"✅ Added {len(result['new_memories'])} new memories:")
            for memory in result["new_memories"]:
                print(f"  • {memory['memory']} [{memory['id']}]")

        if result["evolved_memories"]:
            print(f"🧠 {len(result['evolved_memories'])} memories evolved:")
            for memory in result["evolved_memories"]:
                print(f"  • {memory['memory']} [{memory['id']}]")

    def search_memories(self, search_text: str = None, category: str = None):
        """Search memories with filters."""
        if not self.current_session:
            print("❌ Start a session first")
            return

        filters = {}
        if category:
            filters["category"] = category

        results = self.memory_manager.search_memories(self.current_session, search_text, filters)

        print(f"🔍 Found {results['total_found']} memories")
        if search_text:
            print(f"Search: '{search_text}'")
        if filters:
            print(f"Filters: {filters}")
        print("-" * 50)

        for memory in results["memories"]:
            date = memory["created_at"][:10]
            categories = ", ".join(memory["categories"][:2])  # Show first 2
            print(f"[{date}] {memory['memory']}")
            print(f"  📂 {categories} | ⚡ {memory['confidence']:.2f} | 🆔 {memory['id']}")
            print()

    def show_categories(self):
        """Show memories organized by categories."""
        if not self.current_session:
            print("❌ Start a session first")
            return

        categorized = self.memory_manager.list_memories_by_category(self.current_session)

        print("📂 Memories by Category:")
        print("-" * 30)

        for category, memories in categorized.items():
            print(f"\n🏷️ {category.upper()} ({len(memories)} memories)")
            for memory in memories[:3]:  # Show first 3
                print(f"  • {memory['memory']}")
            if len(memories) > 3:
                print(f"  ... and {len(memories) - 3} more")

    def show_timeline(self):
        """Show chronological timeline of memories."""
        if not self.current_session:
            print("❌ Start a session first")
            return

        timeline = self.memory_manager.get_memory_timeline(self.current_session)

        print("📅 Memory Timeline:")
        print("-" * 30)

        current_date = None
        for memory in timeline:
            memory_date = memory["created_at"][:10]

            if memory_date != current_date:
                print(f"\n📅 {memory_date}")
                current_date = memory_date

            time = memory["created_at"][11:16]  # HH:MM
            evolution = (
                f" (evolved {memory['evolution_count']}x)"
                if memory.get("evolution_count", 0) > 0
                else ""
            )
            print(f"  {time}: {memory['memory']}{evolution}")

    def export_memories(self, format: str = "json"):
        """Export memories to file."""
        if not self.current_session:
            print("❌ Start a session first")
            return

        content = self.memory_manager.export_readable_memories(self.current_session, format)

        filename = f"memories_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        filepath = Path(filename)

        filepath.write_text(content)
        print(f"💾 Exported memories to: {filepath}")


def main():
    """Demo of readable memory interface."""
    print("🧠 Memora: Human-Readable Memory Interface")
    print("=" * 50)

    # Setup
    memory_manager = ReadableMemoryManager(Path("./readable_memory_demo"))
    cli = ReadableMemoryCLI(memory_manager)

    print("Commands:")
    print("  start [branch] - Start memory session")
    print("  add <thought> - Add thought to memory")
    print("  search [text] - Search memories")
    print("  categories - Show memories by category")
    print("  timeline - Show chronological timeline")
    print("  export [json|text] - Export memories")
    print("  quit - Exit")
    print()

    while True:
        try:
            user_input = input("readable> ").strip()

            if not user_input:
                continue

            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()

            if cmd == "start":
                branch = parts[1] if len(parts) > 1 else "main"
                cli.start_session(branch)

            elif cmd == "add":
                if len(parts) < 2:
                    print("Usage: add <thought>")
                else:
                    cli.add_thought(parts[1])

            elif cmd == "search":
                search_text = parts[1] if len(parts) > 1 else None
                cli.search_memories(search_text)

            elif cmd == "categories":
                cli.show_categories()

            elif cmd == "timeline":
                cli.show_timeline()

            elif cmd == "export":
                format = parts[1] if len(parts) > 1 else "json"
                cli.export_memories(format)

            elif cmd in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                break

            else:
                print(f"Unknown command: {cmd}")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
