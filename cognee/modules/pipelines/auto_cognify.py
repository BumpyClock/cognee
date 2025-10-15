"""
Auto-Cognify Background Worker Module.

This module provides automatic background processing for cognee. When data is added via
cognee.add(), datasets are marked as "dirty" and a background worker periodically checks
for dirty datasets and runs cognee.cognify() on them.

Key Features:
- Singleton worker pattern (one worker per process)
- Thread-based for compatibility with both sync CLI and async servers
- Thread-safe dirty dataset tracking
- Graceful exception handling (no crash loops)
- Configurable check interval (default 10 minutes)
- Clean shutdown via threading.Event

Public API:
- mark_dataset_dirty(dataset_id): Mark a dataset as needing processing
- start_auto_cognify_worker(interval_seconds): Start the background worker
- stop_auto_cognify_worker(): Stop the worker cleanly
- get_worker_state(): Get current worker state (for testing)
"""

import asyncio
import threading
import time
from typing import Set, Optional
from uuid import UUID

from cognee.shared.logging_utils import get_logger

logger = get_logger("auto_cognify")

# ============================================================================
# Module-level state (protected by locks for thread safety)
# ============================================================================

# Set of dataset IDs that have been modified since last cognify run
_dirty_datasets: Set[UUID] = set()

# Lock protecting the dirty datasets set
_dirty_lock = threading.Lock()

# Worker thread instance
_worker_thread: Optional[threading.Thread] = None

# Flag indicating worker has been started
_worker_started = False

# Lock protecting worker startup (ensures singleton)
_worker_lock = threading.Lock()

# Event to signal worker to stop
_stop_event = threading.Event()

# Check interval in seconds (configurable, default 10 minutes)
_check_interval_seconds = 600


# ============================================================================
# Public API
# ============================================================================

def mark_dataset_dirty(dataset_id: UUID) -> None:
    """
    Mark a dataset as dirty (needing cognify processing).

    This function is thread-safe and should be called whenever data is added
    to a dataset via cognee.add().

    Args:
        dataset_id: UUID of the dataset that needs processing
    """
    with _dirty_lock:
        _dirty_datasets.add(dataset_id)
        logger.info(
            "Dataset marked for auto-cognify",
            dataset_id=str(dataset_id),
            total_dirty_datasets=len(_dirty_datasets)
        )


def start_auto_cognify_worker(interval_seconds: int = 600) -> None:
    """
    Start the auto-cognify background worker.

    This function uses a singleton pattern to ensure only one worker runs per process.
    The worker runs in a daemon thread so it doesn't block process exit.

    Args:
        interval_seconds: How often to check for dirty datasets (default 600 = 10 minutes)
    """
    global _worker_thread, _worker_started, _check_interval_seconds

    with _worker_lock:
        if _worker_started:
            logger.debug("Auto-cognify worker already started, skipping")
            return

        _worker_started = True
        _check_interval_seconds = interval_seconds
        _stop_event.clear()

        _worker_thread = threading.Thread(
            target=_worker_loop,
            name="auto-cognify-worker",
            daemon=True
        )
        _worker_thread.start()

        logger.info(
            "Auto-cognify worker started",
            interval_seconds=interval_seconds,
            thread_name=_worker_thread.name
        )


def stop_auto_cognify_worker() -> None:
    """
    Stop the auto-cognify background worker cleanly.

    This function signals the worker to stop and waits for it to finish.
    Used for testing and graceful shutdown.
    """
    global _worker_started

    if not _worker_started:
        logger.debug("Auto-cognify worker not running, nothing to stop")
        return

    logger.info("Stopping auto-cognify worker")
    _stop_event.set()

    if _worker_thread and _worker_thread.is_alive():
        _worker_thread.join(timeout=5.0)
        if _worker_thread.is_alive():
            logger.warning("Auto-cognify worker did not stop within timeout")

    with _worker_lock:
        _worker_started = False

    logger.info("Auto-cognify worker stopped")


def get_worker_state() -> dict:
    """
    Get the current state of the auto-cognify worker.

    Used primarily for testing and debugging.

    Returns:
        dict: Worker state including:
            - is_running: Whether worker is active
            - dirty_dataset_count: Number of datasets pending processing
            - dirty_datasets: List of dirty dataset IDs (as strings)
            - check_interval_seconds: Current check interval
    """
    with _dirty_lock:
        dirty_dataset_ids = [str(dataset_id) for dataset_id in _dirty_datasets]
        dirty_count = len(_dirty_datasets)

    return {
        "is_running": _worker_started,
        "dirty_dataset_count": dirty_count,
        "dirty_datasets": dirty_dataset_ids,
        "check_interval_seconds": _check_interval_seconds
    }


# ============================================================================
# Internal worker implementation
# ============================================================================

def _worker_loop() -> None:
    """
    Main worker loop that periodically checks for dirty datasets and processes them.

    This function runs in a background thread and:
    1. Waits for the check interval (interruptible via stop event)
    2. Checks if there are any dirty datasets
    3. If dirty datasets exist, collects them and runs cognify
    4. Handles exceptions gracefully without crashing
    5. Continues running until stop event is set
    """
    logger.info("Auto-cognify worker loop started")

    while not _stop_event.is_set():
        # Wait for the check interval (interruptible)
        if _stop_event.wait(timeout=_check_interval_seconds):
            # Stop event was set, exit loop
            logger.debug("Auto-cognify worker received stop signal")
            break

        try:
            # Check if there are any dirty datasets
            datasets_to_process = _collect_dirty_datasets()

            if not datasets_to_process:
                logger.debug("No dirty datasets to process, sleeping")
                continue

            logger.info(
                "Processing dirty datasets",
                dataset_count=len(datasets_to_process),
                dataset_ids=[str(d) for d in datasets_to_process]
            )

            # Run cognify on the dirty datasets
            _run_cognify_on_datasets(datasets_to_process)

            logger.info(
                "Auto-cognify completed successfully",
                processed_dataset_count=len(datasets_to_process)
            )

        except Exception as e:
            # Log the error but don't crash - continue running
            logger.error(
                "Auto-cognify encountered an error, will retry on next interval",
                exc_info=True,
                error_type=type(e).__name__,
                error_message=str(e)
            )

    logger.info("Auto-cognify worker loop exited")


def _collect_dirty_datasets() -> list[UUID]:
    """
    Atomically collect and clear the dirty datasets set.

    This ensures that datasets are processed exactly once and prevents
    re-processing the same data if cognify takes longer than the check interval.

    Returns:
        list[UUID]: List of dataset IDs that need processing
    """
    with _dirty_lock:
        if not _dirty_datasets:
            return []

        # Collect all dirty datasets
        datasets = list(_dirty_datasets)

        # Clear the set atomically
        _dirty_datasets.clear()

        return datasets


def _run_cognify_on_datasets(datasets: list[UUID]) -> None:
    """
    Run cognee.cognify() on the specified datasets.

    This function creates a new event loop and runs cognify in blocking mode.
    Using asyncio.run() allows the worker thread to have its own event loop,
    which is necessary since the worker runs in a separate thread.

    Args:
        datasets: List of dataset UUIDs to process

    Raises:
        Exception: Any exception from cognify is propagated to caller for logging
    """
    # Import here to avoid circular imports at module load time
    from cognee.api.v1.cognify import cognify

    # Create a new event loop for this thread and run cognify
    # We use run_in_background=False to ensure cognify completes before we return
    asyncio.run(
        cognify(
            datasets=datasets,
            run_in_background=False,
            incremental_loading=True
        )
    )
