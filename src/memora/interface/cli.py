"""Memora CLI interface v3.1."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from memora.shared.models import MemorySource
from memora.core.console_utils import create_safe_console, safe_print, ICONS

app = typer.Typer(name="memora", help="Git-style versioned memory for LLMs")
console = create_safe_console()


def check_port_available(port: int) -> bool:
    """Check if a port is available for use."""
    import socket

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)  # Quick timeout
            result = s.connect_ex(("localhost", port))
            return result != 0  # 0 means connection successful (port in use)
    except socket.error:
        return True  # Assume available if we can't test


def ensure_spacy_model():
    """Ensure spaCy model is available, download if missing."""
    try:
        import spacy

        spacy.load("en_core_web_sm")
        safe_print(console, f"{ICONS['check']} spaCy language model available", style="green")
    except OSError:
        safe_print(
            console,
            f"{ICONS['import']} Downloading spaCy language model (one-time, ~12MB)...",
            style="yellow",
        )
        try:
            import subprocess

            subprocess.run(
                [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
                check=True,
                capture_output=True,
            )
            safe_print(console, f"{ICONS['check']} Language model downloaded", style="green")
        except subprocess.CalledProcessError as e:
            safe_print(
                console, f"{ICONS['warning']} Failed to download spaCy model: {e}", style="red"
            )
            console.print("NER functionality will be disabled", style="yellow")
    except ImportError:
        safe_print(
            console, f"{ICONS['warning']} spaCy not installed. Run: pip install spacy", style="red"
        )
        console.print("NER functionality will be disabled", style="yellow")


@app.command()
def version():
    """Show version information."""
    console.print("Memora 3.1.0", style="bold green")


def check_version_compatibility(store_path: Path) -> bool:
    """Check if store version is compatible with current Memora version.

    Returns True if compatible, False if migration needed.
    """
    config_file = store_path / ".memora" / "config"
    if not config_file.exists():
        return True  # Fresh init, no version check needed

    try:
        import json

        config = json.loads(config_file.read_text())
        stored_version = config.get("core", {}).get("version", "1.0")
        current_version = "3.1"

        if stored_version == current_version:
            return True  # All good

        # Check major version compatibility
        try:
            major_stored = int(stored_version.split(".")[0])
            major_current = int(current_version.split(".")[0])

            if major_stored < major_current:
                console.print(
                    f"⚠ Your store was created with Memora v{stored_version}.", style="yellow"
                )
                console.print(f"  Current version is v{current_version}.", style="yellow")
                console.print(f"  Run 'memora migrate' to upgrade your store.", style="yellow")
                console.print(
                    f"  Or run 'memora migrate --dry-run' to preview changes.", style="yellow"
                )
                return False

            # Minor version difference - auto-update config silently
            if stored_version != current_version:
                config["core"]["version"] = current_version
                config_file.write_text(json.dumps(config, indent=2))
                console.print(
                    f"✓ Updated config from v{stored_version} to v{current_version}", style="green"
                )
        except (ValueError, IndexError):
            # Invalid version format, proceed anyway
            pass

        return True
    except Exception as e:
        console.print(f"⚠ Could not check version: {e}", style="yellow")
        return True  # Proceed anyway


@app.command()
def migrate(
    dry_run: bool = typer.Option(False, help="Show what would change without doing it"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory store"),
):
    """Upgrade store from old version to current version."""
    store_path = Path(memory_path)
    config_file = store_path / ".memora" / "config"

    if not config_file.exists():
        console.print("✗ No Memora store found at this location", style="red")
        return

    try:
        import json

        config = json.loads(config_file.read_text())
        stored_version = config.get("core", {}).get("version", "1.0")
        current_version = "3.1"

        console.print(f"Current store version: {stored_version}", style="yellow")
        console.print(f"Target version: {current_version}", style="green")

        if stored_version == current_version:
            console.print("✓ Store is already at the current version", style="green")
            return

        if dry_run:
            console.print("\n[DRY RUN] Would perform the following changes:", style="bold yellow")
            console.print(f"  - Update config version: {stored_version} → {current_version}")
            console.print(f"  - Add new config sections: [sessions], [index] settings")
            console.print("No files will be modified in dry-run mode.", style="yellow")
            return

        # Perform migration
        console.print("\n🔄 Migrating store...", style="bold blue")

        # Update version
        config["core"]["version"] = current_version

        # Add new config sections if missing
        if "sessions" not in config:
            config["sessions"] = {
                "keep_closed_days": 30,
                "archive_enabled": True,
            }
            console.print("  ✓ Added [sessions] config section", style="green")

        if "index" not in config:
            config["index"] = {
                "enable_word_index": True,
                "enable_temporal_index": True,
                "enable_session_index": True,
                "lru_cache_size": 1000,
                "word_index_archive_days": 365,
                "lazy_load_threshold_mb": 1,
            }
        else:
            # Update existing index config with new settings
            if "word_index_archive_days" not in config["index"]:
                config["index"]["word_index_archive_days"] = 365
                console.print("  ✓ Added index archiving settings", style="green")
            if "lazy_load_threshold_mb" not in config["index"]:
                config["index"]["lazy_load_threshold_mb"] = 1

        # Save updated config
        config_file.write_text(json.dumps(config, indent=2))
        console.print(
            f"\n✓ Migration complete: {stored_version} → {current_version}", style="bold green"
        )

    except Exception as e:
        console.print(f"✗ Migration failed: {e}", style="red")
        import traceback

        console.print(traceback.format_exc(), style="red")


@app.command()
def start(
    memory_path: str = typer.Option("./memora_data", help="Path to memory"),
    port: int = typer.Option(11435, help="Proxy port"),
    auto_setup: bool = typer.Option(True, help="Automatically configure OLLAMA_HOST"),
):
    """Single command to start Memora: init + proxy + setup."""
    import os
    import subprocess
    from memora.core.engine import CoreEngine

    storage_path = Path(memory_path)

    # Step 1: Initialize if needed
    safe_print(console, f"{ICONS['rocket']} Starting Memora...", style="bold blue")
    storage_path.mkdir(parents=True, exist_ok=True)

    # Step 1.5: Check version compatibility
    if not check_version_compatibility(storage_path):
        console.print("⚠ Cannot start with incompatible store version", style="red")
        return

    engine = CoreEngine()
    try:
        engine.init_store(storage_path)
        console.print(f"✓ Repository initialized at: {storage_path}", style="green")
    except Exception as e:
        if "already exists" in str(e):
            console.print(f"✓ Repository exists at: {storage_path}", style="green")
        else:
            console.print(f"✗ Init failed: {e}", style="red")
            return

    # Step 2: Ensure spaCy model is available
    ensure_spacy_model()

    # Step 3: Check port availability
    console.print("🔍 Checking port availability...", style="yellow")
    if not check_port_available(port):
        console.print(f"✗ Port {port} is already in use.", style="red")
        console.print(f"  Options:", style="yellow")
        console.print(f"  1. Stop whatever is using port {port}", style="yellow")
        console.print(f"  2. Use a different port: memora start --port <port>", style="yellow")
        console.print(f"  3. Check what's using it: netstat -ano | findstr :{port}", style="yellow")
        return

    # Also check if Ollama is running on default port 11434
    if not check_port_available(11434):
        console.print(f"✓ Ollama detected on port 11434", style="green")
    else:
        console.print(f"⚠ Ollama not detected on port 11434.", style="yellow")
        console.print(f"  Is Ollama running? Try: ollama serve", style="yellow")
        console.print(f"  Continuing anyway...", style="dim")

    # Step 3: Configure OLLAMA_HOST if requested
    if auto_setup:
        console.print("🔧 Configuring OLLAMA_HOST...", style="yellow")
        try:
            subprocess.run(
                ["setx", "OLLAMA_HOST", f"http://localhost:{port}"], check=True, capture_output=True
            )
            console.print(
                f"✓ OLLAMA_HOST set to http://localhost:{port} system-wide", style="green"
            )
        except Exception:
            try:
                os.environ["OLLAMA_HOST"] = f"http://localhost:{port}"
                console.print(f"✓ OLLAMA_HOST set for current session", style="yellow")
            except Exception as e:
                console.print(f"⚠ Could not set OLLAMA_HOST: {e}", style="yellow")

    # Step 4: Start the proxy
    console.print(f"🌐 Starting proxy on port {port}...", style="yellow")
    console.print(
        "✓ Memora is running! Chat with Ollama normally - memories will be captured automatically.",
        style="bold green",
    )
    console.print("Press Ctrl+C to stop\n", style="dim")

    try:
        from memora.ai.ollama_proxy import start_proxy

        start_proxy(proxy_port=port, memory_path=memory_path)
    except KeyboardInterrupt:
        console.print("\n👋 Memora stopped", style="yellow")
    except Exception as e:
        console.print(f"✗ Proxy failed: {e}", style="red")


@app.command()
def init(
    path: str = typer.Option("./memora_data", help="Path to initialize"),
    reset: bool = typer.Option(False, help="Reset existing store (DELETES ALL MEMORIES)"),
):
    """Initialize a new Memora repository."""
    from memora.core.engine import CoreEngine
    import shutil

    storage_path = Path(path)
    memora_dir = storage_path / ".memora"

    # Check if .memora directory already exists
    if memora_dir.exists() and not reset:
        # Count existing objects to inform user
        objects_dir = memora_dir / "objects"
        object_count = 0
        if objects_dir.exists():
            object_count = sum(1 for _ in objects_dir.rglob("*") if _.is_file())

        console.print(f"✗ Memora already initialized in this directory.", style="red")
        console.print(f"  Found: {object_count} stored objects", style="yellow")
        console.print(f"  Options:", style="yellow")
        console.print(f"  - To continue using existing store: run 'memora start'", style="yellow")
        console.print(
            f"  - To start fresh (DELETES ALL MEMORIES): 'memora init --reset'", style="yellow"
        )
        return

    # Handle reset case
    if reset and memora_dir.exists():
        console.print("⚠ WARNING: This will permanently delete all memories.", style="red")
        console.print("  All objects, sessions, graph, and indices will be removed.", style="red")
        console.print(
            "\n💡 TIP: Before destructive operations, backup with: memora backup", style="yellow"
        )
        confirm = typer.prompt("\n  Type 'DELETE' to confirm")
        if confirm != "DELETE":
            console.print("Cancelled.", style="yellow")
            return
        console.print("🗑️  Deleting existing store...", style="yellow")
        shutil.rmtree(memora_dir)

    # Fresh init - proceed normally
    storage_path.mkdir(parents=True, exist_ok=True)
    engine = CoreEngine()
    try:
        engine.init_store(storage_path)
        console.print(f"✓ Memora repository initialized at: {storage_path}", style="green")
        console.print("Run 'memora start' to begin.", style="dim")
    except Exception as e:
        console.print(f"✗ Init failed: {e}", style="red")


@app.command()
def search(
    query: str,
    memory_path: str = typer.Option("./memora_data", help="Path to memory"),
    time: str = typer.Option(
        "", help="Time filter (e.g., 'last week', 'yesterday', 'since monday')"
    ),
):
    """Search stored memories with optional time filtering."""
    from memora.core.engine import CoreEngine
    from memora.core.time_parser import parse_time_query

    engine = CoreEngine()
    try:
        engine.open_store(Path(memory_path))
    except Exception:
        console.print("No Memora store found. Run 'memora init' first.", style="red")
        return

    # Parse time query if provided
    date_range = None
    if time:
        date_range = parse_time_query(time)
        if date_range:
            start, end = date_range
            console.print(
                f"🕒 Time filter: {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}",
                style="dim",
            )
        else:
            console.print(f"⚠ Could not parse time expression: '{time}'", style="yellow")
            return

    # Search with time filter
    results = engine.search_memories(query, date_range=date_range)
    if not results:
        time_msg = f" (in time range '{time}')" if time else ""
        console.print(f"No memories found for '{query}'{time_msg}.", style="yellow")
        return

    # Display results
    time_suffix = f" (time: {time})" if time else ""
    table = Table(title=f"Search results for '{query}'{time_suffix}")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Date", style="magenta")
    table.add_column("Content", style="white")
    table.add_column("Confidence", style="yellow")

    for m in results:
        # Format date nicely
        try:
            from dateutil import parser as date_parser

            created = date_parser.parse(m.created_at)
            date_str = created.strftime("%m/%d %H:%M")
        except:
            date_str = m.created_at[:16]  # Fallback

        table.add_row(
            m.id[:12],
            m.memory_type.value,
            date_str,
            m.content[:60] + "..." if len(m.content) > 60 else m.content,
            f"{m.confidence:.2f}",
        )
    console.print(table)


@app.command()
def when(
    time_query: str,
    memory_path: str = typer.Option("./memora_data", help="Path to memory"),
    limit: int = typer.Option(20, help="Maximum results to show"),
):
    """Search memories by time using natural language.

    Examples:
        memora when "last week"
        memora when "yesterday"
        memora when "2 days ago"
        memora when "since monday"
        memora when "between 2024-01-01 and 2024-01-31"
    """
    from memora.core.engine import CoreEngine
    from memora.core.time_parser import parse_time_query

    engine = CoreEngine()
    try:
        engine.open_store(Path(memory_path))
    except Exception:
        console.print("No Memora store found. Run 'memora init' first.", style="red")
        return

    # Parse time query
    date_range = parse_time_query(time_query)
    if not date_range:
        console.print(f"⚠ Could not parse time expression: '{time_query}'", style="yellow")
        console.print(
            "Try expressions like: 'last week', 'yesterday', '2 days ago', 'since monday'",
            style="dim",
        )
        return

    start, end = date_range
    console.print(
        f"🕒 Searching memories from {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}",
        style="blue",
    )

    # Search in time range
    results = engine.search_memories_by_time(start, end, limit=limit)
    if not results:
        console.print(f"No memories found in time range '{time_query}'.", style="yellow")
        return

    # Display results
    table = Table(title=f"Memories from '{time_query}' ({len(results)} found)")
    table.add_column("Date/Time", style="magenta")
    table.add_column("Type", style="green")
    table.add_column("Content", style="white")
    table.add_column("Source", style="cyan")

    for m in results:
        try:
            from dateutil import parser as date_parser

            created = date_parser.parse(m.created_at)
            date_str = created.strftime("%m/%d %H:%M")
        except:
            date_str = m.created_at[:16]

        source = getattr(m, "source", MemorySource.OLLAMA_CHAT).value
        content = m.content[:80] + "..." if len(m.content) > 80 else m.content

        table.add_row(date_str, m.memory_type.value, content, source)

    console.print(table)

    # Show summary stats
    console.print(f"\n📊 Found {len(results)} memories in '{time_query}'", style="dim")


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
def rollback(
    commit: str,
    memory_path: str = typer.Option("./memora_data", help="Path to memory"),
    force: bool = typer.Option(False, help="Skip safety confirmation"),
    create_backup_branch: bool = typer.Option(True, help="Create backup branch before rollback"),
):
    """Roll back to a previous commit with safety guards.

    WARNING: This will make all memories committed after the target commit unreachable.
    Use --create-backup-branch to preserve current state.
    """
    from memora.core.engine import CoreEngine
    from memora.core.refs import get_current_branch, get_branch_commit, update_branch

    engine = CoreEngine()
    try:
        engine.open_store(Path(memory_path))
    except Exception:
        console.print("No Memora store found.", style="red")
        return

    # Validate commit exists
    try:
        store_path, store = engine._ensure()
        target_commit = store.read_commit(commit)
        console.print(f"Target commit: {commit[:12]}... ({target_commit.message})", style="cyan")
        console.print(f"Committed at: {target_commit.committed_at}", style="dim")
    except Exception as e:
        console.print(f"Invalid commit hash: {e}", style="red")
        return

    # Get current state
    current_branch = get_current_branch(Path(memory_path))
    current_commit = get_branch_commit(Path(memory_path), current_branch)

    if current_commit == commit:
        console.print("Already at target commit.", style="green")
        return

    # Safety warning
    if not force:
        console.print("⚠️  ROLLBACK WARNING", style="bold red")
        console.print(
            f"This will move branch '{current_branch}' from {current_commit[:12]}... to {commit[:12]}...",
            style="yellow",
        )
        console.print(
            "All memories committed after the target will become orphaned.", style="yellow"
        )

        if create_backup_branch:
            backup_name = f"{current_branch}-backup-{current_commit[:8]}"
            console.print(f"A backup branch '{backup_name}' will be created first.", style="green")
        else:
            console.print(
                "No backup will be created. This operation cannot be undone!", style="red"
            )

        confirm = console.input("\nContinue? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            console.print("Rollback cancelled.", style="yellow")
            return

    # Create backup branch if requested
    if create_backup_branch:
        backup_name = f"{current_branch}-backup-{current_commit[:8]}"
        try:
            update_branch(Path(memory_path), backup_name, current_commit)
            console.print(f"✓ Backup branch created: {backup_name}", style="green")
        except Exception as e:
            console.print(f"Failed to create backup: {e}", style="red")
            return

    # Perform rollback
    try:
        update_branch(Path(memory_path), current_branch, commit)
        console.print(f"✓ Rolled back to {commit[:12]}...", style="green")

        if create_backup_branch:
            console.print(f"✓ Previous state preserved in branch: {backup_name}", style="green")
            console.print(f"To restore: memora branch switch {backup_name}", style="dim")

    except Exception as e:
        console.print(f"Rollback failed: {e}", style="red")


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
def gc(
    memory_path: str = typer.Option("./memora_data", help="Path to memory"),
    aggressive: bool = typer.Option(False, help="Use aggressive cleanup settings"),
    dry_run: bool = typer.Option(False, help="Show what would be cleaned without deleting"),
):
    """Run garbage collection to clean up orphaned objects and old data."""
    from memora.core.garbage_collector import run_maintenance

    try:
        results = run_maintenance(Path(memory_path), aggressive=aggressive, dry_run=dry_run)

        if dry_run:
            console.print("🔍 DRY RUN - No files were deleted", style="bold yellow")

        # Show before/after stats
        before = results["before"]
        console.print(f"📊 Storage Stats:", style="bold blue")
        console.print(f"  Objects: {before['total_objects']:,}")
        console.print(f"  Size: {before['total_size_bytes'] / (1024*1024):.1f} MB")
        console.print(f"  Active sessions: {before['active_sessions']}")
        console.print(f"  Closed sessions: {before['closed_sessions']}")
        console.print(f"  Open conflicts: {before['open_conflicts']}")
        console.print(f"  Resolved conflicts: {before['resolved_conflicts']}")

        if not dry_run and "cleaned" in results:
            cleaned = results["cleaned"]
            console.print(f"\n🧹 Cleanup Results:", style="bold green")
            console.print(f"  Orphaned objects removed: {cleaned['orphaned_objects']}")
            console.print(f"  Old sessions removed: {cleaned['old_sessions']}")
            console.print(f"  Resolved conflicts removed: {cleaned['resolved_conflicts']}")
            console.print(f"  Space freed: {cleaned['bytes_freed'] / (1024*1024):.1f} MB")

            if results["aggressive"]:
                console.print("  Used aggressive cleanup settings", style="dim")

        console.print(f"\n✨ Maintenance complete!", style="bold green")

    except Exception as e:
        console.print(f"Maintenance failed: {e}", style="red")


@app.command()
def backup(
    destination: Optional[str] = typer.Option(None, help="Backup destination directory"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory store"),
):
    """Create a backup of the Memora store."""
    import tarfile
    from datetime import datetime

    store_path = Path(memory_path)
    memora_dir = store_path / ".memora"

    if not memora_dir.exists():
        console.print("✗ No Memora store found at this location", style="red")
        return

    try:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        if destination is None:
            backup_file = Path.cwd() / f"memora-backup-{timestamp}.tar.gz"
        else:
            dest_dir = Path(destination)
            dest_dir.mkdir(parents=True, exist_ok=True)
            backup_file = dest_dir / f"memora-backup-{timestamp}.tar.gz"

        console.print(f"📦 Creating backup...", style="yellow")

        with tarfile.open(backup_file, "w:gz") as tar:
            tar.add(memora_dir, arcname=".memora")

        size_mb = backup_file.stat().st_size / (1024 * 1024)
        console.print(f"✓ Backup created: {backup_file}", style="green")
        console.print(f"  Size: {size_mb:.1f} MB", style="dim")
        console.print(f"  To restore: memora restore {backup_file}", style="dim")

    except Exception as e:
        console.print(f"✗ Backup failed: {e}", style="red")
        import traceback

        console.print(traceback.format_exc(), style="red")


@app.command()
def restore(
    backup_file: str = typer.Argument(..., help="Path to backup file"),
    memory_path: str = typer.Option("./memora_data", help="Path to restore to"),
    force: bool = typer.Option(False, help="Overwrite existing store"),
):
    """Restore a Memora store from backup."""
    import tarfile
    import shutil

    backup_path = Path(backup_file)
    store_path = Path(memory_path)
    memora_dir = store_path / ".memora"

    if not backup_path.exists():
        console.print(f"✗ Backup file not found: {backup_file}", style="red")
        return

    if memora_dir.exists() and not force:
        console.print("✗ Memora store already exists at this location", style="red")
        console.print("  Options:", style="yellow")
        console.print("  1. Use a different restore path: --memory-path <path>", style="yellow")
        console.print("  2. Overwrite existing store: --force", style="yellow")
        console.print("  3. Create a backup first: memora backup", style="yellow")
        return

    try:
        # Backup existing store if it exists and force is used
        if memora_dir.exists() and force:
            console.print("⚠ Backing up existing store before overwrite...", style="yellow")
            temp_backup = store_path / f".memora.backup.{int(datetime.now().timestamp())}"
            shutil.move(str(memora_dir), str(temp_backup))
            console.print(f"  Existing store moved to: {temp_backup}", style="dim")

        console.print(f"📦 Restoring from backup...", style="yellow")

        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(path=store_path)

        console.print(f"✓ Restore complete: {memora_dir}", style="green")
        console.print("  You can now run: memora start", style="dim")

    except Exception as e:
        console.print(f"✗ Restore failed: {e}", style="red")
        import traceback

        console.print(traceback.format_exc(), style="red")


@app.command()
def setup():
    """Interactive setup wizard."""
    console.print("Memora Setup", style="bold blue")
    console.print("1. Make sure Ollama is installed and running")
    console.print("2. Run: memora init")
    console.print("3. Run: memora proxy start")
    console.print("4. Configure your Ollama client to use http://localhost:11435")
    console.print("5. Start chatting!", style="green")


# ==================== Ollama Target Management ====================

ollama_app = typer.Typer(name="ollama", help="Manage multiple Ollama instances")
app.add_typer(ollama_app, name="ollama")


@ollama_app.command("list")
def list_ollama_targets(
    memory_path: str = typer.Option("./memora_data", help="Path to memory store"),
):
    """List configured Ollama targets."""
    import json
    from pathlib import Path

    config_file = Path(memory_path) / ".memora" / "config"
    if not config_file.exists():
        console.print("No Memora store found. Run 'memora init' first.", style="red")
        return

    try:
        with open(config_file) as f:
            config = json.load(f)

        targets = config.get("ollama_targets", {})
        if not targets:
            console.print("No Ollama targets configured.", style="yellow")
            return

        table = Table(title="Configured Ollama Targets")
        table.add_column("Name", style="cyan")
        table.add_column("Host", style="blue")
        table.add_column("Port", style="green")
        table.add_column("Priority", style="yellow")
        table.add_column("Status", style="white")

        for name, target in targets.items():
            status = "✓ Enabled" if target.get("enabled", True) else "✗ Disabled"
            table.add_row(
                target.get("name", name),
                target.get("host", "localhost"),
                str(target.get("port", 11434)),
                str(target.get("priority", 1)),
                status,
            )
        console.print(table)

    except Exception as e:
        console.print(f"Error reading config: {e}", style="red")


@ollama_app.command("add")
def add_ollama_target(
    name: str = typer.Argument(..., help="Target name (e.g., 'secondary')"),
    host: str = typer.Option("localhost", help="Ollama host"),
    port: int = typer.Option(11434, help="Ollama port"),
    priority: int = typer.Option(2, help="Priority (1=highest)"),
    friendly_name: str = typer.Option("", help="Friendly display name"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory store"),
):
    """Add a new Ollama target."""
    import json
    from pathlib import Path

    config_file = Path(memory_path) / ".memora" / "config"
    if not config_file.exists():
        console.print("No Memora store found. Run 'memora init' first.", style="red")
        return

    # Test connectivity
    if not check_port_available(port):
        console.print(f"✓ Ollama detected at {host}:{port}", style="green")
    else:
        console.print(f"⚠ No Ollama detected at {host}:{port}", style="yellow")
        if not typer.confirm("Continue anyway?"):
            return

    try:
        with open(config_file) as f:
            config = json.load(f)

        if "ollama_targets" not in config:
            config["ollama_targets"] = {}

        config["ollama_targets"][name] = {
            "host": host,
            "port": port,
            "priority": priority,
            "enabled": True,
            "name": friendly_name or f"Ollama on {host}:{port}",
        }

        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        console.print(f"✓ Added Ollama target '{name}' at {host}:{port}", style="green")

    except Exception as e:
        console.print(f"Error updating config: {e}", style="red")


@ollama_app.command("remove")
def remove_ollama_target(
    name: str = typer.Argument(..., help="Target name to remove"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory store"),
):
    """Remove an Ollama target."""
    import json
    from pathlib import Path

    config_file = Path(memory_path) / ".memora" / "config"
    if not config_file.exists():
        console.print("No Memora store found. Run 'memora init' first.", style="red")
        return

    try:
        with open(config_file) as f:
            config = json.load(f)

        targets = config.get("ollama_targets", {})
        if name not in targets:
            console.print(f"Target '{name}' not found.", style="red")
            return

        if name == "primary":
            console.print("Cannot remove primary target. Disable it instead.", style="red")
            return

        del targets[name]

        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        console.print(f"✓ Removed Ollama target '{name}'", style="green")

    except Exception as e:
        console.print(f"Error updating config: {e}", style="red")


@ollama_app.command("enable")
def enable_ollama_target(
    name: str = typer.Argument(..., help="Target name to enable"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory store"),
):
    """Enable an Ollama target."""
    _toggle_ollama_target(name, True, memory_path)


@ollama_app.command("disable")
def disable_ollama_target(
    name: str = typer.Argument(..., help="Target name to disable"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory store"),
):
    """Disable an Ollama target."""
    _toggle_ollama_target(name, False, memory_path)


def _toggle_ollama_target(name: str, enabled: bool, memory_path: str):
    """Toggle Ollama target enabled/disabled state."""
    import json
    from pathlib import Path

    config_file = Path(memory_path) / ".memora" / "config"
    if not config_file.exists():
        console.print("No Memora store found. Run 'memora init' first.", style="red")
        return

    try:
        with open(config_file) as f:
            config = json.load(f)

        targets = config.get("ollama_targets", {})
        if name not in targets:
            console.print(f"Target '{name}' not found.", style="red")
            return

        targets[name]["enabled"] = enabled

        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        status = "enabled" if enabled else "disabled"
        console.print(f"✓ {status.title()} Ollama target '{name}'", style="green")

    except Exception as e:
        console.print(f"Error updating config: {e}", style="red")


# ==================== Server Commands ====================

server_app = typer.Typer(name="server", help="Standalone server commands")
app.add_typer(server_app, name="server")


@server_app.command("start")
def start_server(
    port: int = typer.Option(11436, help="Server port (separate from proxy)"),
    memory_path: str = typer.Option("./memora_data", help="Path to memory store"),
):
    """Start standalone Memora server (dashboard only, no proxy)."""
    from pathlib import Path

    console.print("🌐 Starting Memora standalone server...", style="bold blue")

    # Check port availability
    if not check_port_available(port):
        console.print(f"✗ Port {port} is already in use.", style="red")
        return

    # Check if store exists
    store_path = Path(memory_path) / ".memora"
    if not store_path.exists():
        console.print("No Memora store found. Run 'memora init' first.", style="red")
        return

    console.print(f"✓ Dashboard available at: http://localhost:{port}/dashboard", style="green")
    console.print("✓ API available at: http://localhost:{port}/api", style="green")
    console.print("Press Ctrl+C to stop", style="dim")

    try:
        # Import and start FastAPI server without proxy
        from memora.ai.server import start_server as start_fastapi_server

        start_fastapi_server(port=port, memory_path=memory_path, proxy_mode=False)
    except KeyboardInterrupt:
        console.print("\n👋 Server stopped", style="yellow")
    except Exception as e:
        console.print(f"✗ Server failed: {e}", style="red")


if __name__ == "__main__":
    app()
