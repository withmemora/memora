"""Memora CLI interface."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import track
from rich.table import Table

app = typer.Typer(name="memora", help="Git-style versioned memory for LLMs")
console = Console()


@app.command()
def version():
    """Show version information."""
    console.print("Memora 0.1.0", style="bold green")


@app.command()
def init(path: str = typer.Option("./memora_data", help="Path to initialize memory storage")):
    """Initialize a new Memora repository."""
    storage_path = Path(path)
    storage_path.mkdir(parents=True, exist_ok=True)
    console.print(f"Memora repository initialized at: {storage_path}", style="green")


@app.command()
def chat(
    model: str = typer.Option("llama3.2:3b", help="Ollama model to use"),
    branch: str = typer.Option("main", help="Memory branch to use"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show memory extractions"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory storage"),
):
    """Start interactive AI chat with memory context.

    This starts a terminal-based chat loop where you can converse with an AI
    that automatically stores and recalls memories from your conversations.

    Example:
        memora chat --verbose
        memora chat --model llama3.2 --branch work
    """
    try:
        from memora.ai.conversational_ai import MemoraChat
    except ImportError:
        console.print("Error: AI module not found", style="red")
        return

    # Initialize chat
    try:
        chat_instance = MemoraChat(model=model, branch=branch, memory_path=memory_path)
    except Exception as e:
        console.print(f" Error initializing chat: {e}", style="red")
        console.print("\nMake sure Ollama is installed and running:", style="yellow")
        console.print("  curl -fsSL https://ollama.ai/install.sh | sh", style="cyan")
        console.print(f"  ollama pull {model}", style="cyan")
        return

    # Display welcome message
    console.print(f"\n Memora Chat", style="bold blue")
    console.print(f"Model: {model} | Branch: {branch}", style="dim")
    console.print("Type 'exit' or 'quit' to end the conversation\n", style="dim")

    # Interactive chat loop
    while True:
        try:
            # Get user input
            user_input = console.input("[bold cyan]You:[/bold cyan] ")

            if user_input.lower().strip() in ["exit", "quit", "q"]:
                console.print("\n Chat session ended.", style="green")
                break

            if not user_input.strip():
                continue

            # Get AI response
            try:
                response = chat_instance.chat(user_input, verbose=verbose)
                console.print(f"[bold green]AI:[/bold green] {response}\n")
            except KeyboardInterrupt:
                console.print("\n Chat session ended.", style="green")
                break
            except Exception as e:
                console.print(f" Error: {e}", style="red")

        except KeyboardInterrupt:
            console.print("\n Chat session ended.", style="green")
            break
        except EOFError:
            console.print("\n Chat session ended.", style="green")
            break


@app.command()
def ingest(
    path: str = typer.Argument(help="File or directory path to ingest"),
    recursive: bool = typer.Option(
        False, "--recursive", "-r", help="Process directories recursively"
    ),
    file_types: str = typer.Option("txt,md,pdf", help="Comma-separated file extensions to process"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory storage"),
):
    """Ingest documents and extract memories.

    Process text files, Markdown files, and PDFs to extract facts and store them
    as memories. Supports both individual files and batch directory processing.

    Examples:
        memora ingest document.txt
        memora ingest documents/ --recursive
        memora ingest docs/ --file-types txt,md
    """
    try:
        from memora.ai.file_processor import FileProcessor
        from memora.interface.api import MemoraStore
    except ImportError as e:
        console.print(f" Error importing modules: {e}", style="red")
        return

    # Initialize processor and store
    processor = FileProcessor()
    memory_store = MemoraStore(memory_path)

    path_obj = Path(path)

    if not path_obj.exists():
        console.print(f" Path not found: {path}", style="red")
        return

    # Collect files to process
    files_to_process = []
    extensions = [ext.strip().lower().strip(".") for ext in file_types.split(",")]

    if path_obj.is_file():
        files_to_process = [path_obj]
    elif path_obj.is_dir():
        for ext in extensions:
            pattern = f"**/*.{ext}" if recursive else f"*.{ext}"
            files_to_process.extend(path_obj.glob(pattern))

    if not files_to_process:
        console.print(f"  No files found matching criteria", style="yellow")
        return

    console.print(f" Processing {len(files_to_process)} file(s)...\n", style="blue")

    # Process files
    total_facts = 0
    successful = 0
    failed = 0

    for file_path in track(files_to_process, description="Processing files"):
        try:
            facts = processor.process_file(str(file_path))

            # Store each fact
            for fact in facts:
                memory_store.add(fact.content, source=fact.source)

            total_facts += len(facts)
            successful += 1

            if facts:
                console.print(f"   {file_path.name}: {len(facts)} memories", style="green")
        except Exception as e:
            failed += 1
            console.print(f"   {file_path.name}: {e}", style="red")

    # Summary
    console.print(f"\n Summary:", style="bold")
    console.print(f"  Files processed: {successful}/{len(files_to_process)}")
    console.print(f"  Total memories extracted: {total_facts}")
    if failed > 0:
        console.print(f"  Failed: {failed}", style="red")


@app.command()
def branch(
    action: str = typer.Argument(help="Action: list, create, switch, or delete"),
    name: Optional[str] = typer.Option(None, help="Branch name for create/switch/delete"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory storage"),
):
    """Memory branch management.

    Manage memory branches to organize memories by context or topic.

    Examples:
        memora branch list
        memora branch create work-project
        memora branch switch personal
        memora branch delete old-branch
    """
    try:
        from memora.interface.api import MemoraStore
    except ImportError:
        console.print(" Error importing MemoraStore", style="red")
        return

    memory_store = MemoraStore(memory_path)

    if action == "list":
        # List all branches
        console.print(" Available branches:", style="bold")
        console.print("  • main (default)", style="green")
        console.print("\nNote: Full branch management coming soon!", style="dim")

    elif action == "create":
        if not name:
            console.print(" Branch name required for create action", style="red")
            return
        console.print(f" Created branch: {name}", style="green")
        console.print("Note: Full branch management coming soon!", style="dim")

    elif action == "switch":
        if not name:
            console.print(" Branch name required for switch action", style="red")
            return
        console.print(f" Switched to branch: {name}", style="green")
        console.print("Note: Full branch management coming soon!", style="dim")

    elif action == "delete":
        if not name:
            console.print(" Branch name required for delete action", style="red")
            return
        if name == "main":
            console.print(" Cannot delete main branch", style="red")
            return
        console.print(f" Deleted branch: {name}", style="green")
        console.print("Note: Full branch management coming soon!", style="dim")

    else:
        console.print(f" Unknown action: {action}", style="red")
        console.print("Valid actions: list, create, switch, delete", style="yellow")


@app.command()
def search(
    query: str = typer.Argument(help="Search query"),
    limit: int = typer.Option(10, help="Maximum number of results"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory storage"),
):
    """Search stored memories.

    Search through all stored memories and display matching results.

    Example:
        memora search "Python programming"
        memora search "project deadline" --limit 20
    """
    try:
        from memora.interface.api import MemoraStore
    except ImportError:
        console.print(" Error importing MemoraStore", style="red")
        return

    memory_store = MemoraStore(memory_path)

    console.print(f" Searching for: '{query}'\n", style="blue")

    try:
        results = memory_store.search(query, limit=limit)

        if not results:
            console.print("No memories found", style="yellow")
            return

        # Display results
        for i, result in enumerate(results, 1):
            memory_text = result.get("memory", "")
            source = result.get("source", "unknown")

            console.print(f"{i}. {memory_text}", style="green")
            console.print(f"   Source: {source}", style="dim")
            console.print()

        console.print(f"Found {len(results)} memories", style="bold")

    except Exception as e:
        console.print(f" Error searching: {e}", style="red")


@app.command()
def add(
    text: str = typer.Argument(help="Text to add as memory"),
    source: str = typer.Option("cli", help="Source attribution"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory storage"),
):
    """Add a memory manually.

    Manually add text to memory storage. Facts will be automatically extracted.

    Example:
        memora add "My favorite programming language is Python"
        memora add "Project deadline is March 30th" --source "meeting-notes"
    """
    try:
        from memora.interface.api import MemoraStore
    except ImportError:
        console.print(" Error importing MemoraStore", style="red")
        return

    memory_store = MemoraStore(memory_path)

    try:
        result = memory_store.add(text, source=source)
        facts_count = result.get("facts_extracted", 0)

        console.print(f" Memory added successfully", style="green")
        console.print(f"Extracted {facts_count} fact(s)", style="dim")

    except Exception as e:
        console.print(f" Error adding memory: {e}", style="red")


@app.command()
def stats(memory_path: str = typer.Option("./memora_data", help="Path to memory storage")):
    """Display memory statistics.

    Show statistics about stored memories including counts, sources, and more.
    """
    try:
        from memora.interface.api import MemoraStore
    except ImportError:
        console.print(" Error importing MemoraStore", style="red")
        return

    memory_store = MemoraStore(memory_path)

    console.print("Memory Statistics\n", style="bold blue")

    try:
        all_memories = memory_store.get_all()

        console.print(f"Total memories: {len(all_memories)}", style="green")
        console.print(f"Storage path: {memory_path}", style="dim")
        console.print("\nNote: Enhanced analytics coming soon!", style="dim")

    except Exception as e:
        console.print(f" Error getting statistics: {e}", style="red")


@app.command()
def proxy(
    action: str = typer.Argument(help="Action: start, stop, or status"),
    port: int = typer.Option(11435, help="Proxy port"),
    ollama_host: str = typer.Option("http://localhost:11434", help="Ollama service URL"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory storage"),
    background: bool = typer.Option(False, help="Run in background (daemon mode)"),
    show_logs: bool = typer.Option(True, "--show-logs", help="Show memory capture logs"),
):
    """Manage the Ollama proxy for automatic memory capture.

    The proxy sits between Ollama clients and the Ollama service,
    transparently capturing memories from all conversations.

    Examples:
        memora proxy start
        memora proxy start --port 11435 --background
        memora proxy stop
        memora proxy status
    """
    if action == "start":
        _start_proxy(port, ollama_host, memory_path, background, show_logs)
    elif action == "stop":
        _stop_proxy(port)
    elif action == "status":
        _proxy_status(port)
    else:
        console.print(f"Unknown action: {action}", style="red")
        console.print("Valid actions: start, stop, status", style="yellow")


def _start_proxy(port: int, ollama_host: str, memory_path: str, background: bool, show_logs: bool):
    """Start the proxy server."""
    import subprocess
    import socket

    # Check if proxy is already running
    if _is_port_in_use(port):
        console.print(f"Port {port} is already in use", style="yellow")
        console.print(
            "The proxy may already be running. Use 'memora proxy status' to check.", style="dim"
        )
        return

    # Check if Ollama is running
    try:
        import httpx

        client = httpx.Client(timeout=5.0)
        response = client.get(f"{ollama_host}/api/tags")
        if response.status_code != 200:
            raise Exception("Ollama not responding")
    except Exception:
        console.print("Cannot connect to Ollama service", style="red")
        console.print(f"   Make sure Ollama is running at: {ollama_host}", style="yellow")
        console.print("\nTo start Ollama:", style="dim")
        console.print("   • Open the Ollama app, or", style="dim")
        console.print("   • Run: ollama serve", style="dim")
        return

    if background:
        # Run proxy in background
        console.print(f"Starting Memora proxy in background on port {port}...", style="blue")

        try:
            import sys
            import os

            python_exe = sys.executable

            # Prepare environment
            env = os.environ.copy()
            env.update(
                {
                    "MEMORA_PROXY_PORT": str(port),
                    "MEMORA_OLLAMA_HOST": ollama_host,
                    "MEMORA_MEMORY_PATH": memory_path,
                    "MEMORA_VERBOSE": str(show_logs).lower(),
                }
            )

            # Create a Python script to run the proxy
            proxy_script = f"""
import sys
from memora.ai.ollama_proxy import start_proxy

start_proxy(
    ollama_host="{ollama_host}",
    proxy_port={port},
    memory_path="{memory_path}",
    verbose={show_logs}
)
"""

            # Create a detached background process
            if sys.platform == "win32":
                # Windows: Use CREATE_NO_WINDOW
                subprocess.Popen(
                    [python_exe, "-c", proxy_script],
                    env=env,
                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                # Unix: Use nohup-style detach
                subprocess.Popen(
                    [python_exe, "-c", proxy_script],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )

            # Give it a moment to start
            import time

            time.sleep(2)

            if _is_port_in_use(port):
                console.print(f"Proxy started successfully on port {port}", style="green")
                console.print(f"\nNext steps:", style="bold blue")
                console.print(f"   Set environment variable:", style="dim")
                console.print(f"      export OLLAMA_HOST=http://localhost:{port}", style="cyan")
                console.print(
                    f"\n   Then use Ollama normally - memories will be captured automatically!",
                    style="dim",
                )
            else:
                console.print("Proxy may not have started correctly", style="yellow")

        except Exception as e:
            console.print(f"Error starting background proxy: {e}", style="red")
    else:
        # Run proxy in foreground
        console.print(f" Starting Memora proxy on port {port}...", style="blue")
        console.print("   Press Ctrl+C to stop\n", style="dim")

        try:
            from memora.ai.ollama_proxy import start_proxy

            start_proxy(
                ollama_host=ollama_host,
                proxy_port=port,
                memory_path=memory_path,
                verbose=show_logs,
            )
        except KeyboardInterrupt:
            console.print("\n Proxy stopped", style="green")
        except Exception as e:
            console.print(f"\n Error running proxy: {e}", style="red")


def _stop_proxy(port: int):
    """Stop the proxy server."""
    if not _is_port_in_use(port):
        console.print(f"  No proxy running on port {port}", style="yellow")
        return

    console.print(f"  Stopping proxy on port {port}...", style="yellow")
    console.print("Note: You may need to manually kill the process", style="dim")

    # Try to find and kill the process
    import subprocess
    import sys

    try:
        if sys.platform == "win32":
            # Windows: Find process using netstat
            result = subprocess.run(
                ["netstat", "-ano", "-p", "TCP"],
                capture_output=True,
                text=True,
            )
            for line in result.stdout.split("\n"):
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    pid = parts[-1]
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
                    console.print(f" Stopped proxy (PID: {pid})", style="green")
                    return
        else:
            # Unix: Use lsof
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
            )
            if result.stdout.strip():
                pid = result.stdout.strip()
                subprocess.run(["kill", pid], capture_output=True)
                console.print(f" Stopped proxy (PID: {pid})", style="green")
                return

        console.print(" Could not find proxy process", style="red")

    except Exception as e:
        console.print(f" Error stopping proxy: {e}", style="red")


def _proxy_status(port: int):
    """Check proxy status."""
    console.print(f" Checking proxy status on port {port}...\n", style="blue")

    if _is_port_in_use(port):
        console.print(f" Proxy is running on port {port}", style="green")

        # Try to get process info
        import subprocess
        import sys

        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["netstat", "-ano", "-p", "TCP"],
                    capture_output=True,
                    text=True,
                )
                for line in result.stdout.split("\n"):
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        pid = parts[-1]
                        console.print(f"   PID: {pid}", style="dim")
                        break
            else:
                result = subprocess.run(
                    ["lsof", "-ti", f":{port}"],
                    capture_output=True,
                    text=True,
                )
                if result.stdout.strip():
                    pid = result.stdout.strip()
                    console.print(f"   PID: {pid}", style="dim")
        except Exception:
            pass

        console.print(f"\n Configuration:", style="bold")
        console.print(f"   Set environment variable to use proxy:", style="dim")
        console.print(f"      export OLLAMA_HOST=http://localhost:{port}", style="cyan")
    else:
        console.print(f" No proxy running on port {port}", style="red")
        console.print("\n   Start the proxy with:", style="dim")
        console.print("      memora proxy start", style="cyan")


def _is_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("localhost", port))
            return False
        except OSError:
            return True


@app.command()
def setup(
    port: int = typer.Option(11435, help="Proxy port"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory storage"),
):
    """Interactive setup wizard for Memora.

    Walks you through setting up the Ollama proxy and configuring
    your environment for automatic memory capture.

    Example:
        memora setup
    """
    console.print("\n Memora Setup Wizard\n", style="bold blue")
    console.print("This will help you set up automatic memory capture from Ollama.\n")

    # Step 1: Check Ollama
    console.print(" Step 1: Checking Ollama installation...", style="bold")

    try:
        import httpx

        client = httpx.Client(timeout=5.0)
        response = client.get("http://localhost:11434/api/tags")

        if response.status_code == 200:
            console.print("    Ollama is installed and running", style="green")

            # Show available models
            data = response.json()
            models = data.get("models", [])
            if models:
                console.print(
                    f"   Available models: {', '.join([m['name'] for m in models[:3]])}",
                    style="dim",
                )
        else:
            raise Exception("Ollama not responding")

    except Exception:
        console.print("    Ollama is not running", style="red")
        console.print("\n   Please start Ollama first:", style="yellow")
        console.print("      • Open the Ollama app, or", style="dim")
        console.print("      • Run: ollama serve", style="dim")
        console.print("\n   Then run 'memora setup' again.", style="dim")
        return

    # Step 2: Initialize storage
    console.print("\n Step 2: Initializing memory storage...", style="bold")
    storage_path = Path(memory_path)
    storage_path.mkdir(parents=True, exist_ok=True)
    console.print(f"    Storage initialized at: {storage_path.absolute()}", style="green")

    # Step 3: Start proxy
    console.print("\n Step 3: Starting proxy server...", style="bold")

    if _is_port_in_use(port):
        console.print(f"     Port {port} is already in use", style="yellow")
        console.print("   The proxy may already be running.", style="dim")
    else:
        # Start in background
        import subprocess
        import sys
        import time
        import os

        try:
            python_exe = sys.executable

            # Prepare environment
            env = os.environ.copy()
            env.update(
                {
                    "MEMORA_PROXY_PORT": str(port),
                    "MEMORA_OLLAMA_HOST": "http://localhost:11434",
                    "MEMORA_MEMORY_PATH": memory_path,
                    "MEMORA_VERBOSE": "true",
                }
            )

            # Create a Python script to run the proxy
            proxy_script = f"""
from memora.ai.ollama_proxy import start_proxy
start_proxy(
    ollama_host="http://localhost:11434",
    proxy_port={port},
    memory_path="{memory_path}",
    verbose=True
)
"""

            if sys.platform == "win32":
                subprocess.Popen(
                    [python_exe, "-c", proxy_script],
                    env=env,
                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                subprocess.Popen(
                    [python_exe, "-c", proxy_script],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )

            time.sleep(2)

            if _is_port_in_use(port):
                console.print(f"    Proxy started on port {port}", style="green")
            else:
                console.print("     Proxy may not have started", style="yellow")

        except Exception as e:
            console.print(f"    Error starting proxy: {e}", style="red")
            return

    # Step 4: Configuration instructions
    console.print("\n Step 4: Configure Ollama to use proxy...", style="bold")
    console.print("\n   Add this to your environment:", style="dim")

    import sys

    if sys.platform == "win32":
        console.print(f"\n   For PowerShell:", style="bold")
        console.print(f"      $env:OLLAMA_HOST='http://localhost:{port}'", style="cyan")
        console.print(f"\n   For Command Prompt:", style="bold")
        console.print(f"      set OLLAMA_HOST=http://localhost:{port}", style="cyan")
        console.print(
            f"\n   To make it permanent, add to System Environment Variables", style="dim"
        )
    else:
        console.print(f"\n   For current session:", style="bold")
        console.print(f"      export OLLAMA_HOST=http://localhost:{port}", style="cyan")
        console.print(f"\n   To make it permanent, add to ~/.bashrc or ~/.zshrc:", style="bold")
        console.print(
            f"      echo 'export OLLAMA_HOST=http://localhost:{port}' >> ~/.bashrc", style="cyan"
        )

    # Step 5: Test
    console.print("\n Step 5: Test the setup...", style="bold")
    console.print("\n   After setting OLLAMA_HOST, try:", style="dim")
    console.print("      ollama run llama3.2:3b", style="cyan")
    console.print("\n   Have a conversation, then check captured memories:", style="dim")
    console.print('      memora search ""', style="cyan")

    # Success
    console.print("\n Setup complete!", style="bold green")
    console.print(
        "\nMemora is now ready to capture memories from all your Ollama conversations.", style="dim"
    )


if __name__ == "__main__":
    app()
