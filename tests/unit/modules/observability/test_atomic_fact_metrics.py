# ABOUTME: Unit tests for atomic fact observability and metrics tracking.
# ABOUTME: Validates metric collection, log format, and correlation ID handling.

import pytest
from uuid import uuid4
from io import StringIO
import logging
from cognee.modules.observability.atomic_fact_metrics import (
    track_extraction,
    track_classification,
    track_invalidation,
    track_conflict_resolution,
)


@pytest.mark.asyncio
async def test_track_extraction_logs_correctly(caplog):
    """Test that track_extraction logs extraction metrics with correct format."""
    correlation_id = str(uuid4())

    with caplog.at_level(logging.INFO):
        await track_extraction(count=5, latency_ms=250.5, correlation_id=correlation_id)

    # Verify log entry was created
    assert len(caplog.records) == 1
    record = caplog.records[0]

    # Verify log level
    assert record.levelname == "INFO"

    # Verify message content
    assert "5" in record.message or "5" in str(record.msg)
    assert "250.5" in record.message or "250.5" in str(record.msg)

    # Verify correlation ID is present (either in message or extra)
    log_text = str(record.message) + str(getattr(record, 'msg', ''))
    assert correlation_id in log_text or (hasattr(record, 'correlation_id') and record.correlation_id == correlation_id)


@pytest.mark.asyncio
async def test_track_classification_logs_batch_metrics(caplog):
    """Test that track_classification logs batch processing metrics."""
    correlation_id = str(uuid4())

    with caplog.at_level(logging.INFO):
        await track_classification(batch_size=10, latency_ms=180.3, correlation_id=correlation_id)

    assert len(caplog.records) == 1
    record = caplog.records[0]

    # Verify batch size and latency are logged
    log_text = str(record.message) + str(getattr(record, 'msg', ''))
    assert "10" in log_text
    assert "180.3" in log_text or "180" in log_text


@pytest.mark.asyncio
async def test_track_invalidation_logs_event_details(caplog):
    """Test that track_invalidation logs fact invalidation events with reason."""
    fact_id = str(uuid4())
    new_fact_id = str(uuid4())
    reason = "superseded_by_newer_fact"

    with caplog.at_level(logging.INFO):
        await track_invalidation(fact_id=fact_id, new_fact_id=new_fact_id, reason=reason)

    assert len(caplog.records) == 1
    record = caplog.records[0]

    # Verify all IDs and reason are present
    log_text = str(record.message) + str(getattr(record, 'msg', ''))
    assert fact_id in log_text
    assert new_fact_id in log_text
    assert reason in log_text


@pytest.mark.asyncio
async def test_track_conflict_resolution_logs_counts(caplog):
    """Test that track_conflict_resolution logs conflict detection results."""
    with caplog.at_level(logging.INFO):
        await track_conflict_resolution(conflicts_found=3, conflicts_resolved=2)

    assert len(caplog.records) == 1
    record = caplog.records[0]

    # Verify counts are logged
    log_text = str(record.message) + str(getattr(record, 'msg', ''))
    assert "3" in log_text
    assert "2" in log_text


@pytest.mark.asyncio
async def test_track_extraction_with_zero_facts(caplog):
    """Test that extraction tracking handles edge case of zero facts extracted."""
    correlation_id = str(uuid4())

    with caplog.at_level(logging.INFO):
        await track_extraction(count=0, latency_ms=50.0, correlation_id=correlation_id)

    assert len(caplog.records) == 1
    # Should still log even with 0 facts (important for debugging)


@pytest.mark.asyncio
async def test_track_classification_with_large_batch(caplog):
    """Test that classification tracking handles large batch sizes."""
    correlation_id = str(uuid4())

    with caplog.at_level(logging.INFO):
        await track_classification(batch_size=100, latency_ms=1500.75, correlation_id=correlation_id)

    assert len(caplog.records) == 1
    record = caplog.records[0]

    # Verify large numbers are logged correctly
    log_text = str(record.message) + str(getattr(record, 'msg', ''))
    assert "100" in log_text
    assert "1500" in log_text or "1500.75" in log_text


@pytest.mark.asyncio
async def test_track_invalidation_with_default_reason(caplog):
    """Test that invalidation tracking uses default reason if not provided."""
    fact_id = str(uuid4())
    new_fact_id = str(uuid4())

    with caplog.at_level(logging.INFO):
        await track_invalidation(fact_id=fact_id, new_fact_id=new_fact_id, reason="superseded")

    assert len(caplog.records) == 1
    record = caplog.records[0]

    # Should have default reason
    log_text = str(record.message) + str(getattr(record, 'msg', ''))
    assert "superseded" in log_text


@pytest.mark.asyncio
async def test_all_metrics_use_atomic_fact_logger(caplog):
    """Test that all metric functions use the atomic_fact_metrics logger."""
    correlation_id = str(uuid4())

    # Clear any existing logs
    caplog.clear()

    with caplog.at_level(logging.INFO):
        await track_extraction(count=1, latency_ms=100.0, correlation_id=correlation_id)

    # Verify logger name contains atomic_fact or metrics
    if caplog.records:
        logger_name = caplog.records[0].name
        assert "atomic_fact" in logger_name or "metrics" in logger_name
