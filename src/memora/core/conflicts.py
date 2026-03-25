"""Conflict detection and resolution for Memora.

This module detects when facts contradict each other, classifies conflicts,
and provides auto-resolution policies. Conflicts are stored as structured
objects with full resolution lifecycle tracking.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from memora.shared.models import Fact, Conflict, ConflictType, ConflictStatus


def detect_conflicts(new_fact: Fact, existing_facts: list[Fact]) -> list[Conflict]:
    """Detect conflicts between a new fact and existing facts.

    A conflict exists when:
    - Same entity (case-insensitive)
    - Same attribute (case-insensitive)
    - Different value (case-sensitive)

    Args:
        new_fact: The new fact being added
        existing_facts: List of existing facts to check against

    Returns:
        List of Conflict objects (may be empty)
    """
    conflicts = []

    for existing_fact in existing_facts:
        # Check if facts conflict: same entity+attribute, different value
        if (
            new_fact.entity.lower() == existing_fact.entity.lower()
            and new_fact.attribute.lower() == existing_fact.attribute.lower()
            and new_fact.value != existing_fact.value
        ):
            # Create conflict
            conflict_type = classify_conflict(new_fact, existing_fact)
            conflict_id = _generate_conflict_id(new_fact, existing_fact)

            conflict = Conflict(
                conflict_id=conflict_id,
                fact_a_hash=existing_fact.compute_hash(),
                fact_b_hash=new_fact.compute_hash(),
                conflict_type=conflict_type,
                conflict_status=ConflictStatus.UNRESOLVED,
                detected_at=datetime.utcnow(),
                resolution_fact_hash=None,
                resolution_reason=None,
                resolved_at=None,
            )

            conflicts.append(conflict)

    return conflicts


def classify_conflict(fact_a: Fact, fact_b: Fact) -> ConflictType:
    """Classify conflict type based on timing and sources.

    Classification rules (from CLAUDE.md):
    - Same entity+attr, different value, within 24h → DIRECT_CONTRADICTION
    - Same entity+attr, different value, 7+ days apart → TEMPORAL_SUPERSESSION
    - Same entity+attr, different value, different sources, same time → SOURCE_CONFLICT
    - Cannot classify → UNCERTAIN

    Args:
        fact_a: First conflicting fact
        fact_b: Second conflicting fact

    Returns:
        ConflictType classification
    """
    time_diff = abs((fact_b.observed_at - fact_a.observed_at).total_seconds())
    time_diff_days = time_diff / (24 * 3600)  # Convert to days

    # Rule 1: 7+ days apart = TEMPORAL_SUPERSESSION
    if time_diff_days >= 7.0:
        return ConflictType.TEMPORAL_SUPERSESSION

    # Rule 2: Different sources, same timeframe (within 24h) = SOURCE_CONFLICT
    if fact_a.source != fact_b.source and time_diff_days <= 1.0:
        return ConflictType.SOURCE_CONFLICT

    # Rule 3: Within 24 hours, same source = DIRECT_CONTRADICTION
    if time_diff_days <= 1.0:
        return ConflictType.DIRECT_CONTRADICTION

    # Rule 4: Cannot classify = UNCERTAIN
    return ConflictType.UNCERTAIN


def auto_resolve_conflict(
    conflict: Conflict, fact_a: Fact, fact_b: Fact, source_priority_list: Optional[list[str]] = None
) -> Optional[Conflict]:
    """Attempt to auto-resolve conflict using resolution policies.

    Resolution chain (first match wins):
    1. RecencyPolicy: If time gap ≥ 7 days → newer fact wins
    2. ConfidencePolicy: If confidence diff ≥ 0.3 → higher wins
    3. SourcePriorityPolicy: Check configured source priority list
    4. ManualReviewPolicy: Always returns None → needs human review

    Args:
        conflict: The conflict to resolve
        fact_a: First conflicting fact
        fact_b: Second conflicting fact
        source_priority_list: Optional list of sources in priority order

    Returns:
        Updated Conflict object if resolved, None if needs manual review
    """
    # Policy 1: RecencyPolicy - newer fact wins if gap ≥ 7 days
    recency_policy = RecencyPolicy()
    resolved_conflict = recency_policy.resolve(conflict, fact_a, fact_b)
    if resolved_conflict is not None:
        return resolved_conflict

    # Policy 2: ConfidencePolicy - higher confidence wins if diff ≥ 0.3
    confidence_policy = ConfidencePolicy()
    resolved_conflict = confidence_policy.resolve(conflict, fact_a, fact_b)
    if resolved_conflict is not None:
        return resolved_conflict

    # Policy 3: SourcePriorityPolicy - configured source priority
    if source_priority_list:
        source_policy = SourcePriorityPolicy(source_priority_list)
        resolved_conflict = source_policy.resolve(conflict, fact_a, fact_b)
        if resolved_conflict is not None:
            return resolved_conflict

    # Policy 4: ManualReviewPolicy - always returns None
    manual_policy = ManualReviewPolicy()
    return manual_policy.resolve(conflict, fact_a, fact_b)


class RecencyPolicy:
    """Newer fact wins if time gap ≥ 7 days."""

    def resolve(self, conflict: Conflict, fact_a: Fact, fact_b: Fact) -> Optional[Conflict]:
        """Resolve conflict based on recency if time gap ≥ 7 days."""
        time_diff = abs((fact_b.observed_at - fact_a.observed_at).total_seconds())
        time_diff_days = time_diff / (24 * 3600)

        if time_diff_days >= 7.0:
            # Choose newer fact
            if fact_b.observed_at > fact_a.observed_at:
                winner_hash = fact_b.compute_hash()
                reason = f"RecencyPolicy: newer fact from {fact_b.observed_at.isoformat()}"
            else:
                winner_hash = fact_a.compute_hash()
                reason = f"RecencyPolicy: newer fact from {fact_a.observed_at.isoformat()}"

            # Return resolved conflict
            conflict.conflict_status = ConflictStatus.AUTO_RESOLVED
            conflict.resolution_fact_hash = winner_hash
            conflict.resolution_reason = reason
            conflict.resolved_at = datetime.utcnow()
            return conflict

        return None


class ConfidencePolicy:
    """Higher confidence wins if difference ≥ 0.3."""

    def resolve(self, conflict: Conflict, fact_a: Fact, fact_b: Fact) -> Optional[Conflict]:
        """Resolve conflict based on confidence if difference ≥ 0.3."""
        confidence_diff = abs(fact_b.confidence - fact_a.confidence)

        if confidence_diff >= 0.3:
            # Choose higher confidence fact
            if fact_b.confidence > fact_a.confidence:
                winner_hash = fact_b.compute_hash()
                reason = f"ConfidencePolicy: higher confidence {fact_b.confidence:.2f} vs {fact_a.confidence:.2f}"
            else:
                winner_hash = fact_a.compute_hash()
                reason = f"ConfidencePolicy: higher confidence {fact_a.confidence:.2f} vs {fact_b.confidence:.2f}"

            # Return resolved conflict
            conflict.conflict_status = ConflictStatus.AUTO_RESOLVED
            conflict.resolution_fact_hash = winner_hash
            conflict.resolution_reason = reason
            conflict.resolved_at = datetime.utcnow()
            return conflict

        return None


class SourcePriorityPolicy:
    """Configured source priority list wins."""

    def __init__(self, priority_list: list[str]):
        """Initialize with source priority list (higher index = higher priority)."""
        self.priority_list = priority_list

    def resolve(self, conflict: Conflict, fact_a: Fact, fact_b: Fact) -> Optional[Conflict]:
        """Resolve conflict based on source priority."""
        try:
            priority_a = self.priority_list.index(fact_a.source)
        except ValueError:
            priority_a = -1  # Not in list = lowest priority

        try:
            priority_b = self.priority_list.index(fact_b.source)
        except ValueError:
            priority_b = -1  # Not in list = lowest priority

        # If both sources not in priority list, cannot resolve
        if priority_a == -1 and priority_b == -1:
            return None

        # Choose higher priority source (higher index = higher priority)
        if priority_b > priority_a:
            winner_hash = fact_b.compute_hash()
            reason = f"SourcePriorityPolicy: source '{fact_b.source}' priority {priority_b}"
        elif priority_a > priority_b:
            winner_hash = fact_a.compute_hash()
            reason = f"SourcePriorityPolicy: source '{fact_a.source}' priority {priority_a}"
        else:
            # Equal priority, cannot resolve
            return None

        # Return resolved conflict
        conflict.conflict_status = ConflictStatus.AUTO_RESOLVED
        conflict.resolution_fact_hash = winner_hash
        conflict.resolution_reason = reason
        conflict.resolved_at = datetime.utcnow()
        return conflict


class ManualReviewPolicy:
    """Always returns None - human must decide."""

    def resolve(self, conflict: Conflict, fact_a: Fact, fact_b: Fact) -> Optional[Conflict]:
        """Always returns None to force manual review."""
        return None


def store_conflict(conflict: Conflict, store_path: Path) -> None:
    """Store conflict to appropriate directory based on status.

    Args:
        conflict: Conflict object to store
        store_path: Path to .memora directory
    """
    conflicts_dir = store_path / "conflicts"

    if conflict.conflict_status == ConflictStatus.UNRESOLVED:
        target_dir = conflicts_dir / "open"
    else:
        target_dir = conflicts_dir / "resolved"

    # Create directories if they don't exist
    target_dir.mkdir(parents=True, exist_ok=True)

    # Write conflict as JSON
    conflict_file = target_dir / f"{conflict.conflict_id}.json"
    with open(conflict_file, "w", encoding="utf-8") as f:
        json.dump(conflict.to_dict(), f, separators=(",", ":"), sort_keys=True)


def load_conflict(conflict_id: str, store_path: Path) -> Optional[Conflict]:
    """Load conflict by ID from either open or resolved directory.

    Args:
        conflict_id: SHA-256 conflict ID
        store_path: Path to .memora directory

    Returns:
        Conflict object if found, None otherwise
    """
    conflicts_dir = store_path / "conflicts"

    # Check open conflicts first
    open_file = conflicts_dir / "open" / f"{conflict_id}.json"
    if open_file.exists():
        with open(open_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Conflict.from_dict(data)

    # Check resolved conflicts
    resolved_file = conflicts_dir / "resolved" / f"{conflict_id}.json"
    if resolved_file.exists():
        with open(resolved_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Conflict.from_dict(data)

    return None


def list_open_conflicts(store_path: Path) -> list[str]:
    """List all unresolved conflict IDs.

    Args:
        store_path: Path to .memora directory

    Returns:
        List of conflict IDs (without .json extension)
    """
    open_dir = store_path / "conflicts" / "open"
    if not open_dir.exists():
        return []

    conflict_ids = []
    for file_path in open_dir.glob("*.json"):
        conflict_ids.append(file_path.stem)  # Remove .json extension

    return sorted(conflict_ids)


def move_conflict_to_resolved(conflict: Conflict, store_path: Path) -> None:
    """Move conflict from open to resolved directory.

    Args:
        conflict: Resolved conflict object
        store_path: Path to .memora directory
    """
    conflicts_dir = store_path / "conflicts"
    open_file = conflicts_dir / "open" / f"{conflict.conflict_id}.json"
    resolved_file = conflicts_dir / "resolved" / f"{conflict.conflict_id}.json"

    # Ensure resolved directory exists
    resolved_file.parent.mkdir(parents=True, exist_ok=True)

    # Write to resolved directory
    with open(resolved_file, "w", encoding="utf-8") as f:
        json.dump(conflict.to_dict(), f, separators=(",", ":"), sort_keys=True)

    # Remove from open directory
    if open_file.exists():
        open_file.unlink()


def _generate_conflict_id(fact_a: Fact, fact_b: Fact) -> str:
    """Generate deterministic conflict ID from two facts.

    Conflict ID = SHA-256 of (fact_a_hash + fact_b_hash + detected_at)

    Args:
        fact_a: First fact
        fact_b: Second fact

    Returns:
        64-character hex SHA-256 hash
    """
    detected_at = datetime.utcnow().isoformat()

    # Sort hashes to ensure deterministic ordering
    hash_a = fact_a.compute_hash()
    hash_b = fact_b.compute_hash()
    hashes = sorted([hash_a, hash_b])

    # Combine hashes with timestamp
    combined = hashes[0] + hashes[1] + detected_at

    # SHA-256 hash
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


class ConflictManager:
    """Enhanced conflict management with better UX and filtering."""

    def __init__(self, store_path: Path):
        self.store_path = store_path
        self.conflicts_dir = store_path / ".memora" / "conflicts"

    def list_conflicts_with_context(
        self,
        since: Optional[datetime] = None,
        search_term: Optional[str] = None,
        entity_filter: Optional[str] = None,
        status_filter: ConflictStatus = ConflictStatus.UNRESOLVED,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """List conflicts with rich context and filtering options."""
        from ..core.store import ObjectStore

        object_store = ObjectStore(self.store_path)
        conflicts_with_context = []

        # Determine which conflicts to check
        if status_filter == ConflictStatus.UNRESOLVED:
            conflict_dir = self.conflicts_dir / "open"
        else:
            conflict_dir = self.conflicts_dir / "resolved"

        if not conflict_dir.exists():
            return []

        # Load all conflict files
        for conflict_file in conflict_dir.glob("*.json"):
            try:
                conflict_data = json.loads(conflict_file.read_text())
                conflict = Conflict(**conflict_data)

                # Apply date filter
                if since and conflict.detected_at < since:
                    continue

                # Load facts for context
                try:
                    fact_a = object_store.read_fact(conflict.fact_a_hash)
                    fact_b = object_store.read_fact(conflict.fact_b_hash)
                except Exception:
                    continue  # Skip if facts can't be loaded

                # Apply entity filter
                if entity_filter and not (
                    entity_filter.lower() in fact_a.entity.lower()
                    or entity_filter.lower() in fact_b.entity.lower()
                ):
                    continue

                # Apply search filter
                if search_term and not (
                    search_term.lower() in fact_a.value.lower()
                    or search_term.lower() in fact_b.value.lower()
                    or search_term.lower() in fact_a.attribute.lower()
                    or search_term.lower() in fact_b.attribute.lower()
                ):
                    continue

                # Create rich context
                conflict_context = {
                    "conflict_id": conflict.conflict_id,
                    "short_id": conflict.conflict_id[:8],  # First 8 chars for display
                    "entity": fact_a.entity,
                    "attribute": fact_a.attribute,
                    "conflict_type": conflict.conflict_type.value,
                    "detected_at": conflict.detected_at,
                    "time_ago": self._time_ago(conflict.detected_at),
                    "fact_a": {
                        "value": fact_a.value,
                        "content": fact_a.content[:100] + "..."
                        if len(fact_a.content) > 100
                        else fact_a.content,
                        "observed_at": fact_a.observed_at,
                        "confidence": fact_a.confidence,
                        "source": fact_a.source,
                    },
                    "fact_b": {
                        "value": fact_b.value,
                        "content": fact_b.content[:100] + "..."
                        if len(fact_b.content) > 100
                        else fact_b.content,
                        "observed_at": fact_b.observed_at,
                        "confidence": fact_b.confidence,
                        "source": fact_b.source,
                    },
                }

                conflicts_with_context.append(conflict_context)

            except Exception as e:
                print(f"Warning: Could not load conflict {conflict_file}: {e}")
                continue

        # Sort by detection time (newest first)
        conflicts_with_context.sort(
            key=lambda x: x["detected_at"].isoformat()
            if hasattr(x["detected_at"], "isoformat")
            else str(x["detected_at"]),
            reverse=True,
        )

        return conflicts_with_context[:limit]

    def get_conflict_summary(self) -> Dict[str, Any]:
        """Get a summary of conflict statistics."""
        open_conflicts = (
            len(list((self.conflicts_dir / "open").glob("*.json")))
            if (self.conflicts_dir / "open").exists()
            else 0
        )
        resolved_conflicts = (
            len(list((self.conflicts_dir / "resolved").glob("*.json")))
            if (self.conflicts_dir / "resolved").exists()
            else 0
        )

        # Count conflicts by type (from open conflicts)
        conflict_types: dict[str, int] = {}
        if (self.conflicts_dir / "open").exists():
            for conflict_file in (self.conflicts_dir / "open").glob("*.json"):
                try:
                    conflict_data = json.loads(conflict_file.read_text())
                    conflict_type = conflict_data.get("conflict_type", "UNCERTAIN")
                    conflict_types[conflict_type] = conflict_types.get(conflict_type, 0) + 1
                except Exception:
                    continue

        return {
            "total_open": open_conflicts,
            "total_resolved": resolved_conflicts,
            "total_all": open_conflicts + resolved_conflicts,
            "by_type": conflict_types,
            "resolution_rate": round(
                resolved_conflicts / (open_conflicts + resolved_conflicts) * 100, 1
            )
            if (open_conflicts + resolved_conflicts) > 0
            else 0.0,
        }

    def resolve_conflict_interactive(
        self, conflict_id: str, winning_fact: str, reason: str
    ) -> bool:
        """Resolve a conflict with full validation."""
        conflict_file = self.conflicts_dir / "open" / f"{conflict_id}.json"

        if not conflict_file.exists():
            # Try short ID match
            for file in (self.conflicts_dir / "open").glob("*.json"):
                if file.stem.startswith(conflict_id):
                    conflict_file = file
                    conflict_id = file.stem
                    break
            else:
                return False

        try:
            # Load conflict
            conflict_data = json.loads(conflict_file.read_text())
            conflict = Conflict(**conflict_data)

            # Validate winning fact
            if winning_fact not in ["a", "b", "fact_a", "fact_b"]:
                return False

            winning_hash = (
                conflict.fact_a_hash if winning_fact in ["a", "fact_a"] else conflict.fact_b_hash
            )

            # Update conflict
            conflict.conflict_status = ConflictStatus.USER_RESOLVED
            conflict.resolution_fact_hash = winning_hash
            conflict.resolution_reason = reason
            conflict.resolved_at = datetime.utcnow()

            # Move to resolved
            resolved_file = self.conflicts_dir / "resolved" / f"{conflict_id}.json"
            resolved_file.parent.mkdir(exist_ok=True)
            resolved_file.write_text(json.dumps(conflict.__dict__, default=str, indent=2))
            conflict_file.unlink()  # Remove from open

            return True

        except Exception as e:
            print(f"Error resolving conflict: {e}")
            return False

    def _time_ago(self, timestamp: datetime) -> str:
        """Human-readable time ago string."""
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        now = datetime.utcnow()
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=None)
        if now.tzinfo is not None:
            now = now.replace(tzinfo=None)

        diff = now - timestamp

        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "just now"


def create_enhanced_conflict_commands():
    """Enhanced CLI commands for conflict management."""
    import typer
    from rich.console import Console
    from rich.table import Table
    from rich.prompt import Prompt
    from pathlib import Path

    console = Console()

    def conflicts_list(
        since: Optional[str] = typer.Option(None, help="Show conflicts since date (YYYY-MM-DD)"),
        search: Optional[str] = typer.Option(None, help="Search in conflict content"),
        entity: Optional[str] = typer.Option(None, help="Filter by entity"),
        resolved: bool = typer.Option(False, help="Show resolved conflicts"),
        limit: int = typer.Option(20, help="Maximum conflicts to show"),
    ):
        """List conflicts with advanced filtering."""
        manager = ConflictManager(Path.cwd())

        # Parse date filter
        since_date = None
        if since:
            try:
                since_date = datetime.fromisoformat(since)
            except ValueError:
                console.print(f"[red]Invalid date format: {since}. Use YYYY-MM-DD[/red]")
                return

        # Get filtered conflicts
        status = ConflictStatus.USER_RESOLVED if resolved else ConflictStatus.UNRESOLVED
        conflicts = manager.list_conflicts_with_context(
            since=since_date,
            search_term=search,
            entity_filter=entity,
            status_filter=status,
            limit=limit,
        )

        if not conflicts:
            console.print("[yellow]No conflicts found matching your criteria.[/yellow]")
            return

        # Display conflicts in table
        table = Table(title=f"{'Resolved' if resolved else 'Open'} Conflicts")
        table.add_column("ID", style="cyan")
        table.add_column("Entity/Attribute", style="green")
        table.add_column("Conflict", style="yellow")
        table.add_column("Type", style="blue")
        table.add_column("When", style="dim")

        for conflict in conflicts:
            table.add_row(
                conflict["short_id"],
                f"{conflict['entity']}/{conflict['attribute']}",
                f"'{conflict['fact_a']['value']}' vs '{conflict['fact_b']['value']}'",
                conflict["conflict_type"],
                conflict["time_ago"],
            )

        console.print(table)
        console.print(f"\nShowing {len(conflicts)} conflicts")
        console.print("Use [cyan]memora conflicts resolve <id>[/cyan] to resolve")

    def conflicts_resolve(
        conflict_id: str = typer.Argument(help="Conflict ID (short form accepted)"),
        winner: Optional[str] = typer.Option(None, help="Winner: 'a' or 'b'"),
        reason: Optional[str] = typer.Option(None, help="Resolution reason"),
    ):
        """Resolve a conflict interactively."""
        manager = ConflictManager(Path.cwd())

        # Get conflict details
        conflicts = manager.list_conflicts_with_context(limit=1000)
        matching_conflict = None

        for conflict in conflicts:
            if (
                conflict["conflict_id"].startswith(conflict_id)
                or conflict["short_id"] == conflict_id
            ):
                matching_conflict = conflict
                break

        if not matching_conflict:
            console.print(f"[red]Conflict not found: {conflict_id}[/red]")
            return

        # Show conflict details
        console.print("\n[bold]Conflict Details[/bold]")
        console.print(f"Entity: [cyan]{matching_conflict['entity']}[/cyan]")
        console.print(f"Attribute: [cyan]{matching_conflict['attribute']}[/cyan]")
        console.print(f"Type: [yellow]{matching_conflict['conflict_type']}[/yellow]")
        console.print()

        # Show both facts
        console.print("[bold]Fact A (older):[/bold]")
        fact_a = matching_conflict["fact_a"]
        console.print(f"  Value: [green]{fact_a['value']}[/green]")
        console.print(f"  Content: {fact_a['content']}")
        console.print(f"  When: {fact_a['observed_at']}")
        console.print(f"  Confidence: {fact_a['confidence']}")
        console.print()

        console.print("[bold]Fact B (newer):[/bold]")
        fact_b = matching_conflict["fact_b"]
        console.print(f"  Value: [green]{fact_b['value']}[/green]")
        console.print(f"  Content: {fact_b['content']}")
        console.print(f"  When: {fact_b['observed_at']}")
        console.print(f"  Confidence: {fact_b['confidence']}")
        console.print()

        # Get user choice
        if not winner:
            winner = Prompt.ask(
                "Which fact should be kept?", choices=["a", "b", "both"], default="b"
            )

        if not reason:
            reason = Prompt.ask("Reason for resolution", default="User preference")

        # Resolve conflict
        if winner == "both":
            console.print(
                "[yellow]Both facts kept - conflict marked as resolved but both values remain.[/yellow]"
            )
            # Keep both facts, just mark conflict as resolved
            success = manager.resolve_conflict_interactive(
                matching_conflict["conflict_id"], "a", f"Both kept: {reason}"
            )
        else:
            success = manager.resolve_conflict_interactive(
                matching_conflict["conflict_id"], winner, reason
            )

        if success:
            console.print(f"[green]✓[/green] Conflict resolved: kept fact {winner.upper()}")
        else:
            console.print("[red]✗[/red] Failed to resolve conflict")

    def conflicts_summary():
        """Show conflict statistics summary."""
        manager = ConflictManager(Path.cwd())
        summary = manager.get_conflict_summary()

        table = Table(title="Conflict Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Open Conflicts", str(summary["total_open"]))
        table.add_row("Resolved Conflicts", str(summary["total_resolved"]))
        table.add_row("Resolution Rate", f"{summary['resolution_rate']}%")

        console.print(table)

        if summary["by_type"]:
            console.print("\n[bold]Conflicts by Type:[/bold]")
            for conflict_type, count in summary["by_type"].items():
                console.print(f"  {conflict_type}: {count}")

    return {
        "conflicts_list": conflicts_list,
        "conflicts_resolve": conflicts_resolve,
        "conflicts_summary": conflicts_summary,
    }


# Enhanced conflict resolution algorithms
