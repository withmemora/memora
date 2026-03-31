import ollama
from pathlib import Path
from memora.core.ingestion import extract_facts
from memora.core.store import ObjectStore


class MemoraChat:

    def __init__(self):
        self.client = ollama.Client()
        self.store = ObjectStore(Path(".memora"))

    def extract_code_blocks(self, message: str):
        code_blocks = []

        if "```" in message:
            parts = message.split("```")
            for i in range(1, len(parts), 2):
                block = parts[i].strip()
                if block:
                    code_blocks.append(block)

        if not code_blocks:
            if any(k in message for k in ["def ", "return ", "class ", "import "]):
                code_blocks.append(message.strip())

        return code_blocks

    def needs_memory(self, message: str) -> bool:
        message = message.lower()

        triggers = [
            "my", "i", "me",
            "what did i", "what do i",
            "who am i", "remember",
            "code", "earlier", "before"
        ]

        return any(t in message for t in triggers)

    def chat(self, message: str):

        message_lower = message.lower()

        # ✅ STEP 1: store normal facts
        if len(message.strip()) > 3:
            facts = extract_facts(message, "user")
            for f in facts:
                self.store.write(f)

        # ✅ STEP 2: store code (SAFE METHOD)
        code_blocks = self.extract_code_blocks(message)

        for code in code_blocks:
            fact_text = f"user wrote code {code}"
            facts = extract_facts(fact_text, "user")

            for f in facts:
                self.store.write(f)

        # ✅ STEP 3: retrieve memory
        if self.needs_memory(message):

            all_hashes = self.store.list_all_hashes()

            # 🔥 CODE RETRIEVAL
            if "code" in message_lower:
                for h in reversed(all_hashes):
                    try:
                        fact = self.store.read_fact(h)

                        content = getattr(fact, "content", "").lower()

                        if "code" in content or "def " in content:
                            return f"Here is your code:\n{fact.content}"

                    except:
                        continue

        # ✅ STEP 4: fallback AI
        try:
            response = self.client.chat(
                model="llama3.2",
                messages=[{"role": "user", "content": message}]
            )

            return response["message"]["content"].strip()

        except Exception:
            return "Something went wrong."