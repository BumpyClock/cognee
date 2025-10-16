"""
Performance validation tests for temporal cascade pipeline.

Tests that atomic fact processing meets <2x overhead target
using small/medium/large baseline documents.

Performance Targets (from tasklist):
- Atomic extraction: <500ms per chunk
- Classification: <200ms per batch of 10 facts
- Invalidation check: <100ms per fact
- Total overhead: <2x base pipeline
"""

import pytest
import time
from uuid import uuid4

from cognee.modules.chunking.models.DocumentChunk import DocumentChunk
from cognee.modules.data.processing.document_types import Document
from cognee.modules.engine.models import AtomicFact
from cognee.tasks.graph import extract_graph_from_data

from tests.fixtures import (
    get_baseline_document,
    get_baseline_metrics,
    validate_performance,
    PERFORMANCE_TARGETS,
)


# ==============================================================================
# Test Helpers
# ==============================================================================

async def measure_pipeline_performance(text: str, doc_name: str) -> dict:
    """
    Process document and measure performance metrics.

    Args:
        text: Document text
        doc_name: Document identifier

    Returns:
        Dictionary with:
        - elapsed_ms: Total processing time
        - fact_count: Number of facts extracted
        - facts_per_second: Extraction rate
    """
    # Create test document
    test_doc = Document(
        id=uuid4(),
        name=f"{doc_name}.txt",
        raw_data_location="memory",
        raw_data=text,
    )

    # Create chunk
    chunk = DocumentChunk(
        id=uuid4(),
        text=text,
        chunk_size=len(text),
        chunk_index=0,
        cut_type="document",
        is_part_of=test_doc,
    )

    # Process with timing
    start_time = time.time()
    processed_chunks = await extract_graph_from_data(
        data_chunks=[chunk],
        n_rounds=2,  # Default rounds
    )
    elapsed_ms = (time.time() - start_time) * 1000

    # Count atomic facts
    fact_count = 0
    for chunk in processed_chunks:
        if chunk.contains:
            fact_count += sum(
                1 for item in chunk.contains
                if isinstance(item, AtomicFact)
            )

    # Calculate rate
    facts_per_second = (fact_count / (elapsed_ms / 1000)) if elapsed_ms > 0 else 0

    return {
        "elapsed_ms": elapsed_ms,
        "fact_count": fact_count,
        "facts_per_second": facts_per_second,
    }


# ==============================================================================
# Small Document Performance (<550ms expected)
# ==============================================================================

@pytest.mark.e2e
@pytest.mark.performance
@pytest.mark.asyncio
async def test_small_document_performance():
    """
    Validate performance with small document (~50 words, ~5 facts).

    Expected:
    - Extraction + classification: <550ms
    - Max acceptable (2x overhead): <1100ms
    """
    # Load baseline document
    text = get_baseline_document("small")
    baseline = get_baseline_metrics("small")

    # Process and measure
    metrics = await measure_pipeline_performance(text, "small_perf")

    # Validate against baseline
    result = validate_performance(
        actual_time_ms=metrics["elapsed_ms"],
        actual_fact_count=metrics["fact_count"],
        doc_size="small",
    )

    # Report results
    print(f"\n📊 Small Document Performance")
    print(f"   Processing time: {metrics['elapsed_ms']:.0f}ms (expected ~{baseline['expected_total_time_ms']}ms)")
    print(f"   Max acceptable: {baseline['max_acceptable_time_ms']}ms (2x overhead)")
    print(f"   Facts extracted: {metrics['fact_count']} (expected ~{baseline['expected_facts']})")
    print(f"   Extraction rate: {metrics['facts_per_second']:.1f} facts/sec")
    print(f"   Overhead multiplier: {result['overhead_multiplier']:.2f}x")

    if result["warnings"]:
        for warning in result["warnings"]:
            print(f"   ⚠️  {warning}")

    # Assert within 2x overhead
    assert result["passed"], \
        f"Exceeded 2x overhead: {result['overhead_multiplier']:.2f}x " \
        f"({metrics['elapsed_ms']:.0f}ms > {baseline['max_acceptable_time_ms']}ms)"


# ==============================================================================
# Medium Document Performance (<1000ms expected)
# ==============================================================================

@pytest.mark.e2e
@pytest.mark.performance
@pytest.mark.asyncio
async def test_medium_document_performance():
    """
    Validate performance with medium document (~300 words, ~28 facts).

    Expected:
    - Extraction + classification: <1000ms
    - Max acceptable (2x overhead): <2000ms
    """
    # Load baseline document
    text = get_baseline_document("medium")
    baseline = get_baseline_metrics("medium")

    # Process and measure
    metrics = await measure_pipeline_performance(text, "medium_perf")

    # Validate against baseline
    result = validate_performance(
        actual_time_ms=metrics["elapsed_ms"],
        actual_fact_count=metrics["fact_count"],
        doc_size="medium",
    )

    # Report results
    print(f"\n📊 Medium Document Performance")
    print(f"   Processing time: {metrics['elapsed_ms']:.0f}ms (expected ~{baseline['expected_total_time_ms']}ms)")
    print(f"   Max acceptable: {baseline['max_acceptable_time_ms']}ms (2x overhead)")
    print(f"   Facts extracted: {metrics['fact_count']} (expected ~{baseline['expected_facts']})")
    print(f"   Extraction rate: {metrics['facts_per_second']:.1f} facts/sec")
    print(f"   Overhead multiplier: {result['overhead_multiplier']:.2f}x")

    if result["warnings"]:
        for warning in result["warnings"]:
            print(f"   ⚠️  {warning}")

    # Assert within 2x overhead
    assert result["passed"], \
        f"Exceeded 2x overhead: {result['overhead_multiplier']:.2f}x " \
        f"({metrics['elapsed_ms']:.0f}ms > {baseline['max_acceptable_time_ms']}ms)"


# ==============================================================================
# Large Document Performance (<2680ms expected)
# ==============================================================================

@pytest.mark.e2e
@pytest.mark.performance
@pytest.mark.asyncio
async def test_large_document_performance():
    """
    Validate performance with large document (~1000 words, ~115 facts).

    Expected:
    - Extraction + classification: <2680ms
    - Max acceptable (2x overhead): <5360ms

    This is a stress test for the pipeline.
    """
    # Load baseline document
    text = get_baseline_document("large")
    baseline = get_baseline_metrics("large")

    # Process and measure
    metrics = await measure_pipeline_performance(text, "large_perf")

    # Validate against baseline
    result = validate_performance(
        actual_time_ms=metrics["elapsed_ms"],
        actual_fact_count=metrics["fact_count"],
        doc_size="large",
    )

    # Report results
    print(f"\n📊 Large Document Performance (Stress Test)")
    print(f"   Processing time: {metrics['elapsed_ms']:.0f}ms (expected ~{baseline['expected_total_time_ms']}ms)")
    print(f"   Max acceptable: {baseline['max_acceptable_time_ms']}ms (2x overhead)")
    print(f"   Facts extracted: {metrics['fact_count']} (expected ~{baseline['expected_facts']})")
    print(f"   Extraction rate: {metrics['facts_per_second']:.1f} facts/sec")
    print(f"   Overhead multiplier: {result['overhead_multiplier']:.2f}x")

    if result["warnings"]:
        for warning in result["warnings"]:
            print(f"   ⚠️  {warning}")

    # Assert within 2x overhead
    assert result["passed"], \
        f"Exceeded 2x overhead: {result['overhead_multiplier']:.2f}x " \
        f"({metrics['elapsed_ms']:.0f}ms > {baseline['max_acceptable_time_ms']}ms)"


# ==============================================================================
# Component-Level Performance Targets
# ==============================================================================

@pytest.mark.e2e
@pytest.mark.performance
@pytest.mark.asyncio
async def test_performance_targets_documentation():
    """
    Document performance targets for reference.

    This is not a real test, just documentation of targets.
    """
    print(f"\n🎯 Performance Targets")
    print(f"   Atomic extraction: <{PERFORMANCE_TARGETS['extraction_per_chunk_ms']}ms per chunk")
    print(f"   Classification: <{PERFORMANCE_TARGETS['classification_per_batch_ms']}ms per batch (10 facts)")
    print(f"   Invalidation check: <{PERFORMANCE_TARGETS['invalidation_per_fact_ms']}ms per fact")
    print(f"   Total overhead: <{PERFORMANCE_TARGETS['total_overhead_multiplier']}x base pipeline")
    print(f"\n   Note: Component-level timing requires instrumentation in pipeline code.")
    print(f"   Current tests measure end-to-end performance only.")

    assert True, "Targets documented"


# ==============================================================================
# Performance Comparison Across Sizes
# ==============================================================================

@pytest.mark.e2e
@pytest.mark.performance
@pytest.mark.asyncio
async def test_performance_scaling():
    """
    Compare performance across document sizes to verify scaling.

    This test processes all three sizes and compares relative performance.
    Helps identify if performance degrades non-linearly with document size.
    """
    results = {}

    # Process all three sizes
    for size in ["small", "medium", "large"]:
        text = get_baseline_document(size)
        baseline = get_baseline_metrics(size)

        metrics = await measure_pipeline_performance(text, f"{size}_scaling")

        results[size] = {
            "elapsed_ms": metrics["elapsed_ms"],
            "fact_count": metrics["fact_count"],
            "facts_per_second": metrics["facts_per_second"],
            "overhead_multiplier": metrics["elapsed_ms"] / baseline["expected_total_time_ms"],
        }

    # Report comparison
    print(f"\n📈 Performance Scaling Comparison")
    print(f"   {'Size':<10} {'Time (ms)':<12} {'Facts':<8} {'Rate (f/s)':<12} {'Overhead':<10}")
    print(f"   {'-'*60}")

    for size in ["small", "medium", "large"]:
        r = results[size]
        print(f"   {size.capitalize():<10} {r['elapsed_ms']:>8.0f}ms   {r['fact_count']:>5}    "
              f"{r['facts_per_second']:>8.1f}      {r['overhead_multiplier']:>6.2f}x")

    # Check for concerning patterns
    small_rate = results["small"]["facts_per_second"]
    large_rate = results["large"]["facts_per_second"]

    if large_rate < small_rate * 0.5:
        print(f"\n   ⚠️  Performance degrades significantly with document size")
        print(f"   Small: {small_rate:.1f} f/s, Large: {large_rate:.1f} f/s")

    assert True, "Scaling comparison complete"
