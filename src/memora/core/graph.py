"""Knowledge graph for Memora v3.0.

Append-only graph with nodes and edges. NER output feeds into this, not the memory store.
Conflicting edges get a superseded_at field.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from memora.shared.models import GraphNode, GraphEdge, now_iso


class KnowledgeGraph:
    """Append-only knowledge graph stored as JSON files."""

    def __init__(self, store_path: Path):
        self.store_path = store_path
        self.graph_path = store_path / "graph"
        self.nodes_file = self.graph_path / "nodes.json"
        self.edges_file = self.graph_path / "edges.json"

    def _load_nodes(self) -> list[dict]:
        if not self.nodes_file.exists():
            return []
        try:
            return json.loads(self.nodes_file.read_text())
        except Exception:
            return []

    def _save_nodes(self, nodes: list[dict]) -> None:
        self.graph_path.mkdir(parents=True, exist_ok=True)
        self.nodes_file.write_text(json.dumps(nodes, indent=2))

    def _load_edges(self) -> list[dict]:
        if not self.edges_file.exists():
            return []
        try:
            return json.loads(self.edges_file.read_text())
        except Exception:
            return []

    def _save_edges(self, edges: list[dict]) -> None:
        self.graph_path.mkdir(parents=True, exist_ok=True)
        self.edges_file.write_text(json.dumps(edges, indent=2))

    def add_node(self, name: str, node_type: str, memory_id: str = "") -> str:
        """Add or update a node. Returns node ID."""
        node_id = name.lower().replace(" ", "_")
        nodes = self._load_nodes()
        now = now_iso()

        for node in nodes:
            if node["id"] == node_id:
                node["last_seen"] = now
                node["memory_count"] = node.get("memory_count", 0) + 1
                self._save_nodes(nodes)
                return node_id

        new_node = {
            "id": node_id,
            "name": name,
            "type": node_type,
            "first_seen": now,
            "last_seen": now,
            "memory_count": 1,
        }
        nodes.append(new_node)
        self._save_nodes(nodes)
        return node_id

    def add_edge(
        self, source_id: str, relation: str, target_id: str, confidence: float, memory_id: str = ""
    ) -> str:
        """Add an edge. Returns edge ID."""
        import uuid

        edge_id = f"edge_{uuid.uuid4().hex[:8]}"
        edges = self._load_edges()

        new_edge = {
            "id": edge_id,
            "source": source_id,
            "relation": relation,
            "target": target_id,
            "confidence": confidence,
            "created_at": now_iso(),
            "superseded_at": None,
            "memory_id": memory_id,
        }
        edges.append(new_edge)
        self._save_edges(edges)
        return edge_id

    def supersede_edge(self, edge_id: str) -> bool:
        """Mark an edge as superseded."""
        edges = self._load_edges()
        for edge in edges:
            if edge["id"] == edge_id:
                edge["superseded_at"] = now_iso()
                self._save_edges(edges)
                return True
        return False

    def get_neighbors(self, node_id: str) -> list[dict]:
        """Get all edges connected to a node."""
        edges = self._load_edges()
        return [
            e
            for e in edges
            if (e["source"] == node_id or e["target"] == node_id) and e.get("superseded_at") is None
        ]

    def get_edges_from(self, source_id: str) -> list[dict]:
        """Get all outgoing edges from a node."""
        edges = self._load_edges()
        return [e for e in edges if e["source"] == source_id and e.get("superseded_at") is None]

    def find_path(self, source_id: str, target_id: str, max_depth: int = 3) -> list[dict]:
        """Find a path between two nodes using BFS."""
        edges = self._load_edges()
        active_edges = [e for e in edges if e.get("superseded_at") is None]

        visited = set()
        queue = [(source_id, [])]

        while queue:
            current, path = queue.pop(0)
            if current == target_id and path:
                return path
            if current in visited or len(path) >= max_depth:
                continue
            visited.add(current)

            for edge in active_edges:
                if edge["source"] == current and edge["target"] not in visited:
                    queue.append((edge["target"], path + [edge]))
                elif edge["target"] == current and edge["source"] not in visited:
                    queue.append((edge["source"], path + [edge]))

        return []

    def get_nodes(self, node_type: Optional[str] = None) -> list[dict]:
        """Get all nodes, optionally filtered by type."""
        nodes = self._load_nodes()
        if node_type:
            return [n for n in nodes if n["type"] == node_type]
        return nodes

    def build_profile(self) -> dict:
        """Assemble a user profile from the graph."""
        nodes = self._load_nodes()
        edges = self._load_edges()
        active_edges = [e for e in edges if e.get("superseded_at") is None]

        profile = {
            "works_at": [],
            "languages": [],
            "tools": [],
            "knows": [],
            "building": [],
            "considering": [],
        }

        user_edges = [e for e in active_edges if e["source"] == "user"]

        for edge in user_edges:
            relation = edge["relation"]
            target = edge["target"]

            if relation == "works_at":
                profile["works_at"].append(target)
            elif relation == "knows":
                profile["knows"].append(target)
            elif relation == "building":
                profile["building"].append(target)
            elif relation == "considering":
                profile["considering"].append(target)
            elif relation == "uses":
                profile["tools"].append(target)
            elif relation == "prefers":
                profile["tools"].append(target)

        for node in nodes:
            if node["type"] == "technology" and node["id"] not in profile["languages"]:
                lang_edges = [
                    e
                    for e in active_edges
                    if e["target"] == node["id"] and e["relation"] in ("knows", "uses", "prefers")
                ]
                if lang_edges:
                    profile["languages"].append(node["name"])

        return profile

    def update_from_ner(
        self, ner_entities: list[dict], context_relations: list[dict] = None
    ) -> None:
        """Add nodes from NER output."""
        for ent in ner_entities:
            self.add_node(ent["name"], ent["type"])

        if context_relations:
            for rel in context_relations:
                source_id = rel.get("source", "").lower().replace(" ", "_")
                target_id = rel.get("target", "").lower().replace(" ", "_")
                relation = rel.get("relation", "related_to")
                confidence = rel.get("confidence", 0.80)
                self.add_edge(source_id, relation, target_id, confidence)
