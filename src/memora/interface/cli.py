"""Memora CLI interface."""

import typer
from memora.ai.conversational_ai import MemoraChat
from memora.ai.file_processor import FileProcessor
from memora.core.store import ObjectStore
from pathlib import Path

app = typer.Typer(name="memora", help="Git-style versioned memory for LLMs")

@app.command()
def search(query: str):
    """Search memory"""
    store = ObjectStore(Path(".memora"))

    results = store.search(query)

    if not results:
        print("No results found")
    else:
        print("Results:")
        for r in results:
            print("-", r)
            
@app.command()
def version():
    """Show version information."""
    print("Memora 0.1.0")


@app.command()
def init():
    """Initialize a new Memora repository."""
    print("Memora repository initialized")


@app.command()
def chat():
    """Start AI chat with memory."""
    bot = MemoraChat()

    print("Start chatting (type exit to quit)")

    while True:
        msg = input("You: ")
        if msg.lower() == "exit":
            break

        response = bot.chat(msg)
        print("AI:", response)

@app.command()
def ingest(path: str):
    """Ingest a file and extract memory"""
    processor = FileProcessor()

    try:
        count = processor.process_file(path)
        print(f"Processed {count} facts from file")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    app()