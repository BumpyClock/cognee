# ABOUTME: Unit tests for atomic fact invalidation workflow.
# ABOUTME: Tests timestamp updates, invalidation metadata, and edge creation logic.

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from cognee.modules.engine.models.AtomicFact import AtomicFact, FactType, TemporalType
from cognee.tasks.storage.invalidate_facts import invalidate_fact, prepare_invalidation_updates


def create_test_fact(
    subject: str = "Test",
    predicate: str = "is",
    object_: str = "value",
    fact_id: str = None
) -> AtomicFact:
    """Helper to create AtomicFact instances for testing."""
    return AtomicFact(
        id=fact_id or uuid4(),
        subject=subject,
        predicate=predicate,
        object=object_,
        fact_type=FactType.FACT,
        temporal_type=TemporalType.STATIC,
        confidence=0.9,
        source_chunk_id=uuid4(),
        source_text=f"{subject} {predicate} {object_}"
    )


@pytest.mark.asyncio
async def test_prepare_invalidation_updates_sets_all_fields():
    """
    Test that prepare_invalidation_updates correctly sets all invalidation fields.
    """
    old_fact = create_test_fact()
    new_fact_id = uuid4()
    reason = "superseded_by_newer_fact"

    # Get the timestamp before calling the function
    before_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

    updates = await prepare_invalidation_updates(
        fact=old_fact,
        new_fact_id=new_fact_id,
        reason=reason
    )

    after_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

    # Verify all required fields are in updates
    assert "invalidated_by" in updates
    assert "invalidated_at" in updates
    assert "expired_at" in updates
    assert "valid_until" in updates

    # Verify values
    assert updates["invalidated_by"] == new_fact_id
    assert before_timestamp <= updates["invalidated_at"] <= after_timestamp
    assert before_timestamp <= updates["expired_at"] <= after_timestamp

    # valid_until should be set to current timestamp if not already set
    if old_fact.valid_until is None:
        assert before_timestamp <= updates["valid_until"] <= after_timestamp


@pytest.mark.asyncio
async def test_prepare_invalidation_preserves_existing_valid_until():
    """
    Test that if valid_until is already set, it's preserved.
    """
    existing_valid_until = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    old_fact = create_test_fact()
    old_fact.valid_until = existing_valid_until

    new_fact_id = uuid4()

    updates = await prepare_invalidation_updates(
        fact=old_fact,
        new_fact_id=new_fact_id,
        reason="superseded"
    )

    # Should preserve existing valid_until
    assert updates["valid_until"] == existing_valid_until


@pytest.mark.asyncio
async def test_invalidate_fact_returns_updates():
    """
    Test that invalidate_fact returns the correct update dictionary.
    """
    fact_id = uuid4()
    new_fact_id = uuid4()
    reason = "confidence_override"

    updates = await invalidate_fact(
        fact_id=fact_id,
        new_fact_id=new_fact_id,
        reason=reason
    )

    # Should return a dict with all invalidation fields
    assert isinstance(updates, dict)
    assert "invalidated_by" in updates
    assert "invalidated_at" in updates
    assert "expired_at" in updates
    assert "valid_until" in updates

    assert updates["invalidated_by"] == new_fact_id


@pytest.mark.asyncio
async def test_invalidate_fact_with_default_reason():
    """
    Test that invalidate_fact uses default reason if not provided.
    """
    fact_id = uuid4()
    new_fact_id = uuid4()

    # Call without explicit reason (should use default "superseded")
    updates = await invalidate_fact(
        fact_id=fact_id,
        new_fact_id=new_fact_id
    )

    assert isinstance(updates, dict)
    assert updates["invalidated_by"] == new_fact_id


@pytest.mark.asyncio
async def test_invalidation_timestamps_are_consistent():
    """
    Test that all invalidation timestamps are the same (or very close).
    """
    old_fact = create_test_fact()
    new_fact_id = uuid4()

    updates = await prepare_invalidation_updates(
        fact=old_fact,
        new_fact_id=new_fact_id,
        reason="test"
    )

    # All timestamps should be within 1 second of each other
    timestamps = [
        updates["invalidated_at"],
        updates["expired_at"],
    ]

    if old_fact.valid_until is None:
        timestamps.append(updates["valid_until"])

    max_diff = max(timestamps) - min(timestamps)
    assert max_diff < 1000  # Less than 1 second difference


@pytest.mark.asyncio
async def test_invalidate_multiple_facts_sequentially():
    """
    Test that we can invalidate multiple facts in sequence.
    """
    fact1_id = uuid4()
    fact2_id = uuid4()
    new_fact_id = uuid4()

    updates1 = await invalidate_fact(fact1_id, new_fact_id, "superseded")
    updates2 = await invalidate_fact(fact2_id, new_fact_id, "superseded")

    # Both should succeed and return valid updates
    assert updates1["invalidated_by"] == new_fact_id
    assert updates2["invalidated_by"] == new_fact_id

    # Timestamps should be close (within 1 second) if executed sequentially
    time_diff = abs(updates1["invalidated_at"] - updates2["invalidated_at"])
    assert time_diff <= 1000  # Within 1 second
