# ABOUTME: Unit tests for temporal classification of atomic facts with mocked LLM responses
# ABOUTME: Tests classification accuracy, batch processing, and timestamp parsing

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from cognee.tasks.graph.cascade_extract.utils.classify_atomic_facts import (
    classify_atomic_facts_temporally,
    _parse_timestamp,
    _format_facts_for_classification,
)
from cognee.modules.engine.models.AtomicFact import AtomicFact, FactType, TemporalType
from cognee.tasks.graph.cascade_extract.models.extraction_models import (
    TemporalClassificationResponse,
)


@pytest.fixture
def mock_chunk_id():
    """Fixture providing a consistent chunk ID."""
    return uuid4()


@pytest.fixture
def sample_facts(mock_chunk_id):
    """Fixture providing sample facts for classification."""
    return [
        AtomicFact(
            subject="Company revenue",
            predicate="was",
            object="$1M in 2024",
            source_chunk_id=mock_chunk_id,
            source_text="The company's revenue was $1M in 2024.",
            fact_type=FactType.FACT,  # Will be overwritten
            temporal_type=TemporalType.STATIC,  # Will be overwritten
            confidence=0.5,  # Will be overwritten
        ),
        AtomicFact(
            subject="Water",
            predicate="boils at",
            object="100°C",
            source_chunk_id=mock_chunk_id,
            source_text="Water boils at 100°C at sea level.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.5,
        ),
    ]


class TestClassifyAtomicFactsTemporally:
    """Test suite for temporal classification of atomic facts."""

    @pytest.mark.asyncio
    async def test_basic_classification(self, sample_facts):
        """Test basic classification updates fact properties."""
        mock_response = TemporalClassificationResponse(
            classifications=[
                {
                    "fact_index": 0,
                    "fact_type": "FACT",
                    "temporal_type": "STATIC",
                    "confidence": 0.95,
                    "valid_from": "2024-01-01",
                    "valid_until": "2024-12-31",
                    "is_open_interval": False,
                },
                {
                    "fact_index": 1,
                    "fact_type": "FACT",
                    "temporal_type": "ATEMPORAL",
                    "confidence": 1.0,
                    "valid_from": "beginning_of_time",
                    "valid_until": "open",
                    "is_open_interval": True,
                },
            ]
        )

        with patch(
            "cognee.tasks.graph.cascade_extract.utils.classify_atomic_facts.LLMGateway.acreate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await classify_atomic_facts_temporally(sample_facts)

        assert result is sample_facts  # Returns same list
        assert sample_facts[0].fact_type == FactType.FACT
        assert sample_facts[0].temporal_type == TemporalType.STATIC
        assert sample_facts[0].confidence == 0.95
        assert sample_facts[0].is_open_interval is False

        assert sample_facts[1].fact_type == FactType.FACT
        assert sample_facts[1].temporal_type == TemporalType.ATEMPORAL
        assert sample_facts[1].confidence == 1.0
        assert sample_facts[1].is_open_interval is True

    @pytest.mark.asyncio
    async def test_empty_facts_raises_error(self):
        """Test that empty facts list raises ValueError."""
        with pytest.raises(ValueError, match="Facts list cannot be empty"):
            await classify_atomic_facts_temporally([])

    @pytest.mark.asyncio
    async def test_missing_source_text_raises_error(self, mock_chunk_id):
        """Test that facts without source_text raise ValueError."""
        facts = [
            AtomicFact(
                subject="Test",
                predicate="is",
                object="value",
                source_chunk_id=mock_chunk_id,
                source_text="",  # Empty source_text
                fact_type=FactType.FACT,
                temporal_type=TemporalType.STATIC,
                confidence=0.5,
            )
        ]

        with pytest.raises(ValueError, match="missing source_text"):
            await classify_atomic_facts_temporally(facts)

    @pytest.mark.asyncio
    async def test_all_fact_types(self, mock_chunk_id):
        """Test classification of all fact types."""
        facts = [
            AtomicFact(
                subject="Revenue",
                predicate="was",
                object="$1M",
                source_chunk_id=mock_chunk_id,
                source_text="Revenue was $1M.",
                fact_type=FactType.FACT,
                temporal_type=TemporalType.STATIC,
                confidence=0.5,
            ),
            AtomicFact(
                subject="Product",
                predicate="is",
                object="great",
                source_chunk_id=mock_chunk_id,
                source_text="The product is great.",
                fact_type=FactType.OPINION,
                temporal_type=TemporalType.STATIC,
                confidence=0.5,
            ),
            AtomicFact(
                subject="Sales",
                predicate="will increase",
                object="next year",
                source_chunk_id=mock_chunk_id,
                source_text="Sales will increase next year.",
                fact_type=FactType.PREDICTION,
                temporal_type=TemporalType.DYNAMIC,
                confidence=0.5,
            ),
        ]

        mock_response = TemporalClassificationResponse(
            classifications=[
                {
                    "fact_index": 0,
                    "fact_type": "FACT",
                    "temporal_type": "STATIC",
                    "confidence": 0.95,
                    "valid_from": "extraction_time",
                    "is_open_interval": True,
                },
                {
                    "fact_index": 1,
                    "fact_type": "OPINION",
                    "temporal_type": "STATIC",
                    "confidence": 0.8,
                    "valid_from": "statement_time",
                    "is_open_interval": True,
                },
                {
                    "fact_index": 2,
                    "fact_type": "PREDICTION",
                    "temporal_type": "DYNAMIC",
                    "confidence": 0.7,
                    "valid_from": "extraction_time",
                    "valid_until": "end_of_next_year",
                    "is_open_interval": False,
                },
            ]
        )

        with patch(
            "cognee.tasks.graph.cascade_extract.utils.classify_atomic_facts.LLMGateway.acreate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            await classify_atomic_facts_temporally(facts)

        assert facts[0].fact_type == FactType.FACT
        assert facts[1].fact_type == FactType.OPINION
        assert facts[2].fact_type == FactType.PREDICTION

    @pytest.mark.asyncio
    async def test_all_temporal_types(self, mock_chunk_id):
        """Test classification of all temporal types."""
        facts = [
            AtomicFact(
                subject="Water",
                predicate="boils at",
                object="100°C",
                source_chunk_id=mock_chunk_id,
                source_text="Water boils at 100°C.",
                fact_type=FactType.FACT,
                temporal_type=TemporalType.ATEMPORAL,
                confidence=0.5,
            ),
            AtomicFact(
                subject="CEO",
                predicate="is",
                object="John",
                source_chunk_id=mock_chunk_id,
                source_text="The CEO is John.",
                fact_type=FactType.FACT,
                temporal_type=TemporalType.STATIC,
                confidence=0.5,
            ),
            AtomicFact(
                subject="Stock price",
                predicate="is",
                object="$50",
                source_chunk_id=mock_chunk_id,
                source_text="The stock price is $50.",
                fact_type=FactType.FACT,
                temporal_type=TemporalType.DYNAMIC,
                confidence=0.5,
            ),
        ]

        mock_response = TemporalClassificationResponse(
            classifications=[
                {
                    "fact_index": 0,
                    "fact_type": "FACT",
                    "temporal_type": "ATEMPORAL",
                    "confidence": 1.0,
                    "valid_from": "beginning_of_time",
                    "is_open_interval": True,
                },
                {
                    "fact_index": 1,
                    "fact_type": "FACT",
                    "temporal_type": "STATIC",
                    "confidence": 0.9,
                    "valid_from": "extraction_time",
                    "is_open_interval": True,
                },
                {
                    "fact_index": 2,
                    "fact_type": "FACT",
                    "temporal_type": "DYNAMIC",
                    "confidence": 0.85,
                    "valid_from": "extraction_time",
                    "is_open_interval": True,
                },
            ]
        )

        with patch(
            "cognee.tasks.graph.cascade_extract.utils.classify_atomic_facts.LLMGateway.acreate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            await classify_atomic_facts_temporally(facts)

        assert facts[0].temporal_type == TemporalType.ATEMPORAL
        assert facts[1].temporal_type == TemporalType.STATIC
        assert facts[2].temporal_type == TemporalType.DYNAMIC

    @pytest.mark.asyncio
    async def test_batch_processing(self, mock_chunk_id):
        """Test that large fact lists are processed in batches."""
        # Create 25 facts (should be split into 3 batches of 10, 10, 5)
        facts = [
            AtomicFact(
                subject=f"Subject{i}",
                predicate="is",
                object=f"Object{i}",
                source_chunk_id=mock_chunk_id,
                source_text="Test text.",
                fact_type=FactType.FACT,
                temporal_type=TemporalType.STATIC,
                confidence=0.5,
            )
            for i in range(25)
        ]

        # Mock response with classifications for each batch
        def create_batch_response(start_idx, count):
            return TemporalClassificationResponse(
                classifications=[
                    {
                        "fact_index": i,
                        "fact_type": "FACT",
                        "temporal_type": "STATIC",
                        "confidence": 0.9,
                        "valid_from": "extraction_time",
                        "is_open_interval": True,
                    }
                    for i in range(count)
                ]
            )

        batch_responses = [
            create_batch_response(0, 10),
            create_batch_response(0, 10),
            create_batch_response(0, 5),
        ]

        mock_gateway = AsyncMock(side_effect=batch_responses)

        with patch(
            "cognee.tasks.graph.cascade_extract.utils.classify_atomic_facts.LLMGateway.acreate_structured_output",
            mock_gateway,
        ):
            await classify_atomic_facts_temporally(facts)

        # Verify LLM was called 3 times (3 batches)
        assert mock_gateway.call_count == 3

    @pytest.mark.asyncio
    async def test_llm_failure_raises_exception(self, sample_facts):
        """Test that LLM failures are properly propagated."""
        with patch(
            "cognee.tasks.graph.cascade_extract.utils.classify_atomic_facts.LLMGateway.acreate_structured_output",
            new_callable=AsyncMock,
            side_effect=Exception("LLM API error"),
        ):
            with pytest.raises(Exception, match="Failed to classify atomic facts"):
                await classify_atomic_facts_temporally(sample_facts)

    @pytest.mark.asyncio
    async def test_expired_at_remains_none(self, sample_facts):
        """Test that expired_at is not set during classification (only during invalidation)."""
        mock_response = TemporalClassificationResponse(
            classifications=[
                {
                    "fact_index": 0,
                    "fact_type": "FACT",
                    "temporal_type": "STATIC",
                    "confidence": 0.9,
                    "valid_from": "extraction_time",
                    "is_open_interval": True,
                }
            ]
        )

        with patch(
            "cognee.tasks.graph.cascade_extract.utils.classify_atomic_facts.LLMGateway.acreate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            await classify_atomic_facts_temporally([sample_facts[0]])

        assert sample_facts[0].expired_at is None


class TestParseTimestamp:
    """Test suite for timestamp parsing utility."""

    def test_parse_unknown_returns_default(self):
        """Test that 'unknown' returns default value."""
        assert _parse_timestamp("unknown", 1000, default=500) == 500
        assert _parse_timestamp(None, 1000, default=None) is None

    def test_parse_open_returns_none(self):
        """Test that 'open' returns None."""
        assert _parse_timestamp("open", 1000) is None

    def test_parse_beginning_of_time_returns_zero(self):
        """Test that 'beginning_of_time' returns 0."""
        assert _parse_timestamp("beginning_of_time", 1000) == 0

    def test_parse_extraction_time_returns_current(self):
        """Test that 'extraction_time' or 'statement_time' return current timestamp."""
        current = 1640000000000
        assert _parse_timestamp("extraction_time", current) == current
        assert _parse_timestamp("statement_time", current) == current

    def test_parse_integer_string(self):
        """Test parsing integer timestamp strings."""
        assert _parse_timestamp("1640000000000", 1000) == 1640000000000
        assert _parse_timestamp(1640000000000, 1000) == 1640000000000

    def test_parse_iso_date(self):
        """Test parsing ISO date strings."""
        # 2024-01-01 00:00:00 UTC
        expected = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        result = _parse_timestamp("2024-01-01", 1000)
        assert result == expected

    def test_parse_iso_datetime(self):
        """Test parsing ISO datetime strings."""
        # 2024-01-01 12:30:45 UTC
        expected = int(
            datetime(2024, 1, 1, 12, 30, 45, tzinfo=timezone.utc).timestamp() * 1000
        )
        result = _parse_timestamp("2024-01-01T12:30:45", 1000)
        assert result == expected

    def test_parse_relative_next_year(self):
        """Test parsing 'end_of_next_year' expressions."""
        result = _parse_timestamp("end_of_next_year", 1000)
        assert result is not None
        # Verify it's a timestamp for next year's Dec 31
        dt = datetime.fromtimestamp(result / 1000, tz=timezone.utc)
        assert dt.year == datetime.now(timezone.utc).year + 1
        assert dt.month == 12
        assert dt.day == 31

    def test_parse_invalid_returns_default(self):
        """Test that unparseable strings return default."""
        assert _parse_timestamp("invalid_date", 1000, default=500) == 500
        assert _parse_timestamp("not a timestamp", 1000, default=None) is None


class TestFormatFactsForClassification:
    """Test suite for fact formatting for classification."""

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
        result = _format_facts_for_classification([fact])
        assert result == "0. (John, works at, Google)"

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
                subject="Sarah",
                predicate="lives in",
                object="NYC",
                source_chunk_id=mock_chunk_id,
                source_text="test",
                fact_type=FactType.FACT,
                temporal_type=TemporalType.STATIC,
                confidence=0.9,
            ),
        ]
        result = _format_facts_for_classification(facts)
        assert "0. (John, works at, Google)" in result
        assert "1. (Sarah, lives in, NYC)" in result
