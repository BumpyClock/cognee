# ABOUTME: AtomicFact model representing temporally precise subject-predicate-object triplets
# ABOUTME: Supports fact classification, temporal tracking, and invalidation chains for knowledge graphs

from enum import Enum
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from pydantic import Field, field_validator

from cognee.infrastructure.engine import DataPoint


class FactType(str, Enum):
    """
    Classification of fact certainty levels.

    FACT: Objectively verifiable statement (e.g., "Revenue was $1M")
    OPINION: Subjective statement or judgment (e.g., "Product is great")
    PREDICTION: Future-oriented claim (e.g., "Sales will increase")
    """
    FACT = "FACT"
    OPINION = "OPINION"
    PREDICTION = "PREDICTION"


class TemporalType(str, Enum):
    """
    Classification of fact temporal stability.

    ATEMPORAL: Timeless truth (e.g., "Water boils at 100°C")
    STATIC: Changes infrequently (e.g., "CEO is John")
    DYNAMIC: Changes frequently (e.g., "Stock price is $50")
    """
    ATEMPORAL = "ATEMPORAL"
    STATIC = "STATIC"
    DYNAMIC = "DYNAMIC"


class AtomicFact(DataPoint):
    """
    Represents a temporally-aware atomic fact as a subject-predicate-object triplet.

    AtomicFacts enable long-term AI agents to reason about changes over time by tracking:
    - What the fact states (subject, predicate, object)
    - When it was true (valid_from, valid_until, expired_at)
    - How certain we are (confidence, fact_type)
    - Whether it was superseded (invalidated_by, invalidated_at)

    Key temporal semantics:
    - is_open_interval: True if fact has ongoing validity (e.g., "CEO is John" since 2020, still valid)
    - valid_until: Natural validity boundary from classification (when fact is expected to end)
    - expired_at: Actual timestamp when fact ceased being valid (may differ from valid_until)
    - invalidated_at: When this fact was superseded by another fact

    Example:
        fact1 = AtomicFact(
            subject="CEO", predicate="is", object="John",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            is_open_interval=True,
            valid_from=1609459200000,  # 2021-01-01
            confidence=0.95
        )

        # Later, when John is replaced:
        fact1.invalidated_by = fact2.id
        fact1.invalidated_at = 1672531200000  # 2023-01-01
        fact1.expired_at = 1672531200000
    """

    # Core triplet
    subject: str = Field(..., description="Subject of the fact (entity or concept)")
    predicate: str = Field(..., description="Relationship or action connecting subject to object")
    object: str = Field(..., description="Object of the fact (entity, value, or concept)")

    # Source tracking
    source_chunk_id: UUID = Field(..., description="UUID of the DocumentChunk this fact was extracted from")
    source_text: str = Field(..., description="Original text passage containing this fact")

    # Fact classification
    fact_type: FactType = Field(..., description="Classification: FACT, OPINION, or PREDICTION")
    temporal_type: TemporalType = Field(..., description="Temporal stability: ATEMPORAL, STATIC, or DYNAMIC")

    # Temporal tracking
    is_open_interval: bool = Field(
        default=False,
        description="True if fact has ongoing validity (no known end date)"
    )
    valid_from: int = Field(
        default_factory=lambda: int(datetime.now(timezone.utc).timestamp() * 1000),
        description="Timestamp (ms since epoch) when fact became valid"
    )
    valid_until: Optional[int] = Field(
        default=None,
        description="Expected timestamp (ms) when fact validity ends (from classification)"
    )
    expired_at: Optional[int] = Field(
        default=None,
        description="Actual timestamp (ms) when fact ceased being valid"
    )

    # Confidence
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 (uncertain) and 1.0 (certain)"
    )

    # Invalidation metadata
    invalidated_by: Optional[UUID] = Field(
        default=None,
        description="UUID of the AtomicFact that superseded this one"
    )
    invalidated_at: Optional[int] = Field(
        default=None,
        description="Timestamp (ms) when this fact was invalidated by another"
    )

    # Housekeeping
    extracted_at: int = Field(
        default_factory=lambda: int(datetime.now(timezone.utc).timestamp() * 1000),
        description="Timestamp (ms) when this fact was extracted from source text"
    )

    # Metadata for indexing and deduplication
    metadata: dict = {
        "index_fields": ["subject", "predicate", "object"]
    }

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {v}")
        return v
