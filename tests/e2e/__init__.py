"""
End-to-end tests for temporal cascade pipeline.

This package contains comprehensive E2E validation tests for the atomic fact
extraction and temporal classification pipeline.

Test Suites:
- test_temporal_cascade.py: Complete pipeline tests with 6 temporal documents
- test_temporal_cascade_performance.py: Performance validation (<2x overhead)
- test_temporal_cascade_regression.py: Backward compatibility tests

Run with:
    pytest tests/e2e/ -v -s
    pytest tests/e2e/ -v -s -m e2e
    pytest tests/e2e/ -v -s -m performance
    pytest tests/e2e/ -v -s -m regression
"""
