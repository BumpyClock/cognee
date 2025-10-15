# ABOUTME: Pydantic response models for atomic fact extraction and temporal classification
# ABOUTME: Defines structured LLM response schemas for fact extraction workflow

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional


class AtomicFactExtractionResponse(BaseModel):
    """
    Response model for atomic fact extraction from LLM.

    Each fact is a simple triplet structure representing:
    - subject: The entity or concept the fact is about
    - predicate: The relationship or property being described
    - object: The value, target entity, or description

    Example:
        {"subject": "John", "predicate": "works at", "object": "Google"}
    """

    facts: List[Dict[str, str]] = Field(
        description="List of extracted atomic facts as (subject, predicate, object) triplets",
        default_factory=list,
    )

    @field_validator("facts")
    @classmethod
    def validate_fact_structure(cls, facts: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Validate that each fact contains required triplet fields.

        Args:
            facts: List of fact dictionaries to validate

        Returns:
            Validated list of facts

        Raises:
            ValueError: If any fact is missing required fields
        """
        required_fields = {"subject", "predicate", "object"}
        for idx, fact in enumerate(facts):
            missing_fields = required_fields - set(fact.keys())
            if missing_fields:
                raise ValueError(
                    f"Fact at index {idx} missing required fields: {missing_fields}"
                )
            # Ensure all values are strings
            for field in required_fields:
                if not isinstance(fact[field], str):
                    raise ValueError(
                        f"Fact at index {idx}: field '{field}' must be a string, got {type(fact[field])}"
                    )
        return facts


class TemporalClassificationResponse(BaseModel):
    """
    Response model for temporal classification of atomic facts.

    Each classification contains:
    - fact_type: FACT, OPINION, or PREDICTION
    - temporal_type: ATEMPORAL, STATIC, or DYNAMIC
    - confidence: Float between 0.0 and 1.0
    - valid_from: Timestamp when fact became valid (milliseconds since epoch)
    - valid_until: Optional timestamp when fact expires (None for open-ended)
    - is_open_interval: Whether the validity period is open-ended
    - reasoning: Optional explanation for the classification
    """

    classifications: List[Dict[str, Any]] = Field(
        description="List of temporal classifications for atomic facts",
        default_factory=list,
    )

    @field_validator("classifications")
    @classmethod
    def validate_classification_structure(
        cls, classifications: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate that each classification contains required fields with correct types.

        Args:
            classifications: List of classification dictionaries to validate

        Returns:
            Validated list of classifications

        Raises:
            ValueError: If any classification has invalid structure or values
        """
        required_fields = {
            "fact_type",
            "temporal_type",
            "confidence",
            "valid_from",
        }
        optional_fields = {"fact_index", "valid_until", "is_open_interval", "reasoning"}
        valid_fact_types = {"FACT", "OPINION", "PREDICTION"}
        valid_temporal_types = {"ATEMPORAL", "STATIC", "DYNAMIC"}

        for idx, classification in enumerate(classifications):
            # Check required fields exist
            missing_fields = required_fields - set(classification.keys())
            if missing_fields:
                raise ValueError(
                    f"Classification at index {idx} missing required fields: {missing_fields}"
                )

            # Validate fact_type
            if classification["fact_type"] not in valid_fact_types:
                raise ValueError(
                    f"Classification at index {idx}: fact_type must be one of {valid_fact_types}, "
                    f"got '{classification['fact_type']}'"
                )

            # Validate temporal_type
            if classification["temporal_type"] not in valid_temporal_types:
                raise ValueError(
                    f"Classification at index {idx}: temporal_type must be one of {valid_temporal_types}, "
                    f"got '{classification['temporal_type']}'"
                )

            # Validate confidence
            confidence = classification["confidence"]
            if not isinstance(confidence, (int, float)):
                raise ValueError(
                    f"Classification at index {idx}: confidence must be a number, got {type(confidence)}"
                )
            if not 0.0 <= confidence <= 1.0:
                raise ValueError(
                    f"Classification at index {idx}: confidence must be between 0.0 and 1.0, got {confidence}"
                )

            # Validate valid_from (can be string or int - parsed later by classification function)
            valid_from = classification["valid_from"]
            if not isinstance(valid_from, (int, str)):
                raise ValueError(
                    f"Classification at index {idx}: valid_from must be a string or integer, "
                    f"got {type(valid_from)}"
                )

            # Validate optional valid_until (can be string, int, or None - parsed later)
            if "valid_until" in classification:
                valid_until = classification["valid_until"]
                if valid_until is not None and not isinstance(valid_until, (int, str)):
                    raise ValueError(
                        f"Classification at index {idx}: valid_until must be None, string, or integer, "
                        f"got {type(valid_until)}"
                    )

            # Validate is_open_interval if present
            if "is_open_interval" in classification:
                if not isinstance(classification["is_open_interval"], bool):
                    raise ValueError(
                        f"Classification at index {idx}: is_open_interval must be a boolean, "
                        f"got {type(classification['is_open_interval'])}"
                    )

            # Validate no unexpected fields
            all_fields = required_fields | optional_fields
            unexpected_fields = set(classification.keys()) - all_fields
            if unexpected_fields:
                raise ValueError(
                    f"Classification at index {idx} has unexpected fields: {unexpected_fields}"
                )

        return classifications
