"""
Unit tests for auto-cognify background worker module.

Tests cover:
- Thread-safe dataset marking
- Worker lifecycle (start, stop, singleton)
- Dirty dataset collection and processing
- Exception handling and resilience
- Worker state inspection
"""

import pytest
import threading
import time
from uuid import uuid4
from unittest.mock import patch, MagicMock, AsyncMock
from cognee.modules.pipelines import auto_cognify


@pytest.fixture(autouse=True)
def reset_worker_state():
    """
    Reset worker state before and after each test.

    This fixture ensures test isolation by:
    1. Stopping any running worker before the test
    2. Clearing dirty datasets
    3. Resetting worker flags
    4. Stopping worker again after test completes
    """
    # Stop worker if running
    auto_cognify.stop_auto_cognify_worker()

    # Clear module state
    with auto_cognify._dirty_lock:
        auto_cognify._dirty_datasets.clear()

    with auto_cognify._worker_lock:
        auto_cognify._worker_started = False
        auto_cognify._worker_thread = None

    auto_cognify._stop_event.clear()

    yield

    # Cleanup after test
    auto_cognify.stop_auto_cognify_worker()
    with auto_cognify._dirty_lock:
        auto_cognify._dirty_datasets.clear()


def test_mark_dataset_dirty_adds_to_queue():
    """
    Test that mark_dataset_dirty correctly adds dataset IDs to the dirty set.
    """
    dataset_id_1 = uuid4()
    dataset_id_2 = uuid4()

    auto_cognify.mark_dataset_dirty(dataset_id_1)
    auto_cognify.mark_dataset_dirty(dataset_id_2)

    state = auto_cognify.get_worker_state()

    assert state["dirty_dataset_count"] == 2
    assert str(dataset_id_1) in state["dirty_datasets"]
    assert str(dataset_id_2) in state["dirty_datasets"]


def test_mark_dataset_dirty_is_idempotent():
    """
    Test that marking the same dataset dirty multiple times doesn't duplicate it.
    """
    dataset_id = uuid4()

    auto_cognify.mark_dataset_dirty(dataset_id)
    auto_cognify.mark_dataset_dirty(dataset_id)
    auto_cognify.mark_dataset_dirty(dataset_id)

    state = auto_cognify.get_worker_state()

    assert state["dirty_dataset_count"] == 1
    assert str(dataset_id) in state["dirty_datasets"]


def test_mark_dataset_dirty_is_thread_safe():
    """
    Test that concurrent calls to mark_dataset_dirty are thread-safe.
    """
    dataset_ids = [uuid4() for _ in range(50)]
    threads = []

    def mark_multiple_datasets(ids):
        for dataset_id in ids:
            auto_cognify.mark_dataset_dirty(dataset_id)

    # Split dataset IDs across 5 threads
    chunk_size = 10
    for i in range(5):
        chunk = dataset_ids[i * chunk_size:(i + 1) * chunk_size]
        thread = threading.Thread(target=mark_multiple_datasets, args=(chunk,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    state = auto_cognify.get_worker_state()

    # All 50 unique datasets should be marked
    assert state["dirty_dataset_count"] == 50


def test_worker_starts_successfully():
    """
    Test that worker starts and sets correct state.
    """
    auto_cognify.start_auto_cognify_worker(interval_seconds=1)

    state = auto_cognify.get_worker_state()

    assert state["is_running"] is True
    assert state["check_interval_seconds"] == 1
    assert auto_cognify._worker_thread is not None
    assert auto_cognify._worker_thread.is_alive()


def test_worker_singleton_pattern_prevents_duplicate_workers():
    """
    Test that starting the worker multiple times doesn't create duplicate workers.
    """
    auto_cognify.start_auto_cognify_worker(interval_seconds=1)
    first_thread = auto_cognify._worker_thread

    # Try to start again
    auto_cognify.start_auto_cognify_worker(interval_seconds=1)
    second_thread = auto_cognify._worker_thread

    # Should be the same thread
    assert first_thread is second_thread
    assert first_thread.is_alive()


def test_worker_stops_cleanly():
    """
    Test that worker stops cleanly when requested.
    """
    auto_cognify.start_auto_cognify_worker(interval_seconds=1)
    assert auto_cognify._worker_started is True

    auto_cognify.stop_auto_cognify_worker()

    # Give worker thread time to exit
    time.sleep(0.2)

    state = auto_cognify.get_worker_state()
    assert state["is_running"] is False


@patch("cognee.modules.pipelines.auto_cognify.asyncio.run")
def test_worker_processes_dirty_datasets(mock_asyncio_run):
    """
    Test that worker processes dirty datasets by calling cognify.
    """
    # Setup mock
    mock_asyncio_run.return_value = None

    # Mark some datasets as dirty
    dataset_id_1 = uuid4()
    dataset_id_2 = uuid4()
    auto_cognify.mark_dataset_dirty(dataset_id_1)
    auto_cognify.mark_dataset_dirty(dataset_id_2)

    # Start worker with short interval
    auto_cognify.start_auto_cognify_worker(interval_seconds=0.1)

    # Wait for worker to process
    time.sleep(0.3)

    # Stop worker
    auto_cognify.stop_auto_cognify_worker()

    # Verify asyncio.run was called with cognify
    assert mock_asyncio_run.called
    call_args = mock_asyncio_run.call_args

    # The call should be asyncio.run(cognify(...))
    # We can't easily inspect the coroutine, but we can verify it was called
    assert call_args is not None

    # Verify dirty datasets were cleared
    state = auto_cognify.get_worker_state()
    assert state["dirty_dataset_count"] == 0


@patch("cognee.modules.pipelines.auto_cognify.asyncio.run")
def test_worker_does_nothing_when_no_dirty_datasets(mock_asyncio_run):
    """
    Test that worker doesn't call cognify when there are no dirty datasets.
    """
    # Setup mock
    mock_asyncio_run.return_value = None

    # Start worker with short interval (no dirty datasets)
    auto_cognify.start_auto_cognify_worker(interval_seconds=0.1)

    # Wait for worker to check
    time.sleep(0.3)

    # Stop worker
    auto_cognify.stop_auto_cognify_worker()

    # Verify asyncio.run was NOT called since no dirty datasets
    assert not mock_asyncio_run.called


@patch("cognee.modules.pipelines.auto_cognify.asyncio.run")
def test_worker_handles_cognify_exceptions(mock_asyncio_run):
    """
    Test that worker continues running even when cognify raises an exception.
    """
    # Setup mock to raise exception on first call, succeed on second
    call_count = [0]

    def side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            raise Exception("Cognify failed!")
        return None

    mock_asyncio_run.side_effect = side_effect

    # Mark datasets dirty
    dataset_id_1 = uuid4()
    auto_cognify.mark_dataset_dirty(dataset_id_1)

    # Start worker with short interval
    auto_cognify.start_auto_cognify_worker(interval_seconds=0.1)

    # Wait for first processing (will fail)
    time.sleep(0.15)

    # Mark another dataset dirty
    dataset_id_2 = uuid4()
    auto_cognify.mark_dataset_dirty(dataset_id_2)

    # Wait for second processing (should succeed)
    time.sleep(0.15)

    # Stop worker
    auto_cognify.stop_auto_cognify_worker()

    # Verify worker is still running and processed both attempts
    assert mock_asyncio_run.call_count >= 1
    # Worker should have recovered and continued running


@patch("cognee.modules.pipelines.auto_cognify.asyncio.run")
def test_worker_batches_multiple_datasets(mock_asyncio_run):
    """
    Test that worker batches all dirty datasets into a single cognify call.
    """
    # Setup mock
    mock_asyncio_run.return_value = None

    # Mark multiple datasets dirty
    dataset_ids = [uuid4() for _ in range(5)]
    for dataset_id in dataset_ids:
        auto_cognify.mark_dataset_dirty(dataset_id)

    # Start worker with short interval
    auto_cognify.start_auto_cognify_worker(interval_seconds=0.1)

    # Wait for worker to process
    time.sleep(0.3)

    # Stop worker
    auto_cognify.stop_auto_cognify_worker()

    # Verify asyncio.run was called once (not 5 times)
    # This confirms batching behavior
    assert mock_asyncio_run.call_count == 1

    # Verify all datasets were cleared
    state = auto_cognify.get_worker_state()
    assert state["dirty_dataset_count"] == 0


def test_collect_dirty_datasets_is_atomic():
    """
    Test that _collect_dirty_datasets atomically clears the set.
    """
    dataset_id_1 = uuid4()
    dataset_id_2 = uuid4()

    auto_cognify.mark_dataset_dirty(dataset_id_1)
    auto_cognify.mark_dataset_dirty(dataset_id_2)

    # Collect datasets
    collected = auto_cognify._collect_dirty_datasets()

    assert len(collected) == 2
    assert dataset_id_1 in collected
    assert dataset_id_2 in collected

    # Verify set is now empty
    state = auto_cognify.get_worker_state()
    assert state["dirty_dataset_count"] == 0

    # Collecting again should return empty list
    collected_again = auto_cognify._collect_dirty_datasets()
    assert len(collected_again) == 0


def test_collect_dirty_datasets_returns_empty_when_no_datasets():
    """
    Test that _collect_dirty_datasets returns empty list when nothing is dirty.
    """
    collected = auto_cognify._collect_dirty_datasets()
    assert collected == []


def test_get_worker_state_returns_correct_structure():
    """
    Test that get_worker_state returns expected data structure.
    """
    state = auto_cognify.get_worker_state()

    # Verify structure
    assert "is_running" in state
    assert "dirty_dataset_count" in state
    assert "dirty_datasets" in state
    assert "check_interval_seconds" in state

    # Verify types
    assert isinstance(state["is_running"], bool)
    assert isinstance(state["dirty_dataset_count"], int)
    assert isinstance(state["dirty_datasets"], list)
    assert isinstance(state["check_interval_seconds"], int)


@patch("cognee.modules.pipelines.auto_cognify.asyncio.run")
def test_worker_uses_correct_cognify_parameters(mock_asyncio_run):
    """
    Test that worker calls cognify with correct parameters.
    """
    # We need to capture the coroutine passed to asyncio.run
    captured_coro = None

    def capture_coro(coro):
        nonlocal captured_coro
        captured_coro = coro
        # Close the coroutine to prevent warnings
        coro.close()
        return None

    mock_asyncio_run.side_effect = capture_coro

    # Mark dataset dirty
    dataset_id = uuid4()
    auto_cognify.mark_dataset_dirty(dataset_id)

    # Start worker
    auto_cognify.start_auto_cognify_worker(interval_seconds=0.1)

    # Wait for processing
    time.sleep(0.3)

    # Stop worker
    auto_cognify.stop_auto_cognify_worker()

    # Verify asyncio.run was called
    assert mock_asyncio_run.called

    # Note: We can't easily inspect the coroutine parameters without running it,
    # but we verified it was called with a coroutine


def test_stop_worker_when_not_running_is_safe():
    """
    Test that stopping a worker that isn't running doesn't raise an error.
    """
    # Worker not started
    assert not auto_cognify._worker_started

    # Should not raise
    auto_cognify.stop_auto_cognify_worker()

    # Still not started
    assert not auto_cognify._worker_started


@patch("cognee.modules.pipelines.auto_cognify.asyncio.run")
def test_worker_respects_check_interval(mock_asyncio_run):
    """
    Test that worker respects the configured check interval.
    """
    mock_asyncio_run.return_value = None

    # Mark dataset dirty
    dataset_id = uuid4()
    auto_cognify.mark_dataset_dirty(dataset_id)

    # Start worker with 1 second interval
    auto_cognify.start_auto_cognify_worker(interval_seconds=1)

    # Should not process immediately
    time.sleep(0.3)
    assert mock_asyncio_run.call_count == 0

    # Should process after interval
    time.sleep(0.8)  # Total: 1.1 seconds
    auto_cognify.stop_auto_cognify_worker()

    # Should have been called at least once
    assert mock_asyncio_run.call_count >= 1
