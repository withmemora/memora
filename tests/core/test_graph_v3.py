"""Tests for knowledge graph v3.0.

This module tests:
- Adding nodes and edges
- Graph traversal and queries
- Profile assembly
- NER entities feed graph (not memory store)
"""

from pathlib import Path

import pytest

from memora.core.graph import KnowledgeGraph


@pytest.fixture
def temp_store(tmp_path: Path) -> Path:
    """Create a temporary .memora directory."""
    store_path = tmp_path / ".memora"
    store_path.mkdir()
    return store_path


@pytest.fixture
def graph(temp_store: Path) -> KnowledgeGraph:
    """Create a KnowledgeGraph instance."""
    return KnowledgeGraph(temp_store)


class TestGraphNodeOperations:
    """Test adding and retrieving graph nodes."""

    def test_add_node(self, graph: KnowledgeGraph):
        """Test adding a node to the graph."""
        node_id = graph.add_node(name="Microsoft", node_type="organization")

        assert node_id == "microsoft"

    def test_add_node_creates_file(self, graph: KnowledgeGraph):
        """Test that adding a node creates nodes.json file."""
        graph.add_node(name="Sarah", node_type="person")

        assert graph.nodes_file.exists()

    def test_get_node(self, graph: KnowledgeGraph):
        """Test retrieving a node."""
        node_id = graph.add_node(name="Python", node_type="technology")
        nodes = graph.get_nodes()
        node = next((n for n in nodes if n["id"] == node_id), None)

        assert node is not None
        assert node["name"] == "Python"
        assert node["type"] == "technology"

    def test_add_duplicate_node_updates_existing(self, graph: KnowledgeGraph):
        """Test that adding duplicate node updates existing one."""
        # Add same node twice
        id1 = graph.add_node(name="Google", node_type="organization", memory_id="mem_1")
        id2 = graph.add_node(name="Google", node_type="organization", memory_id="mem_2")

        assert id1 == id2

        nodes = graph.get_nodes()
        node = next((n for n in nodes if n["id"] == id1), None)
        # Memory count should increase
        assert node["memory_count"] >= 2


class TestGraphEdgeOperations:
    """Test adding and retrieving graph edges."""

    def test_add_edge(self, graph: KnowledgeGraph):
        """Test adding an edge to the graph."""
        # Add nodes first
        graph.add_node("User", "person")
        graph.add_node("Microsoft", "organization")

        # Add edge
        edge_id = graph.add_edge(
            source_id="user",
            relation="works_at",
            target_id="microsoft",
            confidence=0.95,
            memory_id="mem_xyz",
        )

        assert edge_id.startswith("edge_")

    def test_get_edges_from_node(self, graph: KnowledgeGraph):
        """Test getting all edges from a node."""
        graph.add_node("User", "person")
        graph.add_node("Python", "technology")

        graph.add_edge("user", "uses", "python", 0.90, "mem_1")

        edges = graph.get_edges_from("user")
        assert len(edges) >= 1
        assert edges[0]["relation"] == "uses"

    def test_supersede_edge(self, graph: KnowledgeGraph):
        """Test marking an edge as superseded."""
        graph.add_node("User", "person")
        graph.add_node("Seattle", "location")

        edge_id = graph.add_edge("user", "lives_in", "seattle", 0.92, "mem_1")

        # Supersede the edge
        success = graph.supersede_edge(edge_id)

        assert success
        edges = graph._load_edges()
        superseded_edge = next(e for e in edges if e["id"] == edge_id)
        assert superseded_edge["superseded_at"] is not None


class TestGraphTraversal:
    """Test graph traversal and pathfinding."""

    def test_get_neighbors(self, graph: KnowledgeGraph):
        """Test getting neighboring edges."""
        graph.add_node("User", "person")
        graph.add_node("Microsoft", "organization")
        graph.add_node("Seattle", "location")

        graph.add_edge("user", "works_at", "microsoft", 0.95)
        graph.add_edge("microsoft", "located_in", "seattle", 0.90)

        # Get neighbor edges of microsoft
        neighbors = graph.get_neighbors("microsoft")

        # neighbors is a list of edge dicts
        assert len(neighbors) == 2
        # Check that edges contain microsoft as source or target
        sources_and_targets = set()
        for edge in neighbors:
            sources_and_targets.add(edge["source"])
            sources_and_targets.add(edge["target"])

        assert "microsoft" in sources_and_targets

    def test_find_path(self, graph: KnowledgeGraph):
        """Test finding path between two nodes."""
        graph.add_node("User", "person")
        graph.add_node("Marcus", "person")
        graph.add_node("Stripe", "organization")

        graph.add_edge("user", "knows", "marcus", 0.90)
        graph.add_edge("marcus", "works_at", "stripe", 0.95)

        # Find path from user to stripe
        path = graph.find_path("user", "stripe")

        assert path is not None
        assert len(path) >= 2  # At least user → marcus → stripe


class TestProfileAssembly:
    """Test assembling user profile from graph."""

    def test_build_profile(self, graph: KnowledgeGraph):
        """Test building user profile from graph."""
        # Add user and related entities
        graph.add_node("User", "person")
        graph.add_node("Microsoft", "organization")
        graph.add_node("Python", "technology")
        graph.add_node("Seattle", "location")

        graph.add_edge("user", "works_at", "microsoft", 0.95)
        graph.add_edge("user", "uses", "python", 0.90)
        graph.add_edge("microsoft", "located_in", "seattle", 0.85)

        profile = graph.build_profile()

        assert isinstance(profile, dict)
        # Profile should have some information
        assert len(profile) > 0


class TestGraphQueries:
    """Test querying the graph."""

    def test_query_entity(self, graph: KnowledgeGraph):
        """Test querying what the graph knows about an entity using get_edges_from."""
        graph.add_node("User", "person")
        graph.add_node("Python", "technology")
        graph.add_node("Rust", "technology")

        graph.add_edge("user", "uses", "python", 0.92)
        graph.add_edge("user", "considering", "rust", 0.80)

        # Query user's outgoing edges
        edges = graph.get_edges_from("user")

        assert len(edges) >= 2
        relations = [e["relation"] for e in edges]
        assert "uses" in relations
        assert "considering" in relations

    def test_get_nodes_by_type(self, graph: KnowledgeGraph):
        """Test getting all nodes of a specific type using get_nodes(node_type=...)."""
        graph.add_node("Microsoft", "organization")
        graph.add_node("Google", "organization")
        graph.add_node("Python", "technology")

        orgs = graph.get_nodes(node_type="organization")

        assert len(orgs) >= 2
        org_names = [o["name"] for o in orgs]
        assert "Microsoft" in org_names
        assert "Google" in org_names


class TestNERIntegration:
    """Test that NER entities feed the graph, not memory store."""

    def test_ner_entities_create_nodes(self, graph: KnowledgeGraph):
        """Test that NER-extracted entities become graph nodes."""
        # Simulate NER extraction
        graph.add_node("Microsoft", "organization", memory_id="mem_1")
        graph.add_node("Seattle", "location", memory_id="mem_1")

        nodes = graph._load_nodes()

        node_names = [n["name"] for n in nodes]
        assert "Microsoft" in node_names
        assert "Seattle" in node_names

    def test_ner_relations_create_edges(self, graph: KnowledgeGraph):
        """Test that NER-inferred relations create edges."""
        graph.add_node("User", "person")
        graph.add_node("Microsoft", "organization")

        # Relation inferred from context
        graph.add_edge("user", "works_at", "microsoft", 0.88, memory_id="mem_1")

        edges = graph._load_edges()
        work_edges = [e for e in edges if e["relation"] == "works_at"]

        assert len(work_edges) >= 1
