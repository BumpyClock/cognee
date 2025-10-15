# ABOUTME: Test fixtures package for temporal cascade E2E validation
# ABOUTME: Exports comprehensive test documents, expected graphs, baselines, and utilities

from tests.fixtures.temporal_documents import (
    get_all_test_documents,
    get_document,
    get_expected,
    get_document_summary,
    STATIC_REPLACEMENT_DOC,
    DYNAMIC_COEXISTENCE_DOC,
    MIXED_FACTS_DOC,
    COMPLEX_SENTENCE_DOC,
    TEMPORAL_SEQUENCE_DOC,
    CONFIDENCE_OVERRIDE_DOC,
)

from tests.fixtures.expected_graphs import (
    get_expected_graph,
    validate_graph_structure,
    get_graph_summary,
)

from tests.fixtures.performance_baselines import (
    get_baseline_document,
    get_baseline_metrics,
    validate_performance,
    get_performance_summary,
    PERFORMANCE_TARGETS,
)

from tests.fixtures.fixture_utils import (
    load_temporal_document,
    load_expected_output,
    load_expected_graph,
    validate_fact_extraction,
    validate_invalidation_chain,
    parse_timestamp_string,
    timestamp_to_readable,
)

__all__ = [
    # Document loading
    "get_all_test_documents",
    "get_document",
    "get_expected",
    "get_document_summary",
    "load_temporal_document",
    "load_expected_output",
    "load_expected_graph",
    # Direct document exports
    "STATIC_REPLACEMENT_DOC",
    "DYNAMIC_COEXISTENCE_DOC",
    "MIXED_FACTS_DOC",
    "COMPLEX_SENTENCE_DOC",
    "TEMPORAL_SEQUENCE_DOC",
    "CONFIDENCE_OVERRIDE_DOC",
    # Graph validation
    "get_expected_graph",
    "validate_graph_structure",
    "get_graph_summary",
    # Performance
    "get_baseline_document",
    "get_baseline_metrics",
    "validate_performance",
    "get_performance_summary",
    "PERFORMANCE_TARGETS",
    # Utilities
    "validate_fact_extraction",
    "validate_invalidation_chain",
    "parse_timestamp_string",
    "timestamp_to_readable",
]
