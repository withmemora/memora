"""Conversational AI integration with Ollama and automatic memory extraction v3.0."""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict

from memora.core.engine import CoreEngine
from memora.core.ingestion import extract_memories
from memora.shared.models import Memory


class MemoraChat:
    """AI chat with automatic memory extraction and context injection."""

    def __init__(
        self,
        model: str = "llama3.2:3b",
        branch: str = "main",
        memory_path: str = "./memora_data",
        max_context_memories: int = 5,
    ):
        self.model = model
        self.branch = branch
        self.max_context_memories = max_context_memories
        self.engine = CoreEngine()
        store_path = Path(memory_path)
        if (store_path / ".memora").exists():
            self.engine.open_store(store_path)
        else:
            self.engine.init_store(store_path)
        self.conversation_history: List[Dict[str, str]] = []

        try:
            import ollama

            self.ollama_client = ollama
            self._ollama_available = True
        except ImportError:
            self._ollama_available = False

    def chat(self, user_message: str, verbose: bool = False) -> str:
        return asyncio.run(self.chat_async(user_message, verbose))

    async def chat_async(self, user_message: str, verbose: bool = False) -> str:
        if not self._ollama_available:
            return "Error: Ollama is not installed. Install with: pip install ollama"

        session = self.engine.get_active_session()
        session_id = session.id if session else ""
        branch = session.branch if session else self.branch

        memories, ner_entities, _ = extract_memories(
            user_message,
            source="ollama_chat",
            session_id=session_id,
            branch=branch,
            raw_turn=user_message,
        )

        if verbose and memories:
            print(f"Extracted {len(memories)} memories from your message")

        store_path, store = self.engine._ensure()
        for memory in memories:
            store.write(memory)
            if self.engine._session_manager and session_id:
                self.engine._session_manager.add_memory_to_session(session_id, memory.id)
            if self.engine._index_manager:
                self.engine._index_manager.add_memory(
                    memory.id,
                    memory.content,
                    memory.memory_type.value,
                    memory.session_id,
                    memory.created_at,
                )
            if self.engine._graph and ner_entities:
                self.engine._graph.update_from_ner(ner_entities)

        context_memories = self._get_relevant_context(user_message)
        prompt = self._build_prompt(user_message, context_memories)

        try:
            response = await self._call_ollama(prompt)
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": response})

            ai_memories, ai_ner, _ = extract_memories(
                response,
                source="ollama_chat",
                session_id=session_id,
                branch=branch,
                raw_turn=response,
            )
            if verbose and ai_memories:
                print(f"Extracted {len(ai_memories)} memories from AI response")

            for memory in ai_memories:
                store.write(memory)
                if self.engine._session_manager and session_id:
                    self.engine._session_manager.add_memory_to_session(session_id, memory.id)
                if self.engine._index_manager:
                    self.engine._index_manager.add_memory(
                        memory.id,
                        memory.content,
                        memory.memory_type.value,
                        memory.session_id,
                        memory.created_at,
                    )
                if self.engine._graph and ai_ner:
                    self.engine._graph.update_from_ner(ai_ner)

            return response
        except Exception as e:
            return f"Error communicating with Ollama: {e}"

    def _get_relevant_context(self, query: str) -> List[Memory]:
        try:
            results = self.engine.search_memories(query)
            return results[: self.max_context_memories]
        except Exception:
            return []

    def _build_prompt(self, user_message: str, context_memories: List[Memory]) -> str:
        if not context_memories:
            return user_message
        context_lines = ["Here is what I remember about you:\n"]
        for memory in context_memories:
            context_lines.append(f"- {memory.content}")
        context_section = "\n".join(context_lines)
        return f"{context_section}\n\nUser: {user_message}\n\nAssistant:"

    async def _call_ollama(self, prompt: str) -> str:
        try:
            messages = self.conversation_history.copy()
            messages.append({"role": "user", "content": prompt})
            response = self.ollama_client.chat(model=self.model, messages=messages)
            if isinstance(response, dict):
                return response.get("message", {}).get("content", "No response from AI")
            return str(response)
        except Exception as e:
            try:
                response = self.ollama_client.generate(model=self.model, prompt=prompt)
                if isinstance(response, dict):
                    return response.get("response", "No response from AI")
                return str(response)
            except Exception:
                raise e

    def reset_conversation(self):
        self.conversation_history = []

    def get_conversation_summary(self) -> str:
        if not self.conversation_history:
            return "No conversation history"
        lines = ["Conversation History:", "=" * 50]
        for msg in self.conversation_history:
            role = msg["role"].capitalize()
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            lines.append(f"{role}: {content}")
        return "\n".join(lines)


from pathlib import Path
