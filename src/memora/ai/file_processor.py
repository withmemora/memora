from pathlib import Path
from memora.core.ingestion import extract_facts
from memora.core.store import ObjectStore


class FileProcessor:

    def __init__(self):
        self.store = ObjectStore(Path(".memora"))

    def process_file(self, file_path: str):

        path = Path(file_path)

        if not path.exists():
            raise ValueError("File not found")

        # 1. Read file
        if path.suffix == ".txt" or path.suffix == ".md":
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            raise ValueError("Only .txt and .md supported")

        # 2. Extract facts
        facts = extract_facts(content, f"file:{path.name}")

        # 3. Store facts
        for f in facts:
            self.store.write(f)

        return len(facts)