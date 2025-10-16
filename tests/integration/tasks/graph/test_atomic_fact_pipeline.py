"""
Integration tests for atomic fact pipeline.

Tests the end-to-end flow of:
1. Document chunking
2. Atomic fact extraction
3. Temporal classification
4. Conflict detection
5. Graph storage
"""

import pytest
from uuid import uuid4

from cognee.modules.chunking.models.DocumentChunk import DocumentChunk
from cognee.modules.data.processing.document_types import Document
from cognee.modules.engine.models import AtomicFact
from cognee.tasks.graph import extract_graph_from_data


@pytest.mark.asyncio
async def test_atomic_fact_extraction_in_pipeline():
    """Test that atomic facts are extracted and added to chunks."""
    # Create a test document
    test_doc = Document(
        id=uuid4(),
        name="test_doc.txt",
        raw_data_location="memory",
        raw_data="Test document",
    )

    # Create test chunks
    chunks = [
        DocumentChunk(
            id=uuid4(),
            text="John works at Google and lives in New York.",
            chunk_size=100,
            chunk_index=0,
            cut_type="paragraph",
            is_part_of=test_doc,
        ),
        DocumentChunk(
            id=uuid4(),
            text="Mary is the CEO of Tesla since 2020.",
            chunk_size=100,
            chunk_index=1,
            cut_type="paragraph",
            is_part_of=test_doc,
        ),
    ]

    # Process chunks through the pipeline
    # Note: This will make real LLM calls if configured
    processed_chunks = await extract_graph_from_data(
        data_chunks=chunks,
        n_rounds=1,  # Use 1 round for faster testing
    )

    # Verify chunks were processed
    assert len(processed_chunks) == 2
    assert processed_chunks[0].id == chunks[0].id
    assert processed_chunks[1].id == chunks[1].id

    # Verify atomic facts were extracted
    # Note: The exact facts depend on LLM output, so we just check structure
    for chunk in processed_chunks:
        if chunk.contains:
            for item in chunk.contains:
                # Check if any items are AtomicFacts
                if isinstance(item, AtomicFact):
                    # Verify AtomicFact has required fields
                    assert item.subject is not None
                    assert item.predicate is not None
                    assert item.object is not None
                    assert item.source_chunk_id == chunk.id
                    assert item.fact_type is not None
                    assert item.temporal_type is not None
                    assert 0.0 <= item.confidence <= 1.0


@pytest.mark.asyncio
async def test_backward_compatibility_without_atomic_facts():
    """Test that pipeline still works for non-temporal processing."""
    # Create a simple chunk
    test_doc = Document(
        id=uuid4(),
        name="simple.txt",
        raw_data_location="memory",
        raw_data="Simple document",
    )

    chunk = DocumentChunk(
        id=uuid4(),
        text="The sky is blue.",
        chunk_size=50,
        chunk_index=0,
        cut_type="paragraph",
        is_part_of=test_doc,
    )

    # Process through pipeline
    processed = await extract_graph_from_data(
        data_chunks=[chunk],
        n_rounds=1,
    )

    # Verify processing completed without errors
    assert len(processed) == 1
    assert processed[0].id == chunk.id


@pytest.mark.asyncio
async def test_empty_chunks_handling():
    """Test that empty chunk list is handled gracefully."""
    processed = await extract_graph_from_data(
        data_chunks=[],
        n_rounds=1,
    )

    assert processed == []


@pytest.mark.asyncio
async def test_chunk_with_no_facts():
    """Test that chunks with no extractable facts are handled correctly."""
    test_doc = Document(
        id=uuid4(),
        name="empty.txt",
        raw_data_location="memory",
        raw_data="Empty",
    )

    chunk = DocumentChunk(
        id=uuid4(),
        text="",  # Empty text
        chunk_size=0,
        chunk_index=0,
        cut_type="paragraph",
        is_part_of=test_doc,
    )

    processed = await extract_graph_from_data(
        data_chunks=[chunk],
        n_rounds=1,
    )

    # Should complete without errors
    assert len(processed) == 1
