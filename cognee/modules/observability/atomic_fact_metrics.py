# ABOUTME: Observability and metrics tracking for atomic fact extraction pipeline.
# ABOUTME: Provides structured logging and performance metrics for extraction, classification, and invalidation operations.

from cognee.shared.logging_utils import get_logger

logger = get_logger("atomic_fact_metrics")


async def track_extraction(count: int, latency_ms: float, correlation_id: str) -> None:
    """
    Track atomic fact extraction metrics.

    Logs the number of facts extracted and processing latency for observability.
    This helps monitor extraction performance and identify bottlenecks.

    Args:
        count: Number of atomic facts extracted
        latency_ms: Processing time in milliseconds
        correlation_id: Unique identifier for correlating logs across the pipeline

    Returns:
        None
    """
    logger.info(
        f"Extracted {count} atomic facts in {latency_ms}ms",
        extra={"correlation_id": correlation_id, "fact_count": count, "latency_ms": latency_ms}
    )


async def track_classification(batch_size: int, latency_ms: float, correlation_id: str) -> None:
    """
    Track classification batch metrics.

    Logs batch processing metrics for temporal and fact-type classification.
    Helps monitor classification performance and batch processing efficiency.

    Args:
        batch_size: Number of facts classified in this batch
        latency_ms: Processing time in milliseconds
        correlation_id: Unique identifier for correlating logs across the pipeline

    Returns:
        None
    """
    logger.info(
        f"Classified {batch_size} facts in {latency_ms}ms",
        extra={
            "correlation_id": correlation_id,
            "batch_size": batch_size,
            "latency_ms": latency_ms,
            "avg_latency_per_fact": round(latency_ms / batch_size, 2) if batch_size > 0 else 0
        }
    )


async def track_invalidation(fact_id: str, new_fact_id: str, reason: str) -> None:
    """
    Track fact invalidation events.

    Logs when a fact is invalidated by a newer fact. This creates an audit trail
    for fact lifecycle management and helps debug invalidation chains.

    Args:
        fact_id: UUID of the fact being invalidated
        new_fact_id: UUID of the superseding fact
        reason: Reason for invalidation (e.g., 'superseded', 'confidence_override')

    Returns:
        None
    """
    logger.info(
        f"Fact {fact_id} invalidated by {new_fact_id} - reason: {reason}",
        extra={
            "fact_id": fact_id,
            "new_fact_id": new_fact_id,
            "invalidation_reason": reason
        }
    )


async def track_conflict_resolution(conflicts_found: int, conflicts_resolved: int) -> None:
    """
    Track conflict detection and resolution.

    Logs conflict detection results to monitor how often facts conflict and
    how many get resolved through invalidation.

    Args:
        conflicts_found: Number of conflicting facts detected
        conflicts_resolved: Number of conflicts successfully resolved

    Returns:
        None
    """
    logger.info(
        f"Conflict resolution: {conflicts_found} found, {conflicts_resolved} resolved",
        extra={
            "conflicts_found": conflicts_found,
            "conflicts_resolved": conflicts_resolved,
            "resolution_rate": round(conflicts_resolved / conflicts_found, 2) if conflicts_found > 0 else 0
        }
    )
