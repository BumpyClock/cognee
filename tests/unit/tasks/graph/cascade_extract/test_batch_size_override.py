"""
Unit tests for batch_size parameter in classify_atomic_facts_temporally.

Tests that:
1. batch_size parameter overrides config when provided
2. batch_size=None reads from TemporalConfig
3. Batching logic works correctly for different batch sizes
"""

import os
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from cognee.modules.engine.models.AtomicFact import AtomicFact, FactType, TemporalType
from cognee.tasks.graph.cascade_extract.utils.classify_atomic_facts import (
    classify_atomic_facts_temporally,
)
from cognee.modules.config import get_temporal_config


@pytest.fixture
def sample_facts():
    """Create sample atomic facts for testing."""
    facts = []
    for i in range(25):  # Create 25 facts
        facts.append(
            AtomicFact(
                id=uuid4(),
                subject=f"Subject{i}",
                predicate="works_at",
                object=f"Company{i}",
                source_chunk_id=uuid4(),
                source_text=f"Subject{i} works at Company{i}.",
                fact_type=FactType.FACT,
                temporal_type=TemporalType.STATIC,
                confidence=0.5,
            )
        )
    return facts


@pytest.mark.asyncio
async def test_batch_size_parameter_override(sample_facts):
    """Test that batch_size parameter overrides config."""
    # Mock the _classify_batch function to count calls
    batch_call_count = 0

    async def mock_classify_batch(facts, context):
        nonlocal batch_call_count
        batch_call_count += 1
        # Don't actually classify, just track calls
        return None

    with patch(
        'cognee.tasks.graph.cascade_extract.utils.classify_atomic_facts._classify_batch',
        side_effect=mock_classify_batch
    ):
        # Test with batch_size=5 (should make 5 calls for 25 facts)
        batch_call_count = 0
        await classify_atomic_facts_temporally(sample_facts, batch_size=5)
        assert batch_call_count == 5, f"Expected 5 batches, got {batch_call_count}"

        # Test with batch_size=10 (should make 3 calls for 25 facts)
        batch_call_count = 0
        await classify_atomic_facts_temporally(sample_facts, batch_size=10)
        assert batch_call_count == 3, f"Expected 3 batches, got {batch_call_count}"

        # Test with batch_size=25 (should make 1 call for 25 facts)
        batch_call_count = 0
        await classify_atomic_facts_temporally(sample_facts, batch_size=25)
        assert batch_call_count == 1, f"Expected 1 batch, got {batch_call_count}"

        # Test with batch_size=50 (should make 1 call for 25 facts)
        batch_call_count = 0
        await classify_atomic_facts_temporally(sample_facts, batch_size=50)
        assert batch_call_count == 1, f"Expected 1 batch, got {batch_call_count}"


@pytest.mark.asyncio
async def test_batch_size_none_reads_from_config(sample_facts):
    """Test that batch_size=None reads from TemporalConfig."""
    # Mock the _classify_batch function
    batch_call_count = 0

    async def mock_classify_batch(facts, context):
        nonlocal batch_call_count
        batch_call_count += 1
        return None

    # Set config batch size to 5
    with patch.dict(os.environ, {"ATOMIC_CLASSIFICATION_BATCH_SIZE": "5"}):
        config = get_temporal_config()
        assert config.classification_batch_size == 5

        with patch(
            'cognee.tasks.graph.cascade_extract.utils.classify_atomic_facts._classify_batch',
            side_effect=mock_classify_batch
        ):
            # Call with batch_size=None (should use config value of 5)
            batch_call_count = 0
            await classify_atomic_facts_temporally(sample_facts, batch_size=None)
            assert batch_call_count == 5, (
                f"Expected 5 batches (from config), got {batch_call_count}"
            )


@pytest.mark.asyncio
async def test_batch_size_default_fallback(sample_facts):
    """Test that default batch size is 10 when no config or parameter."""
    # Mock the _classify_batch function
    batch_call_count = 0

    async def mock_classify_batch(facts, context):
        nonlocal batch_call_count
        batch_call_count += 1
        return None

    # Clear environment variable to test default
    with patch.dict(os.environ, {}, clear=True):
        config = get_temporal_config()
        assert config.classification_batch_size == 10, "Default should be 10"

        with patch(
            'cognee.tasks.graph.cascade_extract.utils.classify_atomic_facts._classify_batch',
            side_effect=mock_classify_batch
        ):
            # Call with batch_size=None (should use default of 10)
            batch_call_count = 0
            await classify_atomic_facts_temporally(sample_facts, batch_size=None)
            assert batch_call_count == 3, (
                f"Expected 3 batches (25 facts / 10 batch size), got {batch_call_count}"
            )


@pytest.mark.asyncio
async def test_empty_facts_raises_error():
    """Test that empty facts list raises ValueError."""
    with pytest.raises(ValueError, match="Facts list cannot be empty"):
        await classify_atomic_facts_temporally([], batch_size=10)


@pytest.mark.asyncio
async def test_facts_without_source_text_raises_error():
    """Test that facts without source_text raise ValueError.

    Note: Pydantic validates source_text at model instantiation,
    so we test the validation logic by creating a fact with empty source_text.
    """
    facts = [
        AtomicFact(
            id=uuid4(),
            subject="Alice",
            predicate="works_at",
            object="Google",
            source_chunk_id=uuid4(),
            source_text="",  # Empty source_text!
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.5,
        )
    ]

    with pytest.raises(ValueError, match="missing source_text field"):
        await classify_atomic_facts_temporally(facts, batch_size=10)
