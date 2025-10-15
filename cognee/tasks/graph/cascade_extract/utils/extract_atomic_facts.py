# ABOUTME: Extracts atomic facts from text using multi-round LLM-based decomposition
# ABOUTME: Converts complex sentences into (subject, predicate, object) triplets with deduplication

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from cognee.infrastructure.llm.prompts import render_prompt, read_query_prompt
from cognee.infrastructure.llm.LLMGateway import LLMGateway
from cognee.root_dir import get_absolute_path
from cognee.modules.engine.models.AtomicFact import AtomicFact, FactType, TemporalType
from cognee.tasks.graph.cascade_extract.models.extraction_models import (
    AtomicFactExtractionResponse,
)


async def extract_atomic_statements(
    text: str,
    source_chunk_id: UUID,
    n_rounds: int = 2,
    existing_facts: Optional[List[AtomicFact]] = None,
) -> List[AtomicFact]:
    """
    Extract atomic facts from text through multi-round LLM analysis.

    This function decomposes complex sentences into simple (subject, predicate, object)
    triplets, resolving pronouns and extracting implicit relationships. Multi-round
    extraction allows refinement and discovery of facts missed in earlier rounds.

    Args:
        text: Source text to extract facts from
        source_chunk_id: UUID of the DocumentChunk this text came from
        n_rounds: Number of extraction rounds for iterative refinement (default: 2)
        existing_facts: Previously extracted facts to avoid duplicates (optional)

    Returns:
        List of AtomicFact instances with core triplet and source tracking populated.
        Classification fields (fact_type, temporal_type, confidence) are set to defaults
        and should be updated via classify_atomic_facts_temporally().

    Raises:
        ValueError: If text is empty or source_chunk_id is invalid
        Exception: If LLM extraction fails

    Example:
        >>> facts = await extract_atomic_statements(
        ...     text="John, who works at Google, lives in NYC",
        ...     source_chunk_id=chunk.id
        ... )
        >>> len(facts)
        2
        >>> facts[0].subject, facts[0].predicate, facts[0].object
        ('John', 'works at', 'Google')
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    all_facts: List[AtomicFact] = []
    seen_triplets = set()  # For deduplication: (subject, predicate, object)

    # Initialize with existing facts to avoid re-extraction
    if existing_facts:
        for fact in existing_facts:
            triplet = (
                fact.subject.lower().strip(),
                fact.predicate.lower().strip(),
                fact.object.lower().strip(),
            )
            seen_triplets.add(triplet)
            all_facts.append(fact)

    base_directory = get_absolute_path("./tasks/graph/cascade_extract/prompts")

    for round_num in range(n_rounds):
        # Format previously extracted facts for prompt
        previous_facts_str = _format_facts_for_prompt(all_facts)

        context = {
            "text": text,
            "previous_facts": previous_facts_str,
            "round_number": round_num + 1,
            "total_rounds": n_rounds,
        }

        # Render prompts
        text_input = render_prompt(
            "extract_atomic_facts_prompt_input.txt",
            context,
            base_directory=base_directory,
        )
        system_prompt = read_query_prompt(
            "extract_atomic_facts_prompt_system.txt",
            base_directory=base_directory,
        )

        # Call LLM with structured output
        try:
            response: AtomicFactExtractionResponse = (
                await LLMGateway.acreate_structured_output(
                    text_input=text_input,
                    system_prompt=system_prompt,
                    response_model=AtomicFactExtractionResponse,
                )
            )
        except Exception as e:
            raise Exception(
                f"Failed to extract atomic facts in round {round_num + 1}: {str(e)}"
            ) from e

        # Process extracted facts
        current_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

        for fact_dict in response.facts:
            # Normalize for deduplication
            triplet = (
                fact_dict["subject"].lower().strip(),
                fact_dict["predicate"].lower().strip(),
                fact_dict["object"].lower().strip(),
            )

            # Skip duplicates
            if triplet in seen_triplets:
                continue

            # Create AtomicFact with default classification values
            # These will be updated by classify_atomic_facts_temporally()
            atomic_fact = AtomicFact(
                subject=fact_dict["subject"].strip(),
                predicate=fact_dict["predicate"].strip(),
                object=fact_dict["object"].strip(),
                source_chunk_id=source_chunk_id,
                source_text=text,
                # Default classification - to be updated by classification step
                fact_type=FactType.FACT,  # Default assumption
                temporal_type=TemporalType.STATIC,  # Default assumption
                confidence=0.5,  # Neutral confidence before classification
                is_open_interval=True,  # Assume ongoing validity initially
                valid_from=current_timestamp,
                extracted_at=current_timestamp,
            )

            all_facts.append(atomic_fact)
            seen_triplets.add(triplet)

    # Return only newly extracted facts (excluding existing_facts)
    if existing_facts:
        return all_facts[len(existing_facts) :]
    return all_facts


def _format_facts_for_prompt(facts: List[AtomicFact]) -> str:
    """
    Format facts as a readable string for inclusion in prompts.

    Args:
        facts: List of AtomicFact instances to format

    Returns:
        Formatted string with one fact per line, or "None" if empty
    """
    if not facts:
        return "None"

    formatted_lines = []
    for idx, fact in enumerate(facts, 1):
        formatted_lines.append(
            f"{idx}. ({fact.subject}, {fact.predicate}, {fact.object})"
        )

    return "\n".join(formatted_lines)
