# ABOUTME: Unit tests for atomic fact extraction and classification response models
# ABOUTME: Validates Pydantic model schemas and field validation logic

import pytest
from cognee.tasks.graph.cascade_extract.models.extraction_models import (
    AtomicFactExtractionResponse,
    TemporalClassificationResponse,
)


class TestAtomicFactExtractionResponse:
    """Test suite for AtomicFactExtractionResponse model."""

    def test_valid_facts(self):
        """Test creation with valid fact triplets."""
        facts = [
            {"subject": "John", "predicate": "works at", "object": "Google"},
            {"subject": "Sarah", "predicate": "lives in", "object": "NYC"},
        ]
        response = AtomicFactExtractionResponse(facts=facts)
        assert len(response.facts) == 2
        assert response.facts[0]["subject"] == "John"

    def test_empty_facts_list(self):
        """Test creation with empty facts list."""
        response = AtomicFactExtractionResponse(facts=[])
        assert response.facts == []

    def test_default_empty_facts(self):
        """Test default initialization creates empty list."""
        response = AtomicFactExtractionResponse()
        assert response.facts == []

    def test_missing_subject_field(self):
        """Test validation fails when subject field is missing."""
        facts = [{"predicate": "works at", "object": "Google"}]
        with pytest.raises(ValueError, match="missing required fields.*subject"):
            AtomicFactExtractionResponse(facts=facts)

    def test_missing_predicate_field(self):
        """Test validation fails when predicate field is missing."""
        facts = [{"subject": "John", "object": "Google"}]
        with pytest.raises(ValueError, match="missing required fields.*predicate"):
            AtomicFactExtractionResponse(facts=facts)

    def test_missing_object_field(self):
        """Test validation fails when object field is missing."""
        facts = [{"subject": "John", "predicate": "works at"}]
        with pytest.raises(ValueError, match="missing required fields.*object"):
            AtomicFactExtractionResponse(facts=facts)

    def test_non_string_field_value(self):
        """Test validation fails when field value is not a string."""
        from pydantic import ValidationError
        facts = [{"subject": 123, "predicate": "works at", "object": "Google"}]
        with pytest.raises(ValidationError, match="Input should be a valid string"):
            AtomicFactExtractionResponse(facts=facts)

    def test_multiple_facts_with_one_invalid(self):
        """Test validation fails if any fact in list is invalid."""
        facts = [
            {"subject": "John", "predicate": "works at", "object": "Google"},
            {"subject": "Sarah", "predicate": "lives in"},  # Missing object
        ]
        with pytest.raises(ValueError, match="Fact at index 1.*missing required fields"):
            AtomicFactExtractionResponse(facts=facts)

    def test_extra_fields_allowed(self):
        """Test that extra fields beyond required triplet are allowed."""
        facts = [
            {
                "subject": "John",
                "predicate": "works at",
                "object": "Google",
                "extra_field": "some value",
            }
        ]
        response = AtomicFactExtractionResponse(facts=facts)
        assert len(response.facts) == 1
        assert "extra_field" in response.facts[0]


class TestTemporalClassificationResponse:
    """Test suite for TemporalClassificationResponse model."""

    def test_valid_classification(self):
        """Test creation with valid classification."""
        classifications = [
            {
                "fact_type": "FACT",
                "temporal_type": "STATIC",
                "confidence": 0.95,
                "valid_from": 1640000000000,
                "valid_until": 1650000000000,
                "is_open_interval": False,
            }
        ]
        response = TemporalClassificationResponse(classifications=classifications)
        assert len(response.classifications) == 1
        assert response.classifications[0]["fact_type"] == "FACT"

    def test_classification_without_optional_fields(self):
        """Test classification with only required fields."""
        classifications = [
            {
                "fact_type": "OPINION",
                "temporal_type": "ATEMPORAL",
                "confidence": 0.8,
                "valid_from": 1640000000000,
            }
        ]
        response = TemporalClassificationResponse(classifications=classifications)
        assert len(response.classifications) == 1

    def test_empty_classifications_list(self):
        """Test creation with empty classifications list."""
        response = TemporalClassificationResponse(classifications=[])
        assert response.classifications == []

    def test_default_empty_classifications(self):
        """Test default initialization creates empty list."""
        response = TemporalClassificationResponse()
        assert response.classifications == []

    def test_missing_fact_type(self):
        """Test validation fails when fact_type is missing."""
        classifications = [
            {
                "temporal_type": "STATIC",
                "confidence": 0.9,
                "valid_from": 1640000000000,
            }
        ]
        with pytest.raises(ValueError, match="missing required fields.*fact_type"):
            TemporalClassificationResponse(classifications=classifications)

    def test_invalid_fact_type(self):
        """Test validation fails for invalid fact_type value."""
        classifications = [
            {
                "fact_type": "INVALID",
                "temporal_type": "STATIC",
                "confidence": 0.9,
                "valid_from": 1640000000000,
            }
        ]
        with pytest.raises(ValueError, match="fact_type must be one of"):
            TemporalClassificationResponse(classifications=classifications)

    def test_invalid_temporal_type(self):
        """Test validation fails for invalid temporal_type value."""
        classifications = [
            {
                "fact_type": "FACT",
                "temporal_type": "INVALID",
                "confidence": 0.9,
                "valid_from": 1640000000000,
            }
        ]
        with pytest.raises(ValueError, match="temporal_type must be one of"):
            TemporalClassificationResponse(classifications=classifications)

    def test_confidence_below_range(self):
        """Test validation fails when confidence is below 0.0."""
        classifications = [
            {
                "fact_type": "FACT",
                "temporal_type": "STATIC",
                "confidence": -0.1,
                "valid_from": 1640000000000,
            }
        ]
        with pytest.raises(ValueError, match="confidence must be between 0.0 and 1.0"):
            TemporalClassificationResponse(classifications=classifications)

    def test_confidence_above_range(self):
        """Test validation fails when confidence is above 1.0."""
        classifications = [
            {
                "fact_type": "FACT",
                "temporal_type": "STATIC",
                "confidence": 1.5,
                "valid_from": 1640000000000,
            }
        ]
        with pytest.raises(ValueError, match="confidence must be between 0.0 and 1.0"):
            TemporalClassificationResponse(classifications=classifications)

    def test_non_numeric_confidence(self):
        """Test validation fails when confidence is not a number."""
        classifications = [
            {
                "fact_type": "FACT",
                "temporal_type": "STATIC",
                "confidence": "high",
                "valid_from": 1640000000000,
            }
        ]
        with pytest.raises(ValueError, match="confidence must be a number"):
            TemporalClassificationResponse(classifications=classifications)

    def test_valid_from_accepts_string_or_int(self):
        """Test that valid_from accepts both string and integer values."""
        # Test with string
        classifications_str = [
            {
                "fact_type": "FACT",
                "temporal_type": "STATIC",
                "confidence": 0.9,
                "valid_from": "2024-01-01",
            }
        ]
        response = TemporalClassificationResponse(classifications=classifications_str)
        assert response.classifications[0]["valid_from"] == "2024-01-01"

        # Test with integer
        classifications_int = [
            {
                "fact_type": "FACT",
                "temporal_type": "STATIC",
                "confidence": 0.9,
                "valid_from": 1640000000000,
            }
        ]
        response = TemporalClassificationResponse(classifications=classifications_int)
        assert response.classifications[0]["valid_from"] == 1640000000000

    def test_valid_until_accepts_string_int_or_none(self):
        """Test that valid_until accepts string, integer, or None values."""
        # Test with string
        classifications_str = [
            {
                "fact_type": "FACT",
                "temporal_type": "STATIC",
                "confidence": 0.9,
                "valid_from": 1640000000000,
                "valid_until": "2025-01-01",
            }
        ]
        response = TemporalClassificationResponse(classifications=classifications_str)
        assert response.classifications[0]["valid_until"] == "2025-01-01"

        # Test with integer
        classifications_int = [
            {
                "fact_type": "FACT",
                "temporal_type": "STATIC",
                "confidence": 0.9,
                "valid_from": 1640000000000,
                "valid_until": 1650000000000,
            }
        ]
        response = TemporalClassificationResponse(classifications=classifications_int)
        assert response.classifications[0]["valid_until"] == 1650000000000

        # Test with None
        classifications_none = [
            {
                "fact_type": "FACT",
                "temporal_type": "STATIC",
                "confidence": 0.9,
                "valid_from": 1640000000000,
                "valid_until": None,
            }
        ]
        response = TemporalClassificationResponse(classifications=classifications_none)
        assert response.classifications[0]["valid_until"] is None

    def test_timestamp_ordering_not_validated_in_model(self):
        """Test that timestamp ordering is NOT validated in Pydantic model (parsed later)."""
        # This is acceptable at model level - parsing handles temporal validation
        classifications = [
            {
                "fact_type": "FACT",
                "temporal_type": "STATIC",
                "confidence": 0.9,
                "valid_from": "2024-01-01",
                "valid_until": "2023-01-01",  # Earlier than valid_from
            }
        ]
        # Should not raise - ordering validation happens during parsing
        response = TemporalClassificationResponse(classifications=classifications)
        assert len(response.classifications) == 1

    def test_valid_until_none_allowed(self):
        """Test that valid_until can be None for open-ended validity."""
        classifications = [
            {
                "fact_type": "FACT",
                "temporal_type": "STATIC",
                "confidence": 0.9,
                "valid_from": 1640000000000,
                "valid_until": None,
            }
        ]
        response = TemporalClassificationResponse(classifications=classifications)
        assert response.classifications[0]["valid_until"] is None

    def test_non_boolean_is_open_interval(self):
        """Test validation fails when is_open_interval is not boolean."""
        classifications = [
            {
                "fact_type": "FACT",
                "temporal_type": "STATIC",
                "confidence": 0.9,
                "valid_from": 1640000000000,
                "is_open_interval": "yes",
            }
        ]
        with pytest.raises(ValueError, match="is_open_interval must be a boolean"):
            TemporalClassificationResponse(classifications=classifications)

    def test_unexpected_fields_rejected(self):
        """Test validation fails when unexpected fields are present."""
        classifications = [
            {
                "fact_type": "FACT",
                "temporal_type": "STATIC",
                "confidence": 0.9,
                "valid_from": 1640000000000,
                "unexpected_field": "value",
            }
        ]
        with pytest.raises(ValueError, match="unexpected fields"):
            TemporalClassificationResponse(classifications=classifications)

    def test_reasoning_field_allowed(self):
        """Test that optional reasoning field is allowed."""
        classifications = [
            {
                "fact_type": "PREDICTION",
                "temporal_type": "DYNAMIC",
                "confidence": 0.7,
                "valid_from": 1640000000000,
                "reasoning": "Based on historical trends",
            }
        ]
        response = TemporalClassificationResponse(classifications=classifications)
        assert response.classifications[0]["reasoning"] == "Based on historical trends"

    def test_all_fact_types(self):
        """Test all valid fact_type values."""
        for fact_type in ["FACT", "OPINION", "PREDICTION"]:
            classifications = [
                {
                    "fact_type": fact_type,
                    "temporal_type": "STATIC",
                    "confidence": 0.9,
                    "valid_from": 1640000000000,
                }
            ]
            response = TemporalClassificationResponse(classifications=classifications)
            assert response.classifications[0]["fact_type"] == fact_type

    def test_all_temporal_types(self):
        """Test all valid temporal_type values."""
        for temporal_type in ["ATEMPORAL", "STATIC", "DYNAMIC"]:
            classifications = [
                {
                    "fact_type": "FACT",
                    "temporal_type": temporal_type,
                    "confidence": 0.9,
                    "valid_from": 1640000000000,
                }
            ]
            response = TemporalClassificationResponse(classifications=classifications)
            assert response.classifications[0]["temporal_type"] == temporal_type
