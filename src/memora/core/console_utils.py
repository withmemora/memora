"""
Cross-platform console utilities for safe output on all terminals.
Handles Windows Unicode issues while maintaining visual appeal on other platforms.
"""

import sys
from rich.console import Console


def create_safe_console() -> Console:
    """Create a console that works safely across all platforms."""
    # On Windows, use legacy mode to avoid Unicode issues
    if sys.platform == "win32":
        return Console(legacy_windows=True, force_terminal=True)
    return Console()


def get_safe_icon(emoji: str, fallback: str) -> str:
    """Get platform-appropriate icon, falling back to ASCII on Windows."""
    if sys.platform == "win32":
        return fallback
    return emoji


def safe_print(console: Console, message: str, style: str = None, **kwargs) -> None:
    """Print message with Windows-safe Unicode handling."""
    try:
        console.print(message, style=style, **kwargs)
    except UnicodeEncodeError:
        # Fallback: strip emojis and use plain text
        safe_message = message.encode("ascii", "ignore").decode("ascii")
        console.print(safe_message, style=style, **kwargs)


# Platform-safe icon mappings
ICONS = {
    "rocket": get_safe_icon("🚀", ">>"),
    "check": get_safe_icon("✓", "[+]"),
    "warning": get_safe_icon("⚠", "[!]"),
    "error": get_safe_icon("❌", "[x]"),
    "info": get_safe_icon("ℹ", "[i]"),
    "arrow": get_safe_icon("→", "->"),
    "bullet": get_safe_icon("•", "*"),
    "gear": get_safe_icon("⚙", "[*]"),
    "folder": get_safe_icon("📁", "[DIR]"),
    "file": get_safe_icon("📄", "[FILE]"),
    "link": get_safe_icon("🔗", "[LINK]"),
    "clock": get_safe_icon("🕒", "[TIME]"),
    "memory": get_safe_icon("🧠", "[MEM]"),
    "search": get_safe_icon("🔍", "[SEARCH]"),
    "graph": get_safe_icon("🕸", "[GRAPH]"),
    "export": get_safe_icon("📤", "[EXPORT]"),
    "import": get_safe_icon("📥", "[IMPORT]"),
    "backup": get_safe_icon("💾", "[BACKUP]"),
    "restore": get_safe_icon("🔄", "[RESTORE]"),
    "delete": get_safe_icon("🗑", "[DELETE]"),
    "branch": get_safe_icon("🌿", "[BRANCH]"),
    "commit": get_safe_icon("💾", "[COMMIT]"),
    "rollback": get_safe_icon("⏪", "[ROLLBACK]"),
}
