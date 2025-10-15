# ABOUTME: Unit tests for atomic fact conflict detection logic.
# ABOUTME: Tests STATIC replacement, DYNAMIC coexistence, confidence overrides, and duplicate detection.

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from cognee.modules.engine.models.AtomicFact import AtomicFact, FactType, TemporalType
from cognee.tasks.storage.manage_atomic_fact_conflicts import find_conflicting_facts


def create_test_fact(
    subject: str,
    predicate: str,
    object_: str,
    fact_type: FactType = FactType.FACT,
    temporal_type: TemporalType = TemporalType.STATIC,
    confidence: float = 0.9,
    source_chunk_id: str = None,
    valid_from: int = None,
    valid_until: int = None,
    is_open_interval: bool = False
) -> AtomicFact:
    """Helper to create AtomicFact instances for testing."""
    chunk_id = uuid4() if source_chunk_id is None else source_chunk_id
    vf = valid_from if valid_from is not None else int(datetime.now(timezone.utc).timestamp() * 1000)

    return AtomicFact(
        subject=subject,
        predicate=predicate,
        object=object_,
        fact_type=fact_type,
        temporal_type=temporal_type,
        confidence=confidence,
        source_chunk_id=chunk_id,
        source_text=f"{subject} {predicate} {object_}",
        valid_from=vf,
        valid_until=valid_until,
        is_open_interval=is_open_interval
    )


@pytest.mark.asyncio
async def test_static_fact_replaces_older_static_fact():
    """
    Test that a new STATIC fact with same (subject, predicate) invalidates older STATIC fact.

    Example: "CEO is John" (2020) → "CEO is Jane" (2024) should invalidate the first fact.
    """
    old_fact = create_test_fact(
        subject="Company X",
        predicate="CEO is",
        object_="John Smith",
        temporal_type=TemporalType.STATIC,
        valid_from=int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    )

    new_fact = create_test_fact(
        subject="Company X",
        predicate="CEO is",
        object_="Jane Doe",
        temporal_type=TemporalType.STATIC,
        valid_from=int(datetime(2024, 3, 15, tzinfo=timezone.utc).timestamp() * 1000)
    )

    conflicts = await find_conflicting_facts(new_fact, [old_fact])

    assert len(conflicts) == 1
    assert conflicts[0].id == old_fact.id
    assert conflicts[0].object == "John Smith"


@pytest.mark.asyncio
async def test_dynamic_facts_coexist_with_time_boundaries():
    """
    Test that DYNAMIC facts with different time boundaries coexist without conflicts.

    Example: Stock price at 09:00 and 09:15 should both be stored.
    """
    fact1 = create_test_fact(
        subject="AAPL",
        predicate="stock price is",
        object_="$150",
        temporal_type=TemporalType.DYNAMIC,
        valid_from=int(datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc).timestamp() * 1000),
        valid_until=int(datetime(2024, 1, 1, 9, 15, tzinfo=timezone.utc).timestamp() * 1000)
    )

    fact2 = create_test_fact(
        subject="AAPL",
        predicate="stock price is",
        object_="$152",
        temporal_type=TemporalType.DYNAMIC,
        valid_from=int(datetime(2024, 1, 1, 9, 15, tzinfo=timezone.utc).timestamp() * 1000),
        valid_until=int(datetime(2024, 1, 1, 9, 30, tzinfo=timezone.utc).timestamp() * 1000)
    )

    conflicts = await find_conflicting_facts(fact2, [fact1])

    # DYNAMIC facts should coexist with time boundaries
    assert len(conflicts) == 0


@pytest.mark.asyncio
async def test_same_source_duplicate_no_conflict():
    """
    Test that facts from the same source chunk are not marked as conflicts (idempotency).

    Example: Re-processing same chunk should not invalidate existing facts.
    """
    chunk_id = uuid4()

    fact1 = create_test_fact(
        subject="John",
        predicate="works at",
        object_="Google",
        source_chunk_id=chunk_id
    )

    fact2 = create_test_fact(
        subject="John",
        predicate="works at",
        object_="Google",
        source_chunk_id=chunk_id
    )

    conflicts = await find_conflicting_facts(fact2, [fact1])

    # Same source duplicate should not be a conflict
    assert len(conflicts) == 0


@pytest.mark.asyncio
async def test_higher_confidence_overrides_lower_confidence():
    """
    Test that a fact with higher confidence can override a lower confidence fact.

    Example: If we extract "CEO is John" with 95% confidence, it should override 70% confidence.
    """
    low_confidence = create_test_fact(
        subject="Company Y",
        predicate="CEO is",
        object_="Alice",
        temporal_type=TemporalType.STATIC,
        confidence=0.7
    )

    high_confidence = create_test_fact(
        subject="Company Y",
        predicate="CEO is",
        object_="Bob",
        temporal_type=TemporalType.STATIC,
        confidence=0.95
    )

    conflicts = await find_conflicting_facts(high_confidence, [low_confidence])

    assert len(conflicts) == 1
    assert conflicts[0].confidence == 0.7


@pytest.mark.asyncio
async def test_lower_confidence_does_not_override_higher():
    """
    Test that a lower confidence fact does NOT override a higher confidence fact.
    """
    high_confidence = create_test_fact(
        subject="Company Y",
        predicate="CEO is",
        object_="Alice",
        temporal_type=TemporalType.STATIC,
        confidence=0.95
    )

    low_confidence = create_test_fact(
        subject="Company Y",
        predicate="CEO is",
        object_="Bob",
        temporal_type=TemporalType.STATIC,
        confidence=0.7
    )

    conflicts = await find_conflicting_facts(low_confidence, [high_confidence])

    # Lower confidence should not override higher
    assert len(conflicts) == 0


@pytest.mark.asyncio
async def test_different_predicates_no_conflict():
    """
    Test that facts with different predicates don't conflict even with same subject.

    Example: "John works at Google" and "John lives in NYC" should coexist.
    """
    fact1 = create_test_fact(
        subject="John",
        predicate="works at",
        object_="Google"
    )

    fact2 = create_test_fact(
        subject="John",
        predicate="lives in",
        object_="NYC"
    )

    conflicts = await find_conflicting_facts(fact2, [fact1])

    assert len(conflicts) == 0


@pytest.mark.asyncio
async def test_multiple_conflicts_detected():
    """
    Test that multiple conflicting facts are all detected.
    """
    existing_facts = [
        create_test_fact("Company", "CEO is", "Person A", confidence=0.8),
        create_test_fact("Company", "CEO is", "Person B", confidence=0.75),
        create_test_fact("Other Company", "CEO is", "Person C"),  # Different subject, no conflict
    ]

    new_fact = create_test_fact("Company", "CEO is", "Person D", confidence=0.9)

    conflicts = await find_conflicting_facts(new_fact, existing_facts)

    assert len(conflicts) == 2
    # Should detect both Person A and Person B as conflicts
    conflict_objects = {c.object for c in conflicts}
    assert "Person A" in conflict_objects
    assert "Person B" in conflict_objects
    assert "Person C" not in conflict_objects


@pytest.mark.asyncio
async def test_atemporal_facts_do_not_conflict():
    """
    Test that ATEMPORAL facts (timeless truths) don't conflict even with same subject/predicate.

    Example: "Water boils at 100°C" is always true, multiple extractions should coexist.
    """
    fact1 = create_test_fact(
        subject="Water",
        predicate="boils at",
        object_="100°C",
        temporal_type=TemporalType.ATEMPORAL
    )

    fact2 = create_test_fact(
        subject="Water",
        predicate="boils at",
        object_="100°C",
        temporal_type=TemporalType.ATEMPORAL
    )

    conflicts = await find_conflicting_facts(fact2, [fact1])

    # ATEMPORAL facts should not conflict if they state the same truth
    assert len(conflicts) == 0


@pytest.mark.asyncio
async def test_empty_existing_facts_no_conflicts():
    """
    Test that when there are no existing facts, no conflicts are found.
    """
    new_fact = create_test_fact("Company", "CEO is", "Alice")

    conflicts = await find_conflicting_facts(new_fact, [])

    assert len(conflicts) == 0


@pytest.mark.asyncio
async def test_opinion_vs_fact_conflict():
    """
    Test that OPINIONs can coexist even with same subject/predicate.

    Example: "Product is great" (opinion) can coexist with other opinions or facts.
    """
    opinion1 = create_test_fact(
        subject="Product X",
        predicate="quality is",
        object_="great",
        fact_type=FactType.OPINION
    )

    opinion2 = create_test_fact(
        subject="Product X",
        predicate="quality is",
        object_="excellent",
        fact_type=FactType.OPINION
    )

    conflicts = await find_conflicting_facts(opinion2, [opinion1])

    # Opinions can coexist
    assert len(conflicts) == 0
