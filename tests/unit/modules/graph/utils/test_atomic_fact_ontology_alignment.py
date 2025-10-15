"""Regression tests for AtomicFact entity resolution alignment.

These tests ensure that AtomicFact-derived entities work correctly with
existing ontology resolution and entity processing logic.
"""

import pytest
from uuid import uuid4
from cognee.modules.engine.models import Entity, AtomicFact, FactType, TemporalType
from cognee.modules.engine.utils import generate_node_name, generate_node_id
from cognee.modules.graph.utils.get_graph_from_model import get_graph_from_model


class TestAtomicFactEntityNormalizationRegression:
    """Regression tests to ensure AtomicFact entities use same normalization as KnowledgeGraph."""

    @pytest.mark.asyncio
    async def test_atomic_fact_normalization_matches_knowledge_graph(self):
        """Verify AtomicFact entities use same normalization as KnowledgeGraph entities."""
        # Create fact
        fact = AtomicFact(
            subject="John's Company",
            predicate="located in",
            object="New York City",
            source_chunk_id=uuid4(),
            source_text="John's Company is located in New York City.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.9
        )

        nodes, _ = await get_graph_from_model(fact, {}, {})

        # Get entities
        entities = [n for n in nodes if isinstance(n, Entity)]

        # Verify ALL entities have normalized names
        for entity in entities:
            # Name should be lowercase
            assert entity.name == entity.name.lower(), f"Entity name {entity.name} not lowercase"
            # Name should have no apostrophes
            assert "'" not in entity.name, f"Entity name {entity.name} contains apostrophe"

    @pytest.mark.asyncio
    async def test_atomic_fact_ids_use_uuid5(self):
        """Verify AtomicFact entities use UUID5 for IDs (not string concatenation)."""
        fact = AtomicFact(
            subject="Tesla",
            predicate="manufactures",
            object="Electric Cars",
            source_chunk_id=uuid4(),
            source_text="Tesla manufactures electric cars.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.9
        )

        nodes, _ = await get_graph_from_model(fact, {}, {})

        # Get entities
        entities = [n for n in nodes if isinstance(n, Entity)]

        # Verify ALL entity IDs are valid UUIDs (not strings with underscores)
        for entity in entities:
            entity_id_str = str(entity.id)
            # Should not contain "_subject" or "_object" suffixes
            assert "_subject" not in entity_id_str, f"Entity ID {entity_id_str} contains '_subject'"
            assert "_object" not in entity_id_str, f"Entity ID {entity_id_str} contains '_object'"
            # Should be a valid UUID format (has dashes in correct positions)
            assert entity_id_str.count('-') == 4, f"Entity ID {entity_id_str} not valid UUID format"

    @pytest.mark.asyncio
    async def test_atomic_fact_entity_deduplication(self):
        """Verify that duplicate entities across facts are deduplicated."""
        # Create two facts sharing an entity
        fact1 = AtomicFact(
            subject="Microsoft",
            predicate="founded by",
            object="Bill Gates",
            source_chunk_id=uuid4(),
            source_text="Microsoft was founded by Bill Gates.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.9
        )

        fact2 = AtomicFact(
            subject="Microsoft",
            predicate="headquartered in",
            object="Redmond",
            source_chunk_id=uuid4(),
            source_text="Microsoft is headquartered in Redmond.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.9
        )

        # Process both facts with shared node tracking
        added_nodes = {}
        added_edges = {}
        nodes1, edges1 = await get_graph_from_model(fact1, added_nodes, added_edges)
        nodes2, edges2 = await get_graph_from_model(fact2, added_nodes, added_edges)

        # Get all Microsoft entities
        microsoft_name = generate_node_name("Microsoft")
        microsoft_id = generate_node_id("Microsoft")

        entities1 = [n for n in nodes1 if isinstance(n, Entity) and n.name == microsoft_name]
        entities2 = [n for n in nodes2 if isinstance(n, Entity) and n.name == microsoft_name]

        # First fact should create Microsoft entity
        assert len(entities1) == 1, "First fact should create Microsoft entity"
        assert entities1[0].id == microsoft_id

        # Second fact should NOT create duplicate Microsoft entity (deduplication)
        assert len(entities2) == 0, "Second fact should not create duplicate Microsoft entity"

        # Verify deduplication via added_nodes tracking
        assert str(microsoft_id) in added_nodes, "Microsoft entity should be tracked in added_nodes"

    @pytest.mark.asyncio
    async def test_atomic_fact_edge_references_valid_entities(self):
        """Verify that edges reference valid entity UUIDs."""
        fact = AtomicFact(
            subject="Python",
            predicate="created by",
            object="Guido van Rossum",
            source_chunk_id=uuid4(),
            source_text="Python was created by Guido van Rossum.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.9
        )

        nodes, edges = await get_graph_from_model(fact, {}, {})

        # Get entity IDs
        entities = [n for n in nodes if isinstance(n, Entity)]
        entity_ids = {str(e.id) for e in entities}

        # Verify all edges reference valid entity IDs
        for edge in edges:
            source_id, target_id, rel_name, props = edge
            assert str(source_id) in entity_ids, f"Edge source {source_id} not in entity IDs"
            assert str(target_id) in entity_ids, f"Edge target {target_id} not in entity IDs"


class TestBackwardCompatibility:
    """Tests to ensure non-AtomicFact entities still work correctly."""

    @pytest.mark.asyncio
    async def test_non_atomic_fact_entities_unaffected(self):
        """Verify that non-AtomicFact entities are not affected by changes."""
        # Create a regular Entity (not from AtomicFact)
        entity_id = uuid4()
        entity = Entity(
            id=entity_id,
            name="TestEntity",
            description="Test description"
        )

        # Process through get_graph_from_model
        nodes, edges = await get_graph_from_model(entity, {}, {})

        # Should include the entity (check by ID since object identity may differ)
        assert len(nodes) >= 1
        node_ids = [n.id for n in nodes]
        assert entity_id in node_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
