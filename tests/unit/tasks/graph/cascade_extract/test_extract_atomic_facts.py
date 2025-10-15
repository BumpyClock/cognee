# ABOUTME: Unit tests for atomic fact extraction with mocked LLM responses
# ABOUTME: Tests multi-round extraction, deduplication, and pronoun resolution

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock

from cognee.tasks.graph.cascade_extract.utils.extract_atomic_facts import (
    extract_atomic_statements,
    _format_facts_for_prompt,
)
from cognee.modules.engine.models.AtomicFact import AtomicFact, FactType, TemporalType
from cognee.tasks.graph.cascade_extract.models.extraction_models import (
    AtomicFactExtractionResponse,
)


@pytest.fixture
def mock_chunk_id():
    """Fixture providing a consistent chunk ID."""
    return uuid4()


@pytest.fixture
def sample_text():
    """Fixture providing sample text for extraction."""
    return "John, who works at Google, lives in NYC."


@pytest.fixture
def complex_text():
    """Fixture providing complex multi-event text."""
    return (
        "The CEO announced Q3 results yesterday. "
        "He mentioned that revenue increased by 20% due to strong product sales."
    )


class TestExtractAtomicStatements:
    """Test suite for atomic fact extraction."""

    @pytest.mark.asyncio
    async def test_basic_extraction(self, mock_chunk_id, sample_text):
        """Test basic extraction of atomic facts from simple text."""
        mock_response = AtomicFactExtractionResponse(
            facts=[
                {"subject": "John", "predicate": "works at", "object": "Google"},
                {"subject": "John", "predicate": "lives in", "object": "NYC"},
            ]
        )

        with patch(
            "cognee.tasks.graph.cascade_extract.utils.extract_atomic_facts.LLMGateway.acreate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            facts = await extract_atomic_statements(
                text=sample_text, source_chunk_id=mock_chunk_id, n_rounds=1
            )

        assert len(facts) == 2
        assert facts[0].subject == "John"
        assert facts[0].predicate == "works at"
        assert facts[0].object == "Google"
        assert facts[0].source_chunk_id == mock_chunk_id
        assert facts[0].source_text == sample_text

    @pytest.mark.asyncio
    async def test_empty_text_raises_error(self, mock_chunk_id):
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await extract_atomic_statements(text="", source_chunk_id=mock_chunk_id)

        with pytest.raises(ValueError, match="Text cannot be empty"):
            await extract_atomic_statements(text="   ", source_chunk_id=mock_chunk_id)

    @pytest.mark.asyncio
    async def test_deduplication_across_rounds(self, mock_chunk_id, sample_text):
        """Test that duplicate facts are not extracted in subsequent rounds."""
        # Round 1 returns 2 facts
        round_1_response = AtomicFactExtractionResponse(
            facts=[
                {"subject": "John", "predicate": "works at", "object": "Google"},
                {"subject": "John", "predicate": "lives in", "object": "NYC"},
            ]
        )

        # Round 2 returns 1 duplicate and 1 new fact
        round_2_response = AtomicFactExtractionResponse(
            facts=[
                {"subject": "John", "predicate": "works at", "object": "Google"},  # Duplicate
                {"subject": "John", "predicate": "is named", "object": "John"},  # New
            ]
        )

        mock_gateway = AsyncMock(side_effect=[round_1_response, round_2_response])

        with patch(
            "cognee.tasks.graph.cascade_extract.utils.extract_atomic_facts.LLMGateway.acreate_structured_output",
            mock_gateway,
        ):
            facts = await extract_atomic_statements(
                text=sample_text, source_chunk_id=mock_chunk_id, n_rounds=2
            )

        # Should have 3 unique facts (2 from round 1, 1 new from round 2)
        assert len(facts) == 3
        assert facts[2].subject == "John"
        assert facts[2].predicate == "is named"

    @pytest.mark.asyncio
    async def test_deduplication_case_insensitive(self, mock_chunk_id, sample_text):
        """Test that deduplication is case-insensitive."""
        mock_response = AtomicFactExtractionResponse(
            facts=[
                {"subject": "John", "predicate": "works at", "object": "Google"},
                {"subject": "JOHN", "predicate": "WORKS AT", "object": "GOOGLE"},  # Duplicate
            ]
        )

        with patch(
            "cognee.tasks.graph.cascade_extract.utils.extract_atomic_facts.LLMGateway.acreate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            facts = await extract_atomic_statements(
                text=sample_text, source_chunk_id=mock_chunk_id, n_rounds=1
            )

        # Should only have 1 fact (duplicate filtered)
        assert len(facts) == 1

    @pytest.mark.asyncio
    async def test_existing_facts_excluded(self, mock_chunk_id, sample_text):
        """Test that existing facts are not re-extracted."""
        existing = [
            AtomicFact(
                subject="John",
                predicate="works at",
                object="Google",
                source_chunk_id=mock_chunk_id,
                source_text=sample_text,
                fact_type=FactType.FACT,
                temporal_type=TemporalType.STATIC,
                confidence=0.9,
            )
        ]

        mock_response = AtomicFactExtractionResponse(
            facts=[
                {"subject": "John", "predicate": "works at", "object": "Google"},  # Existing
                {"subject": "John", "predicate": "lives in", "object": "NYC"},  # New
            ]
        )

        with patch(
            "cognee.tasks.graph.cascade_extract.utils.extract_atomic_facts.LLMGateway.acreate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            facts = await extract_atomic_statements(
                text=sample_text,
                source_chunk_id=mock_chunk_id,
                existing_facts=existing,
                n_rounds=1,
            )

        # Should only return newly extracted fact (not existing)
        assert len(facts) == 1
        assert facts[0].predicate == "lives in"

    @pytest.mark.asyncio
    async def test_multi_event_decomposition(self, mock_chunk_id, complex_text):
        """Test extraction from complex multi-event text."""
        mock_response = AtomicFactExtractionResponse(
            facts=[
                {"subject": "CEO", "predicate": "announced", "object": "Q3 results"},
                {
                    "subject": "CEO announced Q3 results",
                    "predicate": "occurred",
                    "object": "yesterday",
                },
                {"subject": "CEO", "predicate": "mentioned", "object": "revenue increased"},
                {"subject": "revenue", "predicate": "increased by", "object": "20%"},
                {"subject": "product sales", "predicate": "was", "object": "strong"},
            ]
        )

        with patch(
            "cognee.tasks.graph.cascade_extract.utils.extract_atomic_facts.LLMGateway.acreate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            facts = await extract_atomic_statements(
                text=complex_text, source_chunk_id=mock_chunk_id, n_rounds=1
            )

        assert len(facts) == 5
        # Verify pronoun resolution happened (CEO not "He")
        subjects = [fact.subject for fact in facts]
        assert "He" not in subjects
        assert "CEO" in subjects

    @pytest.mark.asyncio
    async def test_default_classification_values(self, mock_chunk_id, sample_text):
        """Test that extracted facts have sensible default classification values."""
        mock_response = AtomicFactExtractionResponse(
            facts=[{"subject": "John", "predicate": "works at", "object": "Google"}]
        )

        with patch(
            "cognee.tasks.graph.cascade_extract.utils.extract_atomic_facts.LLMGateway.acreate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            facts = await extract_atomic_statements(
                text=sample_text, source_chunk_id=mock_chunk_id, n_rounds=1
            )

        fact = facts[0]
        assert fact.fact_type == FactType.FACT  # Default
        assert fact.temporal_type == TemporalType.STATIC  # Default
        assert fact.confidence == 0.5  # Neutral before classification
        assert fact.is_open_interval is True  # Assume ongoing
        assert fact.valid_from is not None
        assert fact.extracted_at is not None

    @pytest.mark.asyncio
    async def test_llm_failure_raises_exception(self, mock_chunk_id, sample_text):
        """Test that LLM failures are properly propagated."""
        with patch(
            "cognee.tasks.graph.cascade_extract.utils.extract_atomic_facts.LLMGateway.acreate_structured_output",
            new_callable=AsyncMock,
            side_effect=Exception("LLM API error"),
        ):
            with pytest.raises(Exception, match="Failed to extract atomic facts"):
                await extract_atomic_statements(
                    text=sample_text, source_chunk_id=mock_chunk_id, n_rounds=1
                )

    @pytest.mark.asyncio
    async def test_whitespace_normalization(self, mock_chunk_id):
        """Test that facts with extra whitespace are normalized."""
        mock_response = AtomicFactExtractionResponse(
            facts=[
                {
                    "subject": "  John  ",
                    "predicate": "  works at  ",
                    "object": "  Google  ",
                }
            ]
        )

        with patch(
            "cognee.tasks.graph.cascade_extract.utils.extract_atomic_facts.LLMGateway.acreate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            facts = await extract_atomic_statements(
                text="John works at Google", source_chunk_id=mock_chunk_id, n_rounds=1
            )

        assert facts[0].subject == "John"
        assert facts[0].predicate == "works at"
        assert facts[0].object == "Google"


class TestFormatFactsForPrompt:
    """Test suite for fact formatting utility."""

    def test_format_empty_facts(self):
        """Test formatting empty facts list."""
        result = _format_facts_for_prompt([])
        assert result == "None"

    def test_format_single_fact(self, mock_chunk_id):
        """Test formatting single fact."""
        fact = AtomicFact(
            subject="John",
            predicate="works at",
            object="Google",
            source_chunk_id=mock_chunk_id,
            source_text="test",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.9,
        )
        result = _format_facts_for_prompt([fact])
        assert result == "1. (John, works at, Google)"

    def test_format_multiple_facts(self, mock_chunk_id):
        """Test formatting multiple facts."""
        facts = [
            AtomicFact(
                subject="John",
                predicate="works at",
                object="Google",
                source_chunk_id=mock_chunk_id,
                source_text="test",
                fact_type=FactType.FACT,
                temporal_type=TemporalType.STATIC,
                confidence=0.9,
            ),
            AtomicFact(
                subject="John",
                predicate="lives in",
                object="NYC",
                source_chunk_id=mock_chunk_id,
                source_text="test",
                fact_type=FactType.FACT,
                temporal_type=TemporalType.STATIC,
                confidence=0.9,
            ),
        ]
        result = _format_facts_for_prompt(facts)
        assert "1. (John, works at, Google)" in result
        assert "2. (John, lives in, NYC)" in result
