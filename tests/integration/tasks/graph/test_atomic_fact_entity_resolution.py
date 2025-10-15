"""Integration tests for AtomicFact entity resolution alignment.

This test suite verifies that AtomicFact-generated entities work correctly
with Cognee's ontology resolution system.
"""

import pytest
from uuid import uuid4
from cognee.modules.engine.models import Entity, AtomicFact, FactType, TemporalType
from cognee.modules.engine.utils import generate_node_name, generate_node_id
from cognee.modules.graph.utils.get_graph_from_model import get_graph_from_model


class TestAtomicFactEntityNormalization:
    """Test entity name normalization for AtomicFacts."""

    @pytest.mark.asyncio
    async def test_atomic_fact_entity_names_raw(self):
        """Verify that AtomicFact entities are created with raw names."""
        fact = AtomicFact(
            subject="John Smith",
            predicate="works at",
            object="Google Inc.",
            source_chunk_id=uuid4(),
            source_text="John Smith works at Google Inc.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.9
        )

        nodes, edges = await get_graph_from_model(fact, {}, {})

        # Find subject and object entities by normalized names
        expected_subject_name = generate_node_name("John Smith")  # "john smith"
        expected_object_name = generate_node_name("Google Inc.")  # "google inc"

        # Find entities by name (now normalized)
        entities = [n for n in nodes if isinstance(n, Entity)]
        subject_entity = next((e for e in entities if e.name == expected_subject_name), None)
        object_entity = next((e for e in entities if e.name == expected_object_name), None)

        # FIXED BEHAVIOR: Names ARE normalized
        assert subject_entity is not None, "Subject entity not found"
        assert object_entity is not None, "Object entity not found"
        assert subject_entity.name == expected_subject_name  # Normalized
        assert object_entity.name == expected_object_name  # Normalized

    @pytest.mark.asyncio
    async def test_atomic_fact_entity_names_with_apostrophe(self):
        """Verify handling of apostrophes in entity names."""
        fact = AtomicFact(
            subject="Tesla's CEO",
            predicate="is",
            object="Elon Musk",
            source_chunk_id=uuid4(),
            source_text="Tesla's CEO is Elon Musk.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.9
        )

        nodes, edges = await get_graph_from_model(fact, {}, {})

        # Expected normalized names (apostrophe removed)
        expected_subject = generate_node_name("Tesla's CEO")  # "teslas ceo"
        expected_object = generate_node_name("Elon Musk")  # "elon musk"

        # Find entities by normalized name
        entities = [n for n in nodes if isinstance(n, Entity)]
        subject_entity = next((e for e in entities if e.name == expected_subject), None)
        object_entity = next((e for e in entities if e.name == expected_object), None)

        # FIXED BEHAVIOR: Apostrophe IS removed through normalization
        assert subject_entity is not None
        assert object_entity is not None
        assert subject_entity.name == expected_subject  # Normalized
        assert object_entity.name == expected_object  # Normalized

    @pytest.mark.asyncio
    async def test_atomic_fact_entity_ids_are_uuid5(self):
        """Verify that AtomicFact entity IDs ARE UUID5 based on normalized names."""
        fact = AtomicFact(
            subject="John Smith",
            predicate="works at",
            object="Google",
            source_chunk_id=uuid4(),
            source_text="John Smith works at Google.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.9
        )

        nodes, edges = await get_graph_from_model(fact, {}, {})

        # Get expected UUID5 IDs based on normalized names
        expected_subject_id = generate_node_id("John Smith")
        expected_object_id = generate_node_id("Google")

        # Find entities
        expected_subject_name = generate_node_name("John Smith")
        expected_object_name = generate_node_name("Google")
        entities = [n for n in nodes if isinstance(n, Entity)]
        subject_entity = next((e for e in entities if e.name == expected_subject_name), None)
        object_entity = next((e for e in entities if e.name == expected_object_name), None)

        # FIXED BEHAVIOR: IDs ARE UUID5 based on normalized names
        assert subject_entity is not None
        assert object_entity is not None
        assert subject_entity.id == expected_subject_id
        assert object_entity.id == expected_object_id


class TestAtomicFactEntityDeduplication:
    """Test entity deduplication scenarios."""

    @pytest.mark.asyncio
    async def test_same_entity_different_facts(self):
        """Test that same entity in different facts creates different Entity instances."""
        fact1 = AtomicFact(
            subject="John Smith",
            predicate="works at",
            object="Google",
            source_chunk_id=uuid4(),
            source_text="John Smith works at Google.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.9
        )

        fact2 = AtomicFact(
            subject="John Smith",
            predicate="lives in",
            object="New York",
            source_chunk_id=uuid4(),
            source_text="John Smith lives in New York.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.9
        )

        nodes1, _ = await get_graph_from_model(fact1, {}, {})
        nodes2, _ = await get_graph_from_model(fact2, {}, {})

        # Get expected values
        expected_name = generate_node_name("John Smith")
        expected_id = generate_node_id("John Smith")

        entities1 = [n for n in nodes1 if isinstance(n, Entity)]
        entities2 = [n for n in nodes2 if isinstance(n, Entity)]

        subject1 = next((e for e in entities1 if e.name == expected_name), None)
        subject2 = next((e for e in entities2 if e.name == expected_name), None)

        # FIXED BEHAVIOR: Same IDs because same entity (UUID5 based on normalized name)
        assert subject1 is not None
        assert subject2 is not None
        assert subject1.id == subject2.id  # Same UUID5
        assert subject1.name == subject2.name  # Both normalized "john smith"
        assert subject1.id == expected_id  # Matches expected UUID5

    @pytest.mark.asyncio
    async def test_case_variants_create_same_entity(self):
        """Test that case variants of same entity create the SAME Entity instance (deduplication)."""
        fact1 = AtomicFact(
            subject="JOHN SMITH",
            predicate="works at",
            object="Google",
            source_chunk_id=uuid4(),
            source_text="JOHN SMITH works at Google.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.9
        )

        fact2 = AtomicFact(
            subject="john smith",
            predicate="lives in",
            object="NYC",
            source_chunk_id=uuid4(),
            source_text="john smith lives in NYC.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.9
        )

        nodes1, _ = await get_graph_from_model(fact1, {}, {})
        nodes2, _ = await get_graph_from_model(fact2, {}, {})

        # Both normalize to same name
        normalized_name = generate_node_name("John Smith")  # "john smith"
        normalized_id = generate_node_id("John Smith")

        entities1 = [n for n in nodes1 if isinstance(n, Entity)]
        entities2 = [n for n in nodes2 if isinstance(n, Entity)]

        subject1 = next((e for e in entities1 if e.name == normalized_name), None)
        subject2 = next((e for e in entities2 if e.name == normalized_name), None)

        # FIXED BEHAVIOR: Same name and ID (normalization handles case)
        assert subject1 is not None
        assert subject2 is not None
        assert subject1.name == subject2.name == normalized_name  # Both normalized
        assert subject1.id == subject2.id == normalized_id  # Same UUID5


class TestAtomicFactEntityTypeInference:
    """Test entity type assignment for AtomicFact entities."""

    @pytest.mark.asyncio
    async def test_atomic_fact_entities_have_no_type(self):
        """Verify that AtomicFact entities are created without type assignment."""
        fact = AtomicFact(
            subject="John Smith",
            predicate="works at",
            object="Google Inc.",
            source_chunk_id=uuid4(),
            source_text="John Smith works at Google Inc.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.9
        )

        nodes, _ = await get_graph_from_model(fact, {}, {})

        # Find entities
        expected_subject_name = generate_node_name("John Smith")
        expected_object_name = generate_node_name("Google Inc.")
        entities = [n for n in nodes if isinstance(n, Entity)]
        subject_entity = next((e for e in entities if e.name == expected_subject_name), None)
        object_entity = next((e for e in entities if e.name == expected_object_name), None)

        # AtomicFact entities have no type inference (not processed through ontology resolution)
        # is_a field will be None or not set
        assert subject_entity is not None
        assert object_entity is not None
        assert not hasattr(subject_entity, 'is_a') or subject_entity.is_a is None
        assert not hasattr(object_entity, 'is_a') or object_entity.is_a is None

    @pytest.mark.asyncio
    async def test_atomic_fact_entities_not_ontology_validated(self):
        """Verify that AtomicFact entities are not ontology-validated."""
        fact = AtomicFact(
            subject="John Smith",
            predicate="works at",
            object="Google",
            source_chunk_id=uuid4(),
            source_text="John Smith works at Google.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.9
        )

        nodes, _ = await get_graph_from_model(fact, {}, {})

        # Find entity
        expected_subject_name = generate_node_name("John Smith")
        entities = [n for n in nodes if isinstance(n, Entity)]
        subject_entity = next((e for e in entities if e.name == expected_subject_name), None)

        # ontology_valid field should be False or not set
        assert subject_entity is not None
        assert not hasattr(subject_entity, 'ontology_valid') or subject_entity.ontology_valid is False


class TestAtomicFactOntologyMatching:
    """Test ontology matching behavior (or lack thereof) for AtomicFact entities."""

    @pytest.mark.skip(reason="Ontology matching not implemented for AtomicFacts - this is the issue we're testing")
    @pytest.mark.asyncio
    async def test_atomic_fact_entity_canonical_name_substitution(self):
        """Test that entity names are substituted with canonical ontology names.

        This test is SKIPPED because AtomicFacts don't currently go through
        ontology resolution. This demonstrates the gap we need to fix.
        """
        # If ontology configured with "John Smith" → "John A. Smith" canonical name
        # Expected behavior: subject entity name should be "john a smith"
        # Actual behavior: subject entity name is "John Smith"
        pass

    @pytest.mark.skip(reason="Ontology matching not implemented for AtomicFacts - this is the issue we're testing")
    @pytest.mark.asyncio
    async def test_atomic_fact_entity_type_inference_from_ontology(self):
        """Test that entity types are inferred from ontology.

        This test is SKIPPED because AtomicFacts don't currently go through
        ontology resolution. This demonstrates the gap we need to fix.
        """
        # If ontology configured with "Google" as type "Organization"
        # Expected behavior: object entity should have is_a=EntityType(name="organization")
        # Actual behavior: object entity has no type
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
