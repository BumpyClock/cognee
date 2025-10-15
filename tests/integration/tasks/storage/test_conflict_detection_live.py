"""
Integration tests for conflict detection with real graph database queries.

Tests that:
1. _query_existing_facts correctly queries the graph for matching facts
2. _update_fact_in_graph correctly persists invalidation metadata
3. Full conflict detection workflow works end-to-end with graph roundtrip
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from cognee.modules.engine.models.AtomicFact import AtomicFact, FactType, TemporalType
from cognee.infrastructure.databases.graph import get_graph_engine
from cognee.tasks.storage.manage_atomic_fact_storage import (
    _query_existing_facts,
    _update_fact_in_graph,
    detect_and_invalidate_conflicting_facts,
)


@pytest.mark.asyncio
async def test_query_existing_facts_returns_matching_facts():
    """Test that _query_existing_facts returns facts with matching subject/predicate."""
    graph_engine = await get_graph_engine()

    # Create a test fact
    fact = AtomicFact(
        id=uuid4(),
        subject="Alice",
        predicate="works_at",
        object="TechCorp",
        source_chunk_id=uuid4(),
        source_text="Alice works at TechCorp.",
        fact_type=FactType.FACT,
        temporal_type=TemporalType.STATIC,
        confidence=0.95,
        valid_from=int(datetime.now(timezone.utc).timestamp() * 1000),
        is_open_interval=True,
    )

    # Store the fact in the graph (you may need to adjust this based on your graph API)
    try:
        # Add the fact to the graph
        await graph_engine.add_nodes([fact])

        # Query for facts with same subject/predicate
        results = await _query_existing_facts(
            graph_engine=graph_engine,
            subject="Alice",
            predicate="works_at"
        )

        # Verify we get the fact back
        assert len(results) > 0, "Should find at least one matching fact"
        found_fact = next((f for f in results if f.id == fact.id), None)
        assert found_fact is not None, "Should find the exact fact we added"
        assert found_fact.subject == "Alice"
        assert found_fact.predicate == "works_at"
        assert found_fact.object == "TechCorp"

    finally:
        # Cleanup: Remove the test fact from the graph
        try:
            await graph_engine.delete_node(str(fact.id))
        except Exception as e:
            # Log but don't fail if cleanup fails
            import logging
            logging.warning(f"Failed to clean up test fact {fact.id}: {e}")


@pytest.mark.asyncio
async def test_query_existing_facts_excludes_invalidated():
    """Test that _query_existing_facts excludes already invalidated facts."""
    graph_engine = await get_graph_engine()

    # Create two facts: one valid, one invalidated
    valid_fact = AtomicFact(
        id=uuid4(),
        subject="Bob",
        predicate="lives_in",
        object="NYC",
        source_chunk_id=uuid4(),
        source_text="Bob lives in NYC.",
        fact_type=FactType.FACT,
        temporal_type=TemporalType.STATIC,
        confidence=0.95,
        valid_from=int(datetime.now(timezone.utc).timestamp() * 1000),
        is_open_interval=True,
        invalidated_at=None,  # Still valid
    )

    invalidated_fact = AtomicFact(
        id=uuid4(),
        subject="Bob",
        predicate="lives_in",
        object="LA",
        source_chunk_id=uuid4(),
        source_text="Bob lives in LA.",
        fact_type=FactType.FACT,
        temporal_type=TemporalType.STATIC,
        confidence=0.90,
        valid_from=int(datetime.now(timezone.utc).timestamp() * 1000),
        is_open_interval=False,
        invalidated_at=int(datetime.now(timezone.utc).timestamp() * 1000),  # Invalidated!
    )

    try:
        # Add both facts to the graph
        await graph_engine.add_nodes([valid_fact, invalidated_fact])

        # Query for facts with same subject/predicate
        results = await _query_existing_facts(
            graph_engine=graph_engine,
            subject="Bob",
            predicate="lives_in"
        )

        # Verify we only get the valid fact (invalidated one should be excluded)
        assert len(results) >= 1, "Should find at least the valid fact"
        result_ids = [f.id for f in results]
        assert valid_fact.id in result_ids, "Should include the valid fact"
        assert invalidated_fact.id not in result_ids, "Should NOT include invalidated fact"

    finally:
        # Cleanup both facts
        try:
            await graph_engine.delete_nodes([str(valid_fact.id), str(invalidated_fact.id)])
        except Exception as e:
            import logging
            logging.warning(f"Failed to clean up test facts: {e}")


@pytest.mark.asyncio
async def test_update_fact_in_graph_persists_invalidation():
    """Test that _update_fact_in_graph correctly updates invalidation fields."""
    graph_engine = await get_graph_engine()

    # Create a fact
    fact = AtomicFact(
        id=uuid4(),
        subject="Charlie",
        predicate="is_CEO_of",
        object="StartupInc",
        source_chunk_id=uuid4(),
        source_text="Charlie is CEO of StartupInc.",
        fact_type=FactType.FACT,
        temporal_type=TemporalType.STATIC,
        confidence=0.95,
        valid_from=int(datetime.now(timezone.utc).timestamp() * 1000),
        is_open_interval=True,
    )

    try:
        # Add the fact to the graph
        await graph_engine.add_nodes([fact])

        # Now invalidate the fact
        new_fact_id = uuid4()
        invalidation_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

        fact.invalidated_by = new_fact_id
        fact.invalidated_at = invalidation_timestamp
        fact.expired_at = invalidation_timestamp
        fact.valid_until = invalidation_timestamp

        # Update the fact in the graph
        await _update_fact_in_graph(graph_engine=graph_engine, fact=fact)

        # Query back and verify the updates persisted
        results = await _query_existing_facts(
            graph_engine=graph_engine,
            subject="Charlie",
            predicate="is_CEO_of"
        )

        # Should NOT find the fact (it's invalidated now)
        found_fact = next((f for f in results if f.id == fact.id), None)
        assert found_fact is None, (
            "Fact should be excluded from query results after invalidation"
        )

    finally:
        # Cleanup
        try:
            await graph_engine.delete_node(str(fact.id))
        except Exception as e:
            import logging
            logging.warning(f"Failed to clean up test fact {fact.id}: {e}")


@pytest.mark.asyncio
async def test_full_conflict_detection_workflow():
    """Test the complete conflict detection workflow with graph persistence."""
    graph_engine = await get_graph_engine()

    # Create an old fact
    old_fact = AtomicFact(
        id=uuid4(),
        subject="David",
        predicate="works_at",
        object="OldCompany",
        source_chunk_id=uuid4(),
        source_text="David works at OldCompany.",
        fact_type=FactType.FACT,
        temporal_type=TemporalType.STATIC,
        confidence=0.85,
        valid_from=int(datetime.now(timezone.utc).timestamp() * 1000) - 1000000,
        is_open_interval=True,
    )

    # Create a new conflicting fact (same subject/predicate, different object)
    new_fact = AtomicFact(
        id=uuid4(),
        subject="David",
        predicate="works_at",
        object="NewCompany",
        source_chunk_id=uuid4(),
        source_text="David works at NewCompany.",
        fact_type=FactType.FACT,
        temporal_type=TemporalType.STATIC,
        confidence=0.95,  # Higher confidence
        valid_from=int(datetime.now(timezone.utc).timestamp() * 1000),
        is_open_interval=True,
    )

    try:
        # Add the old fact to the graph
        await graph_engine.add_nodes([old_fact])

        # Run conflict detection (should invalidate old_fact)
        result_facts = await detect_and_invalidate_conflicting_facts(
            atomic_facts=[new_fact],
            correlation_id="test_workflow"
        )

        # Verify the new fact is returned
        assert len(result_facts) == 1
        assert result_facts[0].id == new_fact.id

        # Verify the old fact was invalidated in the graph
        results = await _query_existing_facts(
            graph_engine=graph_engine,
            subject="David",
            predicate="works_at"
        )

        # Old fact should be excluded (invalidated)
        old_fact_found = next((f for f in results if f.id == old_fact.id), None)
        assert old_fact_found is None, (
            "Old fact should be invalidated and excluded from query"
        )

    finally:
        # Cleanup both facts
        try:
            await graph_engine.delete_nodes([str(old_fact.id), str(new_fact.id)])
        except Exception as e:
            import logging
            logging.warning(f"Failed to clean up test facts: {e}")


@pytest.mark.asyncio
async def test_query_returns_empty_list_on_no_matches():
    """Test that _query_existing_facts returns empty list when no matches."""
    graph_engine = await get_graph_engine()

    results = await _query_existing_facts(
        graph_engine=graph_engine,
        subject="NonexistentEntity",
        predicate="nonexistent_relation"
    )

    assert results == [], "Should return empty list when no matches found"


@pytest.mark.asyncio
async def test_query_handles_graph_errors_gracefully():
    """Test that _query_existing_facts handles graph errors without crashing."""
    graph_engine = await get_graph_engine()

    # Try to query with potentially problematic values
    results = await _query_existing_facts(
        graph_engine=graph_engine,
        subject="",  # Empty string
        predicate=""
    )

    # Should return empty list, not crash
    assert isinstance(results, list), "Should return a list even on error"
