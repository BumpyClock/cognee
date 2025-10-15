# ABOUTME: Conflict detection for atomic facts in the knowledge graph.
# ABOUTME: Identifies facts that should be invalidated based on temporal types, confidence, and source deduplication.

from typing import List
from uuid import UUID
from cognee.modules.engine.models.AtomicFact import AtomicFact, TemporalType, FactType


async def find_conflicting_facts(
    new_fact: AtomicFact,
    existing_facts: List[AtomicFact]
) -> List[AtomicFact]:
    """
    Identify facts that conflict with the new fact.

    Conflict Rules:
    1. Match by (subject, predicate) pairs
    2. Ignore duplicates from same chunk/source_text (idempotency)
    3. STATIC facts replace older STATIC facts with same (subject, predicate)
    4. DYNAMIC facts coexist with time boundaries (no conflicts)
    5. ATEMPORAL facts coexist if they state the same truth
    6. OPINION facts can coexist (subjective, multiple valid)
    7. Higher confidence can override lower confidence (same subject, predicate)
    8. Lower confidence cannot override higher confidence

    Args:
        new_fact: Newly extracted fact to check for conflicts
        existing_facts: Previously stored facts to check against

    Returns:
        List of facts that should be invalidated by the new fact
    """
    conflicts = []

    for existing in existing_facts:
        # Rule 1: Must match (subject, predicate) to be considered
        if not (existing.subject == new_fact.subject and existing.predicate == new_fact.predicate):
            continue

        # Rule 2: Ignore duplicates from same source (idempotency)
        if existing.source_chunk_id == new_fact.source_chunk_id:
            continue

        # Rule 4: DYNAMIC facts coexist with time boundaries
        if new_fact.temporal_type == TemporalType.DYNAMIC or existing.temporal_type == TemporalType.DYNAMIC:
            continue

        # Rule 5: ATEMPORAL facts coexist (they're timeless truths)
        if new_fact.temporal_type == TemporalType.ATEMPORAL and existing.temporal_type == TemporalType.ATEMPORAL:
            continue

        # Rule 6: OPINION facts can coexist (subjective statements)
        if new_fact.fact_type == FactType.OPINION or existing.fact_type == FactType.OPINION:
            continue

        # Rule 3 & 7: STATIC facts - check confidence and time
        if new_fact.temporal_type == TemporalType.STATIC and existing.temporal_type == TemporalType.STATIC:
            # Rule 8: Lower confidence cannot override higher confidence
            if new_fact.confidence < existing.confidence:
                continue

            # Rule 7: Higher confidence can override, or same confidence with newer timestamp
            if new_fact.confidence > existing.confidence:
                conflicts.append(existing)
            elif new_fact.confidence == existing.confidence and new_fact.valid_from >= existing.valid_from:
                # Same confidence - newer fact wins
                conflicts.append(existing)

    return conflicts
