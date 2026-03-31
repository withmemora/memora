"""Ollama Memory Monitor - Automatically capture memories from Ollama conversations.

This service runs in the background and monitors Ollama chat sessions,
automatically extracting and storing memories without needing a separate chat interface.
"""

import time
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict
import threading

from memora.interface.api import MemoraStore
from memora.core.ingestion import extract_facts


class OllamaMemoryMonitor:
    """Monitor Ollama conversations and automatically store memories."""

    def __init__(
        self, memory_path: str = "./memora_data", check_interval: int = 5, verbose: bool = True
    ):
        """Initialize the monitor.

        Args:
            memory_path: Path to Memora storage
            check_interval: Seconds between checks
            verbose: Print monitoring updates
        """
        self.memory_store = MemoraStore(memory_path)
        self.check_interval = check_interval
        self.verbose = verbose
        self.running = False
        self.conversation_history: List[Dict] = []

        # Track processed messages to avoid duplicates
        self.processed_messages: set = set()

    def start(self):
        """Start monitoring in background thread."""
        if self.running:
            print("Monitor already running!")
            return

        self.running = True
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()

        if self.verbose:
            print("🧠 Memora Memory Monitor started")
            print("   Watching Ollama conversations...")
            print("   Press Ctrl+C to stop\n")

    def stop(self):
        """Stop monitoring."""
        self.running = False
        if self.verbose:
            print("\n✅ Memory Monitor stopped")

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                # Check for new Ollama conversations
                self._check_ollama_history()
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Monitor error: {e}")
                time.sleep(self.check_interval)

    def _check_ollama_history(self):
        """Check Ollama for conversation history.

        Note: Ollama doesn't expose conversation history via API,
        but we can monitor conversations if we hook into the chat flow.
        """
        # This is a placeholder - Ollama API doesn't expose history
        # We'll use a different approach below
        pass

    def process_conversation_turn(
        self, user_message: str, ai_response: str, session_id: Optional[str] = None
    ) -> Dict[str, int]:
        """Process a single conversation turn and extract memories.

        Args:
            user_message: User's message
            ai_response: AI's response
            session_id: Optional session identifier

        Returns:
            Dictionary with extraction statistics
        """
        if not session_id:
            session_id = f"ollama_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        # Create unique message IDs to avoid duplicates
        user_msg_id = f"{session_id}_{hash(user_message)}"
        ai_msg_id = f"{session_id}_{hash(ai_response)}"

        user_facts = 0
        ai_facts = 0

        # Process user message
        if user_msg_id not in self.processed_messages:
            user_source = f"ollama:user:{session_id}"
            facts = extract_facts(user_message, source=user_source)

            for fact in facts:
                self.memory_store.add(fact.content, source=user_source)

            user_facts = len(facts)
            self.processed_messages.add(user_msg_id)

            if self.verbose and user_facts > 0:
                print(f"📝 User: {user_facts} memories extracted")

        # Process AI response
        if ai_msg_id not in self.processed_messages:
            ai_source = f"ollama:ai:{session_id}"
            facts = extract_facts(ai_response, source=ai_source)

            for fact in facts:
                self.memory_store.add(fact.content, source=ai_source)

            ai_facts = len(facts)
            self.processed_messages.add(ai_msg_id)

            if self.verbose and ai_facts > 0:
                print(f"🤖 AI: {ai_facts} memories extracted")

        return {"user_facts": user_facts, "ai_facts": ai_facts, "total": user_facts + ai_facts}


def create_monitored_ollama_wrapper():
    """Create a wrapper for Ollama that auto-captures memories.

    This allows users to chat naturally while memories are captured.
    """
    import ollama

    monitor = OllamaMemoryMonitor(verbose=True)
    client = ollama.Client()

    def monitored_chat(model: str, messages: List[Dict], **kwargs):
        """Chat with Ollama while capturing memories."""
        # Get response from Ollama
        response = client.chat(model=model, messages=messages, **kwargs)

        # Extract last user message and AI response
        if messages:
            last_user_msg = next(
                (m["content"] for m in reversed(messages) if m["role"] == "user"), None
            )

            if last_user_msg and "message" in response:
                ai_response = response["message"].get("content", "")

                # Process this conversation turn
                monitor.process_conversation_turn(last_user_msg, ai_response)

        return response

    return monitored_chat, monitor


# Simple interactive chat that auto-captures memories
def interactive_chat_with_memory(model: str = "llama3.2:3b"):
    """Interactive Ollama chat with automatic memory capture.

    This provides a simple terminal interface that captures memories automatically.
    """
    import ollama

    print("=" * 60)
    print("🧠 Ollama Chat with Memora Memory Capture")
    print("=" * 60)
    print(f"Model: {model}")
    print("Type 'exit' to quit, 'memories' to view stored memories\n")

    client = ollama.Client()
    monitor = OllamaMemoryMonitor(verbose=True)
    conversation = []

    try:
        while True:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() == "exit":
                print("\n✅ Chat ended")
                break

            if user_input.lower() == "memories":
                # Show stored memories
                memories = monitor.memory_store.get_all()
                print(f"\n📚 Stored Memories ({len(memories)}):")
                for i, mem in enumerate(memories[:10], 1):
                    print(f"  {i}. {mem.get('memory', '')[:60]}")
                if len(memories) > 10:
                    print(f"  ... and {len(memories) - 10} more")
                print()
                continue

            # Add to conversation history
            conversation.append({"role": "user", "content": user_input})

            # Get AI response
            response = client.chat(model=model, messages=conversation)

            ai_response = response["message"]["content"]
            conversation.append({"role": "assistant", "content": ai_response})

            # Display response
            print(f"\nAI: {ai_response}\n")

            # Capture memories
            stats = monitor.process_conversation_turn(user_input, ai_response)

            if stats["total"] > 0:
                print(f"💾 Captured {stats['total']} new memories\n")

    except KeyboardInterrupt:
        print("\n\n✅ Chat ended")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    # Run interactive chat with memory capture
    interactive_chat_with_memory()
