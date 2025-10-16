"""
Integration tests for atomic fact extraction.

Tests that extract_graph_from_data always runs cascade extraction with atomic facts.
This test file was updated when atomic facts became the default behavior.
"""

import pytest
from uuid import uuid4

from cognee.modules.chunking.models.DocumentChunk import DocumentChunk
from cognee.modules.data.processing.document_types import Document
from cognee.modules.engine.models import AtomicFact
from cognee.tasks.graph import extract_graph_from_data
from cognee.modules.config import get_temporal_config


@pytest.mark.asyncio
async def test_cascade_extractor_produces_atomic_facts():
    """Test that the v2 extractor always produces atomic facts."""
    # Create test chunks
    test_doc = Document(
        id=uuid4(),
        name="test_doc.txt",
        raw_data_location="memory",
        raw_data="Test document",
        external_metadata=None,
        mime_type="text/plain",
    )

    chunks = [
        DocumentChunk(
            id=uuid4(),
            text="John works at Google and lives in New York.",
            chunk_size=100,
            chunk_index=0,
            cut_type="paragraph",
            word_count=8,
            is_part_of=test_doc,
        )
    ]

    # Call extract_graph_from_data (should always use cascade extraction now)
    result = await extract_graph_from_data(data_chunks=chunks)

    # Verify: Atomic facts should be extracted
    atomic_facts_found = False
    for chunk in result:
        if hasattr(chunk, 'contains') and chunk.contains:
            atomic_facts = [item for item in chunk.contains if isinstance(item, AtomicFact)]
            if len(atomic_facts) > 0:
                atomic_facts_found = True
                # Verify atomic facts have required fields
                for fact in atomic_facts:
                    assert fact.subject, "AtomicFact should have subject"
                    assert fact.predicate, "AtomicFact should have predicate"
                    assert fact.object, "AtomicFact should have object"
                    assert fact.source_chunk_id, "AtomicFact should have source_chunk_id"
                    assert fact.fact_type, "AtomicFact should have fact_type"
                    assert fact.temporal_type, "AtomicFact should have temporal_type"
                    assert 0.0 <= fact.confidence <= 1.0, "Confidence should be between 0 and 1"

    assert atomic_facts_found, (
        "V2 cascade extractor should always produce AtomicFacts"
    )


@pytest.mark.asyncio
async def test_extraction_rounds_configuration():
    """Test that extraction rounds are configurable via temporal config."""
    config = get_temporal_config()

    # Config should have extraction_rounds setting
    assert hasattr(config, 'extraction_rounds'), "Config should have extraction_rounds"
    assert config.extraction_rounds >= 1, "Extraction rounds should be at least 1"
    assert config.extraction_rounds <= 5, "Extraction rounds should be at most 5"


@pytest.mark.asyncio
async def test_empty_chunks_handled_gracefully():
    """Test that empty chunks don't cause errors."""
    # Create test with empty text
    test_doc = Document(
        id=uuid4(),
        name="test_doc.txt",
        raw_data_location="memory",
        raw_data="Test document",
        external_metadata=None,
        mime_type="text/plain",
    )

    chunks = [
        DocumentChunk(
            id=uuid4(),
            text="",  # Empty text
            chunk_size=0,
            chunk_index=0,
            cut_type="paragraph",
            word_count=0,
            is_part_of=test_doc,
        )
    ]

    # Should not raise an error
    result = await extract_graph_from_data(data_chunks=chunks)

    # Result should be a list
    assert isinstance(result, list), "Result should be a list"
    assert len(result) > 0, "Should return at least one chunk"
