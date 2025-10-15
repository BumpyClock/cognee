# ABOUTME: Tests for AtomicFact graph conversion ensuring temporal metadata is preserved
# ABOUTME: Validates edge creation, temporal properties mapping, and invalidation relationships

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from cognee.modules.engine.models import AtomicFact, FactType, TemporalType
from cognee.modules.graph.utils.get_graph_from_model import get_graph_from_model


class TestAtomicFactGraphConversion:
    """Test suite for converting AtomicFact models to graph representation."""

    @pytest.mark.asyncio
    async def test_atomic_fact_basic_node_creation(self):
        """Test that AtomicFact creates a node with all properties."""
        source_chunk_id = uuid4()
        fact = AtomicFact(
            subject="John",
            predicate="works at",
            object="Google",
            source_chunk_id=source_chunk_id,
            source_text="John works at Google.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.95,
        )

        added_nodes = {}
        added_edges = {}
        nodes, edges = await get_graph_from_model(fact, added_nodes, added_edges)

        # Should create a node for the fact
        assert len(nodes) == 1
        fact_node = nodes[0]

        # Verify node properties
        assert fact_node.subject == "John"
        assert fact_node.predicate == "works at"
        assert fact_node.object == "Google"
        assert fact_node.fact_type == FactType.FACT
        assert fact_node.temporal_type == TemporalType.STATIC
        assert fact_node.confidence == 0.95
        assert fact_node.source_chunk_id == source_chunk_id

    @pytest.mark.asyncio
    async def test_atomic_fact_temporal_properties_included(self):
        """Test that temporal properties are included in node."""
        source_chunk_id = uuid4()
        valid_from = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        valid_until = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)

        fact = AtomicFact(
            subject="CEO",
            predicate="is",
            object="John",
            source_chunk_id=source_chunk_id,
            source_text="CEO is John from 2020 to 2023.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            is_open_interval=False,
            valid_from=valid_from,
            valid_until=valid_until,
            expired_at=valid_until,
            confidence=0.95,
        )

        added_nodes = {}
        added_edges = {}
        nodes, edges = await get_graph_from_model(fact, added_nodes, added_edges)

        fact_node = nodes[0]
        assert fact_node.is_open_interval is False
        assert fact_node.valid_from == valid_from
        assert fact_node.valid_until == valid_until
        assert fact_node.expired_at == valid_until

    @pytest.mark.asyncio
    async def test_atomic_fact_with_invalidation_metadata(self):
        """Test that invalidation metadata is preserved in node."""
        source_chunk_id = uuid4()
        invalidated_by_id = uuid4()
        invalidated_at = int(datetime.now(timezone.utc).timestamp() * 1000)

        fact = AtomicFact(
            subject="CEO",
            predicate="is",
            object="John",
            source_chunk_id=source_chunk_id,
            source_text="CEO is John.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.95,
            invalidated_by=invalidated_by_id,
            invalidated_at=invalidated_at,
        )

        added_nodes = {}
        added_edges = {}
        nodes, edges = await get_graph_from_model(fact, added_nodes, added_edges)

        fact_node = nodes[0]
        assert fact_node.invalidated_by == invalidated_by_id
        assert fact_node.invalidated_at == invalidated_at

    @pytest.mark.asyncio
    async def test_atomic_fact_node_type(self):
        """Test that node has correct type metadata."""
        source_chunk_id = uuid4()
        fact = AtomicFact(
            subject="Test",
            predicate="is",
            object="working",
            source_chunk_id=source_chunk_id,
            source_text="Test is working.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.95,
        )

        added_nodes = {}
        added_edges = {}
        nodes, edges = await get_graph_from_model(fact, added_nodes, added_edges)

        # Verify the type is set correctly
        assert nodes[0].type == "AtomicFact"

    @pytest.mark.asyncio
    async def test_atomic_fact_deduplication(self):
        """Test that the same AtomicFact is not added twice."""
        source_chunk_id = uuid4()
        fact = AtomicFact(
            subject="Test",
            predicate="is",
            object="unique",
            source_chunk_id=source_chunk_id,
            source_text="Test is unique.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.95,
        )

        added_nodes = {}
        added_edges = {}

        # First call
        nodes1, edges1 = await get_graph_from_model(fact, added_nodes, added_edges)
        assert len(nodes1) == 1

        # Second call with same fact - should return empty
        nodes2, edges2 = await get_graph_from_model(fact, added_nodes, added_edges)
        assert len(nodes2) == 0
        assert len(edges2) == 0

    @pytest.mark.asyncio
    async def test_multiple_atomic_facts(self):
        """Test processing multiple different AtomicFacts."""
        source_chunk_id = uuid4()

        fact1 = AtomicFact(
            subject="John",
            predicate="works at",
            object="Google",
            source_chunk_id=source_chunk_id,
            source_text="John works at Google.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.95,
        )

        fact2 = AtomicFact(
            subject="Jane",
            predicate="works at",
            object="Microsoft",
            source_chunk_id=source_chunk_id,
            source_text="Jane works at Microsoft.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.90,
        )

        added_nodes = {}
        added_edges = {}

        nodes1, edges1 = await get_graph_from_model(fact1, added_nodes, added_edges)
        nodes2, edges2 = await get_graph_from_model(fact2, added_nodes, added_edges)

        assert len(nodes1) == 1
        assert len(nodes2) == 1
        assert nodes1[0].subject == "John"
        assert nodes2[0].subject == "Jane"

    @pytest.mark.asyncio
    async def test_atomic_fact_creates_invalidation_edge(self):
        """Test that invalidation relationships create edges between facts."""
        source_chunk_id = uuid4()

        # Create the new fact that supersedes the old one
        new_fact = AtomicFact(
            subject="CEO",
            predicate="is",
            object="Jane",
            source_chunk_id=source_chunk_id,
            source_text="CEO is now Jane.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.98,
        )

        # Create old fact that was invalidated by new fact
        old_fact = AtomicFact(
            subject="CEO",
            predicate="is",
            object="John",
            source_chunk_id=source_chunk_id,
            source_text="CEO is John.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.95,
            invalidated_by=new_fact.id,
            invalidated_at=int(datetime.now(timezone.utc).timestamp() * 1000),
        )

        added_nodes = {}
        added_edges = {}

        # First add the new fact
        nodes1, edges1 = await get_graph_from_model(new_fact, added_nodes, added_edges)

        # Then add the old fact - should create invalidation edge
        nodes2, edges2 = await get_graph_from_model(old_fact, added_nodes, added_edges)

        # Should have both nodes
        assert len(nodes1) == 1
        assert len(nodes2) == 1

        # Should have an invalidation edge from old_fact to new_fact
        assert len(edges1) == 0  # New fact has no invalidation
        assert len(edges2) == 1  # Old fact creates invalidation edge

        edge = edges2[0]
        assert edge[0] == old_fact.id  # source
        assert edge[1] == new_fact.id  # target
        assert edge[2] == "invalidated_by"  # relationship name

        # Edge should have temporal metadata
        edge_props = edge[3]
        assert edge_props["relationship_name"] == "invalidated_by"
        assert edge_props["source_node_id"] == old_fact.id
        assert edge_props["target_node_id"] == new_fact.id
        assert "invalidated_at" in edge_props

    @pytest.mark.asyncio
    async def test_atomic_fact_without_invalidation_no_edge(self):
        """Test that facts without invalidation don't create invalidation edges."""
        source_chunk_id = uuid4()

        fact = AtomicFact(
            subject="CEO",
            predicate="is",
            object="John",
            source_chunk_id=source_chunk_id,
            source_text="CEO is John.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.95,
        )

        added_nodes = {}
        added_edges = {}
        nodes, edges = await get_graph_from_model(fact, added_nodes, added_edges)

        # Should have node but no edges
        assert len(nodes) == 1
        assert len(edges) == 0
