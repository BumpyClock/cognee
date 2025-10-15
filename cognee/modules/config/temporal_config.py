"""Configuration for temporal atomic fact extraction."""

import os
from pydantic import BaseModel, Field


class TemporalConfig(BaseModel):
    """
    Configuration for temporal atomic fact extraction and classification.

    Atomic fact extraction is always enabled as the default pipeline behavior.

    Attributes:
        extraction_rounds: Number of iterative LLM extraction rounds for refinement.
                          More rounds = better pronoun resolution and fact completeness.
                          Default: 2
        classification_batch_size: Number of facts classified per LLM batch call.
                                   Larger batches = better throughput but higher latency.
                                   Default: 10
    """

    extraction_rounds: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Number of extraction refinement rounds (1-5)"
    )
    classification_batch_size: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Facts classified per LLM batch (1-50)"
    )


def get_temporal_config() -> TemporalConfig:
    """
    Load temporal configuration from environment variables with validation.

    Environment Variables:
        ATOMIC_EXTRACTION_ROUNDS: Number of extraction rounds (default: 2)
        ATOMIC_CLASSIFICATION_BATCH_SIZE: Facts per batch (default: 10)

    Returns:
        TemporalConfig instance with validated settings

    Raises:
        ValidationError: If environment values are outside valid ranges
    """
    return TemporalConfig(
        extraction_rounds=int(os.getenv("ATOMIC_EXTRACTION_ROUNDS", "2")),
        classification_batch_size=int(os.getenv("ATOMIC_CLASSIFICATION_BATCH_SIZE", "10")),
    )
