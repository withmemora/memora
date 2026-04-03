"""Memora CLI interface v3.0."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="memora", help="Git-style versioned memory for LLMs")
console = Console()


@app.command()
def version():
    """Show version information."""
    console.print("Memora 3.0.0", style="bold green")


@app.command()
def init(path: str = typer.Option("./memora_data", help="Path to initialize")):
    """Initialize a new Memora repository."""
    from memora.core.engine import CoreEngine

    storage_path = Path(path)
    storage_path.mkdir(parents=True, exist_ok=True)
    engine = CoreEngine()
    try:
        engine.init_store(storage_path)
        console.print(f"Memora repository initialized at: {storage_path}", style="green")
    except Exception as e:
        if "already exists" in str(e):
            console.print(f"Memora store already exists at: {storage_path}", style="yellow")
        else:
            console.print(f"Error: {e}", style="red")


@app.command()
def search(query: str, memory_path: str = typer.Option("./memora_data", help="Path to memory")):
    """Search stored memories."""
    from memora.core.engine import CoreEngine

    engine = CoreEngine()
    try:
        engine.open_store(Path(memory_path))
    except Exception:
        console.print("No Memora store found. Run 'memora init' first.", style="red")
        return
    results = engine.search_memories(query)
    if not results:
        console.print("No memories found.", style="yellow")
        return
    table = Table(title=f"Search results for '{query}'")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Content", style="white")
    table.add_column("Confidence", style="yellow")
    for m in results:
        table.add_row(m.id[:16], m.memory_type.value, m.content[:80], f"{m.confidence:.2f}")
    console.print(table)


@app.command()
def stats(memory_path: str = typer.Option("./memora_data", help="Path to memory")):
    """Show memory statistics."""
    from memora.core.engine import CoreEngine

    engine = CoreEngine()
    try:
        engine.open_store(Path(memory_path))
    except Exception:
        console.print("No Memora store found.", style="red")
        return
    s = engine.get_store_stats()
    table = Table(title="Memora Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    for k, v in s.items():
        table.add_row(k.replace("_", " ").title(), str(v))
    console.print(table)


@app.command()
def where(memory_path: str = typer.Option("./memora_data", help="Path to memory")):
    """Show where memory data is stored."""
    console.print(f"Memory storage: {Path(memory_path).absolute()}", style="green")
    console.print(f"Store directory: {Path(memory_path) / '.memora'}", style="green")


@app.command()
def ingest(file_path: str, memory_path: str = typer.Option("./memora_data", help="Path to memory")):
    """Ingest a document and extract memories."""
    from memora.core.engine import CoreEngine

    engine = CoreEngine()
    try:
        engine.open_store(Path(memory_path))
    except Exception:
        console.print("No Memora store found.", style="red")
        return
    try:
        results = engine.ingest_file(file_path)
        console.print(f"Ingested {len(results)} memories from {file_path}", style="green")
        for _, m in results:
            console.print(f"  {m.content[:100]}", style="dim")
    except Exception as e:
        console.print(f"Error: {e}", style="red")


@app.command()
def chat(
    model: str = typer.Option("llama3.2:3b", help="Ollama model"),
    branch: str = typer.Option("main", help="Memory branch"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory"),
):
    """Start interactive AI chat with memory context."""
    try:
        from memora.ai.conversational_ai import MemoraChat

        chat_instance = MemoraChat(model=model, branch=branch, memory_path=memory_path)
    except Exception as e:
        console.print(f"Error initializing chat: {e}", style="red")
        return
    console.print(f"Memora Chat - Model: {model} | Branch: {branch}", style="bold blue")
    console.print("Type 'exit' to end\n", style="dim")
    while True:
        try:
            user_input = console.input("[bold cyan]You:[/bold cyan] ")
            if user_input.lower().strip() in ["exit", "quit", "q"]:
                break
            if not user_input.strip():
                continue
            response = chat_instance.chat(user_input)
            console.print(f"[bold green]AI:[/bold green] {response}\n")
        except KeyboardInterrupt:
            break


@app.command()
def proxy(
    action: str = typer.Argument(..., help="start, stop, or status"),
    port: int = typer.Option(11435, help="Proxy port"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory"),
):
    """Manage Ollama proxy."""
    if action == "start":
        console.print(f"Starting Memora proxy on port {port}...", style="green")
        from memora.ai.ollama_proxy import start_proxy

        start_proxy(proxy_port=port, memory_path=memory_path)
    elif action == "status":
        console.print("Proxy status: check if port 11435 is listening", style="yellow")
    elif action == "stop":
        console.print("Stop the proxy process manually (Ctrl+C)", style="yellow")
    else:
        console.print("Usage: memora proxy [start|stop|status]", style="red")


@app.command(name="proxy-setup")
def proxy_setup(action: str = typer.Argument(..., help="enable or disable")):
    """Configure OLLAMA_HOST system-wide."""
    import os
    import subprocess

    if action == "enable":
        try:
            subprocess.run(["setx", "OLLAMA_HOST", "http://localhost:11435"], check=True)
            console.print("OLLAMA_HOST set system-wide. Restart Ollama for changes.", style="green")
        except Exception:
            os.environ["OLLAMA_HOST"] = "http://localhost:11435"
            console.print("OLLAMA_HOST set for current session only.", style="yellow")
    elif action == "disable":
        try:
            subprocess.run(["setx", "OLLAMA_HOST", ""], check=True)
            console.print("OLLAMA_HOST removed.", style="green")
        except Exception:
            console.print("Run 'setx OLLAMA_HOST \"\"' manually.", style="yellow")
    else:
        console.print("Usage: memora proxy-setup [enable|disable]", style="red")


@app.command()
def branch(
    action: str = typer.Argument("list", help="list, create, switch, status"),
    name: str = typer.Argument(None, help="Branch name"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory"),
):
    """Manage branches."""
    from memora.core.engine import CoreEngine

    engine = CoreEngine()
    try:
        engine.open_store(Path(memory_path))
    except Exception:
        console.print("No Memora store found.", style="red")
        return

    if action == "list":
        branches = engine.list_branches()
        current = engine.get_current_branch() or "main"
        table = Table(title="Branches")
        table.add_column("Name", style="cyan")
        table.add_column("Commit", style="dim")
        table.add_column("Current", style="green")
        for bname, chash in branches:
            table.add_row(bname, chash[:12] if chash else "none", "*" if bname == current else "")
        console.print(table)
    elif action == "create":
        if not name:
            console.print("Usage: memora branch create <name>", style="red")
            return
        engine.create_branch(name)
        console.print(f"Branch '{name}' created", style="green")
    elif action == "switch":
        if not name:
            console.print("Usage: memora branch switch <name>", style="red")
            return
        engine.switch_branch(name)
        console.print(f"Switched to branch '{name}'", style="green")
    elif action == "status":
        status = engine.get_branch_status()
        all_status = engine.get_all_branches_status()
        table = Table(title="Branch Status")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Sessions", style="yellow")
        table.add_column("Memories", style="yellow")
        for b in all_status:
            table.add_row(
                b["name"],
                b["status"],
                f"{b['session_count']}/{b['session_limit']}",
                f"{b['memory_count']}/{b['memory_limit']}",
            )
        console.print(table)
    else:
        console.print("Usage: memora branch [list|create|switch|status]", style="red")


@app.command()
def session(
    action: str = typer.Argument("list", help="list, active"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory"),
):
    """Manage sessions."""
    from memora.core.engine import CoreEngine

    engine = CoreEngine()
    try:
        engine.open_store(Path(memory_path))
    except Exception:
        console.print("No Memora store found.", style="red")
        return

    if action == "list":
        sessions = engine.list_sessions()
        if not sessions:
            console.print("No sessions found.", style="yellow")
            return
        table = Table(title="Sessions")
        table.add_column("ID", style="cyan")
        table.add_column("Branch", style="green")
        table.add_column("Started", style="dim")
        table.add_column("Ended", style="dim")
        table.add_column("Memories", style="yellow")
        table.add_column("Status", style="white")
        for s in sessions:
            table.add_row(
                s.id,
                s.branch,
                s.started_at[:19],
                (s.ended_at or "active")[:19] if s.ended_at else "active",
                str(len(s.memory_ids)),
                "closed" if s.ended_at else "open",
            )
        console.print(table)
    elif action == "active":
        s = engine.get_active_session()
        if s:
            console.print(f"Active session: {s.id}", style="green")
            console.print(f"Branch: {s.branch}", style="dim")
            console.print(f"Memories: {len(s.memory_ids)}", style="dim")
        else:
            console.print("No active session.", style="yellow")
    else:
        console.print("Usage: memora session [list|active]", style="red")


@app.command()
def graph(
    entity: Optional[str] = typer.Argument(None, help="Entity to query"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory"),
):
    """Show knowledge graph."""
    from memora.core.engine import CoreEngine

    engine = CoreEngine()
    try:
        engine.open_store(Path(memory_path))
    except Exception:
        console.print("No Memora store found.", style="red")
        return

    if entity:
        edges = engine.graph_query(entity)
        if not edges:
            console.print(f"No graph data for '{entity}'", style="yellow")
            return
        table = Table(title=f"Graph: {entity}")
        table.add_column("Relation", style="cyan")
        table.add_column("Target", style="green")
        table.add_column("Confidence", style="yellow")
        for e in edges:
            target = e["target"] if e["source"] == entity.lower().replace(" ", "_") else e["source"]
            table.add_row(e["relation"], target, f"{e['confidence']:.2f}")
        console.print(table)
    else:
        profile = engine.get_graph_profile()
        nodes = engine.get_graph_nodes()
        console.print("Knowledge Graph", style="bold blue")
        console.print(f"Nodes: {len(nodes)}", style="dim")
        if profile.get("works_at"):
            console.print(f"Works at: {', '.join(profile['works_at'])}", style="green")
        if profile.get("knows"):
            console.print(f"Knows: {', '.join(profile['knows'])}", style="green")
        if profile.get("building"):
            console.print(f"Building: {', '.join(profile['building'])}", style="green")


@app.command()
def forget(
    memory_id: str = typer.Argument(..., help="Memory ID to forget/delete"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory"),
):
    """Forget a specific memory. Selective forgetting."""
    from memora.core.engine import CoreEngine

    engine = CoreEngine()
    try:
        engine.open_store(Path(memory_path))
    except Exception:
        console.print("No Memora store found.", style="red")
        return
    deleted = engine.forget_memory(memory_id)
    if deleted:
        console.print(f"Memory {memory_id} deleted", style="green")
    else:
        console.print(f"Memory {memory_id} not found", style="red")


@app.command()
def rollback(commit: str, memory_path: str = typer.Option("./memora_data", help="Path to memory")):
    """Roll back to a previous commit."""
    console.print(f"Rollback to {commit[:8]} - feature coming soon", style="yellow")


@app.command()
def export(
    format: str = typer.Option("markdown", help="Export format: markdown, json, text"),
    branch: Optional[str] = typer.Option(None, help="Branch to export"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory"),
):
    """Export memories."""
    from memora.core.engine import CoreEngine

    engine = CoreEngine()
    try:
        engine.open_store(Path(memory_path))
    except Exception:
        console.print("No Memora store found.", style="red")
        return
    exported = engine.export_memories(format=format, branch=branch)
    console.print(exported)


@app.command()
def setup():
    """Interactive setup wizard."""
    console.print("Memora Setup", style="bold blue")
    console.print("1. Make sure Ollama is installed and running")
    console.print("2. Run: memora init")
    console.print("3. Run: memora proxy start")
    console.print("4. Configure your Ollama client to use http://localhost:11435")
    console.print("5. Start chatting!", style="green")


if __name__ == "__main__":
    app()
