# ABOUTME: Classifies atomic facts temporally (fact type, temporal type, confidence, validity)
# ABOUTME: Uses LLM to determine FACT/OPINION/PREDICTION and ATEMPORAL/STATIC/DYNAMIC classifications

from typing import List, Optional
from datetime import datetime, timezone
import re

from cognee.infrastructure.llm.prompts import render_prompt, read_query_prompt
from cognee.infrastructure.llm.LLMGateway import LLMGateway
from cognee.root_dir import get_absolute_path
from cognee.modules.engine.models.AtomicFact import AtomicFact, FactType, TemporalType
from cognee.modules.config import get_temporal_config
from cognee.tasks.graph.cascade_extract.models.extraction_models import (
    TemporalClassificationResponse,
)


async def classify_atomic_facts_temporally(
    facts: List[AtomicFact],
    context: Optional[str] = None,
    batch_size: Optional[int] = None,
) -> List[AtomicFact]:
    """
    Classify atomic facts for temporal and episodic properties using LLM.

    This function batch-processes facts to determine:
    - fact_type: FACT, OPINION, or PREDICTION
    - temporal_type: ATEMPORAL, STATIC, or DYNAMIC
    - confidence: Float 0.0-1.0 indicating classification certainty
    - Validity windows: valid_from, valid_until, is_open_interval

    The function updates facts in-place and returns them for convenience.

    Args:
        facts: List of AtomicFact instances to classify (must have source_text populated)
        context: Optional additional context beyond source_text for disambiguation
        batch_size: Optional batch size override. If None, reads from TemporalConfig.

    Returns:
        The same list of AtomicFact instances with classification fields updated

    Raises:
        ValueError: If facts list is empty or facts missing source_text
        Exception: If LLM classification fails

    Example:
        >>> facts = await extract_atomic_statements(text, chunk_id)
        >>> classified = await classify_atomic_facts_temporally(facts)
        >>> classified[0].fact_type
        <FactType.FACT: 'FACT'>
        >>> classified[0].confidence
        0.95
    """
    if not facts:
        raise ValueError("Facts list cannot be empty")

    # Validate all facts have source_text (not None and not empty)
    for idx, fact in enumerate(facts):
        if not fact.source_text or fact.source_text.strip() == "":
            raise ValueError(f"Fact at index {idx} is missing source_text field")

    # Process facts in batches for efficiency
    # Use provided batch_size or read from config
    if batch_size is None:
        temporal_config = get_temporal_config()
        batch_size = temporal_config.classification_batch_size

    for batch_start in range(0, len(facts), batch_size):
        batch_facts = facts[batch_start : batch_start + batch_size]
        await _classify_batch(batch_facts, context)

    return facts


async def _classify_batch(
    facts: List[AtomicFact],
    context: Optional[str] = None,
) -> None:
    """
    Classify a batch of facts using LLM with structured output.

    Updates facts in-place with classification results.

    Args:
        facts: Batch of facts to classify
        context: Optional additional context
    """
    # Use source_text from first fact as primary context
    # (assumes facts from same chunk have same source_text)
    source_text = facts[0].source_text

    # Format facts for prompt
    facts_list_str = _format_facts_for_classification(facts)

    prompt_context = {
        "source_text": source_text,
        "facts_list": facts_list_str,
        "context": context or "None",
    }

    base_directory = get_absolute_path("./tasks/graph/cascade_extract/prompts")

    # Render prompts
    text_input = render_prompt(
        "classify_atomic_fact_prompt_input.txt",
        prompt_context,
        base_directory=base_directory,
    )
    system_prompt = read_query_prompt(
        "classify_atomic_fact_prompt_system.txt",
        base_directory=base_directory,
    )

    # Call LLM with structured output
    try:
        response: TemporalClassificationResponse = (
            await LLMGateway.acreate_structured_output(
                text_input=text_input,
                system_prompt=system_prompt,
                response_model=TemporalClassificationResponse,
            )
        )
    except Exception as e:
        raise Exception(f"Failed to classify atomic facts: {str(e)}") from e

    # Apply classifications to facts
    current_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

    for classification in response.classifications:
        fact_index = classification.get("fact_index", None)

        # Validate fact_index
        if fact_index is None or not 0 <= fact_index < len(facts):
            continue  # Skip invalid indices

        fact = facts[fact_index]

        # Update fact_type
        fact.fact_type = FactType[classification["fact_type"]]

        # Update temporal_type
        fact.temporal_type = TemporalType[classification["temporal_type"]]

        # Update confidence
        fact.confidence = float(classification["confidence"])

        # Parse and set valid_from
        valid_from_raw = classification.get("valid_from")
        fact.valid_from = _parse_timestamp(
            valid_from_raw, current_timestamp, default=current_timestamp
        )

        # Parse and set valid_until
        valid_until_raw = classification.get("valid_until")
        fact.valid_until = _parse_timestamp(
            valid_until_raw, current_timestamp, default=None
        )

        # Set is_open_interval
        fact.is_open_interval = classification.get("is_open_interval", True)

        # Ensure expired_at remains None (only set during invalidation)
        fact.expired_at = None


def _format_facts_for_classification(facts: List[AtomicFact]) -> str:
    """
    Format facts as indexed list for classification prompt.

    Args:
        facts: List of AtomicFact instances

    Returns:
        Formatted string with indexed facts
    """
    formatted_lines = []
    for idx, fact in enumerate(facts):
        formatted_lines.append(
            f"{idx}. ({fact.subject}, {fact.predicate}, {fact.object})"
        )
    return "\n".join(formatted_lines)


def _parse_timestamp(
    timestamp_str: Optional[str],
    current_timestamp: int,
    default: Optional[int] = None,
) -> Optional[int]:
    """
    Parse timestamp string or special value into milliseconds since epoch.

    Handles special values returned by LLM:
    - "unknown": Returns default
    - "open": Returns None (open-ended)
    - "beginning_of_time": Returns 0
    - "extraction_time" or "statement_time": Returns current_timestamp
    - ISO date strings: Parses to timestamp
    - Integer timestamps: Returns as-is
    - "end_of_next_year", "end_of_period": Attempts to parse or returns default

    Args:
        timestamp_str: Raw timestamp value from LLM
        current_timestamp: Current time in milliseconds
        default: Default value if parsing fails

    Returns:
        Timestamp in milliseconds since epoch, or None for open-ended
    """
    if timestamp_str is None or timestamp_str == "unknown":
        return default

    if timestamp_str == "open":
        return None

    if timestamp_str == "beginning_of_time":
        return 0

    if timestamp_str in ("extraction_time", "statement_time"):
        return current_timestamp

    # Try parsing as integer
    if isinstance(timestamp_str, int):
        return timestamp_str

    try:
        timestamp_int = int(timestamp_str)
        return timestamp_int
    except (ValueError, TypeError):
        pass

    # Try parsing ISO date formats (YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS, etc.)
    # Try full datetime first, then date-only to ensure we capture time if present
    iso_patterns = [
        r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})",  # ISO datetime (try first)
        r"(\d{4})-(\d{2})-(\d{2})",  # YYYY-MM-DD (fallback)
    ]

    for pattern in iso_patterns:
        match = re.search(pattern, str(timestamp_str))
        if match:
            try:
                if len(match.groups()) == 3:  # Date only
                    year, month, day = match.groups()
                    dt = datetime(int(year), int(month), int(day), tzinfo=timezone.utc)
                else:  # Datetime
                    year, month, day, hour, minute, second = match.groups()
                    dt = datetime(
                        int(year),
                        int(month),
                        int(day),
                        int(hour),
                        int(minute),
                        int(second),
                        tzinfo=timezone.utc,
                    )
                return int(dt.timestamp() * 1000)
            except (ValueError, OverflowError):
                pass

    # Handle relative time expressions like "end_of_next_year"
    if "next_year" in str(timestamp_str).lower():
        next_year = datetime.now(timezone.utc).year + 1
        dt = datetime(next_year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)

    # If all parsing fails, return default
    return default
