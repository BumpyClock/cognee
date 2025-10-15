# ABOUTME: Invalidation workflow for atomic facts in the knowledge graph.
# ABOUTME: Handles timestamp updates, invalidation metadata, and prepares updates for database persistence.

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from cognee.modules.engine.models.AtomicFact import AtomicFact
from cognee.shared.logging_utils import get_logger

logger = get_logger("atomic_fact_invalidation")


async def prepare_invalidation_updates(
    fact: AtomicFact,
    new_fact_id: UUID,
    reason: str = "superseded"
) -> Dict[str, Any]:
    """
    Prepare invalidation updates for a fact.

    This function generates the update dictionary that should be applied to
    invalidate a fact. It sets timestamps and invalidation metadata.

    Args:
        fact: The AtomicFact to be invalidated
        new_fact_id: UUID of the superseding fact
        reason: Reason for invalidation (for audit trail)

    Returns:
        Dict containing fields to update: invalidated_by, invalidated_at, expired_at, valid_until
    """
    current_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

    updates = {
        "invalidated_by": new_fact_id,
        "invalidated_at": current_timestamp,
        "expired_at": current_timestamp,
    }

    # Only set valid_until if it's not already set
    if fact.valid_until is None:
        updates["valid_until"] = current_timestamp
    else:
        # Preserve existing valid_until
        updates["valid_until"] = fact.valid_until

    logger.debug(
        f"Prepared invalidation updates for fact {fact.id}",
        extra={
            "fact_id": str(fact.id),
            "new_fact_id": str(new_fact_id),
            "reason": reason,
            "invalidated_at": current_timestamp
        }
    )

    return updates


async def invalidate_fact(
    fact_id: UUID,
    new_fact_id: UUID,
    reason: str = "superseded"
) -> Dict[str, Any]:
    """
    Mark a fact as invalidated by a newer fact.

    This function prepares the invalidation updates that should be applied to the fact.
    The actual database update should be performed by the caller using these updates.

    Updates performed:
    1. fact.invalidated_by = new_fact_id
    2. fact.valid_until = current_timestamp (if not already set)
    3. fact.expired_at = current_timestamp
    4. fact.invalidated_at = current_timestamp

    Note: In a full implementation, this would also:
    - Retrieve the fact from the database
    - Apply the updates
    - Create invalidation edge in graph (fact -> INVALIDATED_BY -> new_fact)
    - Persist changes to database

    For now, this returns the update dictionary that can be applied by the caller.

    Args:
        fact_id: UUID of fact to invalidate
        new_fact_id: UUID of superseding fact
        reason: Invalidation reason for audit trail (default: "superseded")

    Returns:
        Dict of updates to apply to the fact
    """
    current_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

    updates = {
        "invalidated_by": new_fact_id,
        "invalidated_at": current_timestamp,
        "expired_at": current_timestamp,
        "valid_until": current_timestamp,  # Will be preserved if already set when applied to fact
    }

    logger.info(
        f"Invalidating fact {fact_id} with new fact {new_fact_id}",
        extra={
            "fact_id": str(fact_id),
            "new_fact_id": str(new_fact_id),
            "invalidation_reason": reason,
            "invalidated_at": current_timestamp
        }
    )

    return updates
