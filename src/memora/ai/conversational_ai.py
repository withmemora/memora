"""Conversational AI integration with Ollama and automatic memory extraction.

This module provides AI chat capabilities with:
- Ollama integration for LLM responses (llama3.2)
- Automatic memory extraction from user messages
- Context injection from stored memories
- Memory extraction from AI responses
"""

import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict

from memora.core.ingestion import extract_facts
from memora.interface.api import MemoraStore
from memora.shared.models import Fact


class MemoraChat:
    """AI chat with automatic memory extraction and context injection."""

    def __init__(
        self,
        model: str = "llama3.2:3b",
        branch: str = "main",
        memory_path: str = "./memora_data",
        max_context_memories: int = 5,
    ):
        """Initialize MemoraChat.

        Args:
            model: Ollama model to use (default: llama3.2)
            branch: Memory branch to use (default: main)
            memory_path: Path to memory storage (default: ./memora_data)
            max_context_memories: Maximum memories to inject in context (default: 5)
        """
        self.model = model
        self.branch = branch
        self.max_context_memories = max_context_memories
        self.memory_store = MemoraStore(memory_path)
        self.conversation_history: List[Dict[str, str]] = []

        # Try to import Ollama
        try:
            import ollama

            self.ollama_client = ollama
            self._ollama_available = True
        except ImportError:
            self._ollama_available = False
            print("Warning: Ollama not installed. Install with: pip install ollama")

    def chat(self, user_message: str, verbose: bool = False) -> str:
        """Synchronous wrapper for async chat.

        Args:
            user_message: User's input message
            verbose: Whether to show memory extraction details

        Returns:
            AI's response
        """
        return asyncio.run(self.chat_async(user_message, verbose))

    async def chat_async(self, user_message: str, verbose: bool = False) -> str:
        """Chat with AI while automatically managing memories.

        Process:
        1. Extract facts from user message
        2. Store user memories
        3. Retrieve relevant context
        4. Send to Ollama with context
        5. Extract and store AI response memories

        Args:
            user_message: User's input message
            verbose: Whether to show memory extraction details

        Returns:
            AI's response
        """
        if not self._ollama_available:
            return "Error: Ollama is not installed. Install with: pip install ollama"

        # 1. Extract facts from user message
        source = f"chat:user:{datetime.now(timezone.utc).isoformat()}"
        user_facts = extract_facts(user_message, source=source)

        if verbose and user_facts:
            print(f"Extracted {len(user_facts)} memories from your message")

        # 2. Store user memories
        if user_facts:
            self.memory_store.add(user_message, source=source)

        # 3. Retrieve relevant context
        context_memories = self._get_relevant_context(user_message)

        # 4. Build prompt with context and send to Ollama
        prompt = self._build_prompt(user_message, context_memories)

        try:
            # Call Ollama API
            response = await self._call_ollama(prompt)

            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": response})

            # 5. Extract and store AI response memories
            ai_source = f"chat:ai:{datetime.now(timezone.utc).isoformat()}"
            ai_facts = extract_facts(response, source=ai_source)

            if verbose and ai_facts:
                print(f"Extracted {len(ai_facts)} memories from AI response")

            if ai_facts:
                self.memory_store.add(response, source=ai_source)

            return response

        except Exception as e:
            error_msg = f"Error communicating with Ollama: {e}"
            if verbose:
                print(f"❌ {error_msg}")
            return error_msg

    def _get_relevant_context(self, query: str) -> List[Dict]:
        """Retrieve relevant memories for context injection.

        Args:
            query: User's message to find relevant context for

        Returns:
            List of relevant memory dictionaries
        """
        try:
            # Search for relevant memories
            results = self.memory_store.search(query, limit=self.max_context_memories)
            return results if results else []
        except Exception:
            return []

    def _build_prompt(self, user_message: str, context_memories: List[Dict]) -> str:
        """Build prompt with context injection.

        Args:
            user_message: User's current message
            context_memories: Relevant memories to inject

        Returns:
            Formatted prompt string
        """
        if not context_memories:
            return user_message

        # Build context section
        context_lines = ["Here is what I remember about you:\n"]
        for memory in context_memories:
            memory_text = memory.get("memory", "")
            if memory_text:
                context_lines.append(f"- {memory_text}")

        context_section = "\n".join(context_lines)

        # Combine context with user message
        full_prompt = f"{context_section}\n\nUser: {user_message}\n\nAssistant:"

        return full_prompt

    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API with the prompt.

        Args:
            prompt: The prompt to send to Ollama

        Returns:
            Ollama's response text
        """
        try:
            # Use Ollama's chat API with conversation history
            messages = self.conversation_history.copy()
            messages.append({"role": "user", "content": prompt})

            response = self.ollama_client.chat(model=self.model, messages=messages)

            # Extract response content
            if isinstance(response, dict):
                return response.get("message", {}).get("content", "No response from AI")
            return str(response)

        except Exception as e:
            # Try fallback to generate API if chat fails
            try:
                response = self.ollama_client.generate(model=self.model, prompt=prompt)
                if isinstance(response, dict):
                    return response.get("response", "No response from AI")
                return str(response)
            except Exception:
                raise e

    def reset_conversation(self):
        """Reset conversation history."""
        self.conversation_history = []

    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation.

        Returns:
            Formatted conversation history
        """
        if not self.conversation_history:
            return "No conversation history"

        lines = ["Conversation History:", "=" * 50]
        for msg in self.conversation_history:
            role = msg["role"].capitalize()
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            lines.append(f"{role}: {content}")

        return "\n".join(lines)

    def extract_code_from_message(self, message: str) -> List[str]:
        """Extract code snippets from a message.

        Args:
            message: Message text potentially containing code

        Returns:
            List of code snippets found
        """
        import re

        code_snippets = []

        # Find code blocks with triple backticks
        code_blocks = re.findall(r"```(?:\w+)?\n(.*?)\n```", message, re.DOTALL)
        code_snippets.extend(code_blocks)

        # Find inline code
        inline_code = re.findall(r"`([^`]+)`", message)
        code_snippets.extend(inline_code)

        return [snippet.strip() for snippet in code_snippets if snippet.strip()]
