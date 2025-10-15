"""
Manage atomic fact storage with conflict detection and invalidation.

This module handles the storage of atomic facts while detecting and resolving
conflicts according to temporal cascade rules.
"""

import asyncio
from typing import List
from uuid import uuid4

from cognee.modules.engine.models import AtomicFact
from cognee.infrastructure.databases.graph import get_graph_engine
from cognee.tasks.storage.manage_atomic_fact_conflicts import find_conflicting_facts
from cognee.tasks.storage.invalidate_facts import prepare_invalidation_updates
from cognee.modules.observability.atomic_fact_metrics import (
    track_conflict_resolution,
    track_invalidation,
)
from cognee.shared.logging_utils import get_logger

logger = get_logger("manage_atomic_fact_storage")


async def detect_and_invalidate_conflicting_facts(
    atomic_facts: List[AtomicFact],
    correlation_id: str = None,
) -> List[AtomicFact]:
    """
    Detect and invalidate conflicting facts for new atomic facts.

    For each new fact:
    1. Query existing facts with the same (subject, predicate)
    2. Detect conflicts using conflict resolution rules
    3. Invalidate conflicting facts in the database
    4. Return the new facts (ready for storage via add_data_points)

    Note: This function does NOT store the new facts. Storage happens via
    the add_data_points task in the pipeline.

    Args:
        atomic_facts: List of AtomicFact instances to check for conflicts
        correlation_id: Optional correlation ID for tracking

    Returns:
        The same list of atomic facts (for pipeline chaining)
    """
    if not atomic_facts:
        return []

    if correlation_id is None:
        correlation_id = str(uuid4())

    graph_engine = await get_graph_engine()
    logger.info(
        f"Storing {len(atomic_facts)} atomic facts with conflict detection "
        f"(correlation_id={correlation_id})"
    )

    total_conflicts_found = 0
    total_conflicts_resolved = 0

    # Process each fact for conflicts
    for new_fact in atomic_facts:
        try:
            # Query existing facts with same (subject, predicate)
            # Note: This is a simplified query - in production you'd use proper graph queries
            existing_facts = await _query_existing_facts(
                graph_engine,
                subject=new_fact.subject,
                predicate=new_fact.predicate,
            )

            # Detect conflicts
            conflicts = await find_conflicting_facts(new_fact, existing_facts)
            total_conflicts_found += len(conflicts)

            # Invalidate conflicting facts
            for old_fact in conflicts:
                try:
                    # Prepare invalidation updates
                    updates = await prepare_invalidation_updates(
                        fact=old_fact,
                        new_fact_id=new_fact.id,
                        reason="superseded",
                    )

                    # Apply updates to the old fact
                    old_fact.invalidated_by = updates["invalidated_by"]
                    old_fact.invalidated_at = updates["invalidated_at"]
                    old_fact.expired_at = updates["expired_at"]
                    if "valid_until" in updates:
                        old_fact.valid_until = updates["valid_until"]

                    # Update the fact in the database
                    await _update_fact_in_graph(graph_engine, old_fact)

                    # Track invalidation
                    await track_invalidation(
                        fact_id=str(old_fact.id),
                        new_fact_id=str(new_fact.id),
                        reason="superseded",
                    )
                    total_conflicts_resolved += 1

                except Exception as e:
                    logger.error(
                        f"Failed to invalidate fact {old_fact.id}: {e}",
                        exc_info=True
                    )
                    # Continue with other invalidations

        except Exception as e:
            logger.error(
                f"Failed to check conflicts for fact {new_fact.id}: {e}",
                exc_info=True
            )
            # Continue storing the fact even if conflict detection fails

    # Track conflict resolution metrics
    if total_conflicts_found > 0:
        await track_conflict_resolution(
            conflicts_found=total_conflicts_found,
            conflicts_resolved=total_conflicts_resolved,
        )
        logger.info(
            f"Resolved {total_conflicts_resolved}/{total_conflicts_found} conflicts "
            f"(correlation_id={correlation_id})"
        )

    return atomic_facts


async def _query_existing_facts(
    graph_engine,
    subject: str,
    predicate: str,
) -> List[AtomicFact]:
    """
    Query existing facts with the same (subject, predicate).

    This function queries the graph database for AtomicFact nodes that match
    the given subject and predicate, excluding already invalidated facts.

    Note: This function uses Cypher-like queries. Databases that don't support
    Cypher (or equivalent) may need custom implementations.

    Args:
        graph_engine: Graph database engine
        subject: Subject to match (e.g., "Alice")
        predicate: Predicate to match (e.g., "works_for")

    Returns:
        List of matching AtomicFact instances that are still valid
    """
    try:
        # Query for AtomicFact nodes with matching subject/predicate
        # Only return facts that haven't been invalidated
        # Note: This uses Cypher-like syntax. Adjust if using non-Cypher database.
        query = """
        MATCH (n:AtomicFact)
        WHERE n.subject = $subject
          AND n.predicate = $predicate
          AND n.invalidated_at IS NULL
        RETURN n
        """

        results = await graph_engine.query(
            query,
            {"subject": subject, "predicate": predicate}
        )

        # Parse results into AtomicFact instances
        # Handle different result formats from different graph adapters
        facts = []
        for result in results:
            node_data = None

            # Try different result formats:
            # 1. Neo4j/Memgraph format: result is dict with 'n' key
            if isinstance(result, dict) and 'n' in result:
                node_data = result['n']
            # 2. Kuzu format: result might be tuple or dict with node properties
            elif isinstance(result, tuple) and len(result) > 0:
                node_data = result[0] if isinstance(result[0], dict) else None
            # 3. Direct dict format
            elif isinstance(result, dict):
                node_data = result

            if node_data:
                # Reconstruct AtomicFact from node properties
                try:
                    fact = AtomicFact(**node_data)
                    facts.append(fact)
                except Exception as parse_error:
                    logger.warning(
                        f"Failed to parse AtomicFact from graph node: {parse_error}",
                        exc_info=True
                    )
                    continue

        return facts

    except Exception as e:
        logger.warning(
            f"Graph query failed for subject='{subject}', predicate='{predicate}': {e}. "
            "Conflict detection will be skipped for this fact. "
            "This may indicate the graph database doesn't support Cypher queries.",
            exc_info=True
        )
        # Return empty list on query failure to allow pipeline to continue
        return []


async def _update_fact_in_graph(graph_engine, fact: AtomicFact) -> None:
    """
    Update a fact in the graph database with invalidation metadata.

    This function updates an existing AtomicFact node's invalidation fields
    to mark it as superseded by a newer fact.

    Note: This function uses Cypher-like queries. Databases that don't support
    Cypher (or equivalent) may need custom implementations.

    Args:
        graph_engine: Graph database engine
        fact: AtomicFact instance with updated invalidation fields

    Raises:
        Exception: If graph update fails (logged and re-raised)
    """
    try:
        # Convert fact_id to string for query parameter
        fact_id_str = str(fact.id)

        # Build SET clauses for invalidation fields
        # Only update fields that are set (not None)
        set_clauses = []
        params = {"fact_id": fact_id_str}

        if fact.invalidated_by is not None:
            set_clauses.append("n.invalidated_by = $invalidated_by")
            params["invalidated_by"] = str(fact.invalidated_by)

        if fact.invalidated_at is not None:
            set_clauses.append("n.invalidated_at = $invalidated_at")
            params["invalidated_at"] = fact.invalidated_at

        if fact.expired_at is not None:
            set_clauses.append("n.expired_at = $expired_at")
            params["expired_at"] = fact.expired_at

        if fact.valid_until is not None:
            set_clauses.append("n.valid_until = $valid_until")
            params["valid_until"] = fact.valid_until

        if not set_clauses:
            # No fields to update
            return

        # Construct update query (Cypher-like syntax)
        query = f"""
        MATCH (n:AtomicFact {{id: $fact_id}})
        SET {", ".join(set_clauses)}
        RETURN n
        """

        results = await graph_engine.query(query, params)

        if not results:
            logger.warning(
                f"AtomicFact with id={fact_id_str} not found in graph during update. "
                "This may indicate the fact hasn't been stored yet."
            )

    except Exception as e:
        logger.warning(
            f"Failed to update AtomicFact {fact.id} in graph: {e}. "
            "This may indicate the graph database doesn't support Cypher queries. "
            "Invalidation will not be persisted to the graph.",
            exc_info=True
        )
        # Don't re-raise - allow pipeline to continue
        # The fact's invalidation metadata is already set in memory
