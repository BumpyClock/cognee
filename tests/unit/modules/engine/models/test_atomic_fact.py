# ABOUTME: Unit tests for AtomicFact model validating field types, constraints, and business logic
# ABOUTME: Tests cover model instantiation, field validation, enum constraints, and temporal relationships

import pytest
from uuid import uuid4, UUID
from datetime import datetime, timezone
from pydantic import ValidationError

from cognee.modules.engine.models.AtomicFact import (
    AtomicFact,
    FactType,
    TemporalType,
)


class TestAtomicFactModel:
    """Test suite for AtomicFact model validation and instantiation."""

    def test_atomic_fact_creation_with_minimal_fields(self):
        """Test creating an AtomicFact with only required fields."""
        source_chunk_id = uuid4()
        fact = AtomicFact(
            subject="John",
            predicate="works at",
            object="Google",
            source_chunk_id=source_chunk_id,
            source_text="John works at Google.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.95,
        )

        assert fact.subject == "John"
        assert fact.predicate == "works at"
        assert fact.object == "Google"
        assert fact.source_chunk_id == source_chunk_id
        assert fact.source_text == "John works at Google."
        assert fact.fact_type == FactType.FACT
        assert fact.temporal_type == TemporalType.STATIC
        assert fact.confidence == 0.95
        assert fact.is_open_interval is False  # Default value
        assert fact.valid_until is None
        assert fact.expired_at is None
        assert fact.invalidated_by is None
        assert fact.invalidated_at is None
        assert isinstance(fact.id, UUID)
        assert isinstance(fact.extracted_at, int)

    def test_atomic_fact_creation_with_all_fields(self):
        """Test creating an AtomicFact with all fields populated."""
        source_chunk_id = uuid4()
        invalidated_by_id = uuid4()
        valid_from = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        valid_until = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        expired_at = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        invalidated_at = int(datetime(2023, 1, 2, tzinfo=timezone.utc).timestamp() * 1000)

        fact = AtomicFact(
            subject="CEO",
            predicate="is",
            object="John Doe",
            source_chunk_id=source_chunk_id,
            source_text="The CEO is John Doe since 2020.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            is_open_interval=True,
            valid_from=valid_from,
            valid_until=valid_until,
            expired_at=expired_at,
            confidence=0.98,
            invalidated_by=invalidated_by_id,
            invalidated_at=invalidated_at,
        )

        assert fact.is_open_interval is True
        assert fact.valid_from == valid_from
        assert fact.valid_until == valid_until
        assert fact.expired_at == expired_at
        assert fact.invalidated_by == invalidated_by_id
        assert fact.invalidated_at == invalidated_at

    def test_fact_type_enum_values(self):
        """Test all FactType enum values are valid."""
        source_chunk_id = uuid4()

        # Test FACT
        fact1 = AtomicFact(
            subject="Revenue",
            predicate="was",
            object="$1M",
            source_chunk_id=source_chunk_id,
            source_text="Revenue was $1M.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.95,
        )
        assert fact1.fact_type == FactType.FACT

        # Test OPINION
        fact2 = AtomicFact(
            subject="Product",
            predicate="is",
            object="great",
            source_chunk_id=source_chunk_id,
            source_text="The product is great.",
            fact_type=FactType.OPINION,
            temporal_type=TemporalType.STATIC,
            confidence=0.7,
        )
        assert fact2.fact_type == FactType.OPINION

        # Test PREDICTION
        fact3 = AtomicFact(
            subject="Sales",
            predicate="will increase to",
            object="$2M",
            source_chunk_id=source_chunk_id,
            source_text="Sales will increase to $2M.",
            fact_type=FactType.PREDICTION,
            temporal_type=TemporalType.DYNAMIC,
            confidence=0.6,
        )
        assert fact3.fact_type == FactType.PREDICTION

    def test_temporal_type_enum_values(self):
        """Test all TemporalType enum values are valid."""
        source_chunk_id = uuid4()

        # Test ATEMPORAL
        fact1 = AtomicFact(
            subject="Water",
            predicate="boils at",
            object="100°C",
            source_chunk_id=source_chunk_id,
            source_text="Water boils at 100°C.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.ATEMPORAL,
            confidence=1.0,
        )
        assert fact1.temporal_type == TemporalType.ATEMPORAL

        # Test STATIC
        fact2 = AtomicFact(
            subject="CEO",
            predicate="is",
            object="John",
            source_chunk_id=source_chunk_id,
            source_text="CEO is John.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.95,
        )
        assert fact2.temporal_type == TemporalType.STATIC

        # Test DYNAMIC
        fact3 = AtomicFact(
            subject="Stock price",
            predicate="is",
            object="$50",
            source_chunk_id=source_chunk_id,
            source_text="Stock price is $50.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.DYNAMIC,
            confidence=0.9,
        )
        assert fact3.temporal_type == TemporalType.DYNAMIC

    def test_confidence_validation(self):
        """Test confidence score must be between 0 and 1."""
        source_chunk_id = uuid4()

        # Valid confidence values
        for confidence in [0.0, 0.5, 1.0]:
            fact = AtomicFact(
                subject="Test",
                predicate="is",
                object="valid",
                source_chunk_id=source_chunk_id,
                source_text="Test is valid.",
                fact_type=FactType.FACT,
                temporal_type=TemporalType.STATIC,
                confidence=confidence,
            )
            assert fact.confidence == confidence

        # Invalid confidence values should raise ValidationError
        with pytest.raises(ValidationError):
            AtomicFact(
                subject="Test",
                predicate="is",
                object="invalid",
                source_chunk_id=source_chunk_id,
                source_text="Test is invalid.",
                fact_type=FactType.FACT,
                temporal_type=TemporalType.STATIC,
                confidence=1.5,  # Too high
            )

        with pytest.raises(ValidationError):
            AtomicFact(
                subject="Test",
                predicate="is",
                object="invalid",
                source_chunk_id=source_chunk_id,
                source_text="Test is invalid.",
                fact_type=FactType.FACT,
                temporal_type=TemporalType.STATIC,
                confidence=-0.1,  # Too low
            )

    def test_uuid_field_validation(self):
        """Test UUID fields accept valid UUIDs and reject invalid ones."""
        # Valid UUID
        valid_uuid = uuid4()
        fact = AtomicFact(
            subject="Test",
            predicate="is",
            object="valid",
            source_chunk_id=valid_uuid,
            source_text="Test is valid.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.9,
        )
        assert fact.source_chunk_id == valid_uuid

        # Invalid UUID should raise ValidationError
        with pytest.raises(ValidationError):
            AtomicFact(
                subject="Test",
                predicate="is",
                object="invalid",
                source_chunk_id="not-a-uuid",  # Invalid UUID
                source_text="Test is invalid.",
                fact_type=FactType.FACT,
                temporal_type=TemporalType.STATIC,
                confidence=0.9,
            )

    def test_timestamp_fields_are_integers(self):
        """Test that timestamp fields accept integer values (milliseconds since epoch)."""
        source_chunk_id = uuid4()
        now = int(datetime.now(timezone.utc).timestamp() * 1000)

        fact = AtomicFact(
            subject="Test",
            predicate="started at",
            object="timestamp",
            source_chunk_id=source_chunk_id,
            source_text="Test started at timestamp.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.DYNAMIC,
            valid_from=now,
            valid_until=now + 3600000,  # 1 hour later
            expired_at=now + 3600000,
            invalidated_at=now + 3700000,
            confidence=0.95,
        )

        assert isinstance(fact.valid_from, int)
        assert isinstance(fact.valid_until, int)
        assert isinstance(fact.expired_at, int)
        assert isinstance(fact.invalidated_at, int)

    def test_open_interval_semantics(self):
        """Test is_open_interval flag represents ongoing validity."""
        source_chunk_id = uuid4()
        valid_from = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)

        # Open interval: fact is still valid (CEO since 2020, still CEO)
        fact_open = AtomicFact(
            subject="CEO",
            predicate="is",
            object="John",
            source_chunk_id=source_chunk_id,
            source_text="CEO is John since 2020.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            is_open_interval=True,
            valid_from=valid_from,
            confidence=0.95,
        )
        assert fact_open.is_open_interval is True
        assert fact_open.valid_until is None  # No end date
        assert fact_open.expired_at is None  # Not expired

        # Closed interval: fact has a defined end
        valid_until = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        fact_closed = AtomicFact(
            subject="CEO",
            predicate="was",
            object="John",
            source_chunk_id=source_chunk_id,
            source_text="CEO was John from 2020 to 2023.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            is_open_interval=False,
            valid_from=valid_from,
            valid_until=valid_until,
            expired_at=valid_until,
            confidence=0.95,
        )
        assert fact_closed.is_open_interval is False
        assert fact_closed.valid_until == valid_until
        assert fact_closed.expired_at == valid_until

    def test_invalidation_chain(self):
        """Test invalidation metadata correctly links facts."""
        source_chunk_id = uuid4()
        old_fact_id = uuid4()
        new_fact_id = uuid4()
        invalidated_at = int(datetime.now(timezone.utc).timestamp() * 1000)

        # Old fact that was invalidated
        old_fact = AtomicFact(
            id=old_fact_id,
            subject="CEO",
            predicate="is",
            object="John",
            source_chunk_id=source_chunk_id,
            source_text="CEO is John.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.95,
            invalidated_by=new_fact_id,
            invalidated_at=invalidated_at,
        )

        assert old_fact.invalidated_by == new_fact_id
        assert old_fact.invalidated_at == invalidated_at

        # New fact that supersedes the old one
        new_fact = AtomicFact(
            id=new_fact_id,
            subject="CEO",
            predicate="is",
            object="Jane",
            source_chunk_id=source_chunk_id,
            source_text="CEO is now Jane.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.98,
        )

        assert new_fact.invalidated_by is None
        assert new_fact.invalidated_at is None

    def test_default_values(self):
        """Test that default values are correctly set."""
        source_chunk_id = uuid4()

        fact = AtomicFact(
            subject="Test",
            predicate="is",
            object="default",
            source_chunk_id=source_chunk_id,
            source_text="Test is default.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.9,
        )

        # Check defaults
        assert fact.is_open_interval is False
        assert fact.valid_from is not None  # Should have a default timestamp
        assert fact.valid_until is None
        assert fact.expired_at is None
        assert fact.invalidated_by is None
        assert fact.invalidated_at is None
        assert isinstance(fact.extracted_at, int)
        assert isinstance(fact.id, UUID)

    def test_metadata_index_fields(self):
        """Test that AtomicFact has appropriate metadata for indexing."""
        source_chunk_id = uuid4()

        fact = AtomicFact(
            subject="John",
            predicate="works at",
            object="Google",
            source_chunk_id=source_chunk_id,
            source_text="John works at Google.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.95,
        )

        # Verify metadata exists and contains index_fields
        assert fact.metadata is not None
        assert "index_fields" in fact.metadata
        # AtomicFact should index subject, predicate, object for deduplication
        assert "subject" in fact.metadata["index_fields"]
        assert "predicate" in fact.metadata["index_fields"]
        assert "object" in fact.metadata["index_fields"]
