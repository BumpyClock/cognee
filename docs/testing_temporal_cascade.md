# Testing Guide - Temporal Cascade Feature

This guide explains how to test the temporal cascade feature at different levels: unit tests, integration tests, and end-to-end tests.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Test Categories](#test-categories)
3. [Running Tests](#running-tests)
4. [Using Test Fixtures](#using-test-fixtures)
5. [Performance Testing](#performance-testing)
6. [Creating New Tests](#creating-new-tests)
7. [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

```bash
# Install test dependencies
uv pip install pytest pytest-asyncio pytest-mock

# Set up LLM API key for E2E tests (optional for unit tests)
export LLM_API_KEY="your-api-key"
```

### Run All Tests

```bash
# Run all temporal cascade tests
pytest tests/ -v -k "atomic" -s

# Run with coverage
pytest tests/ -v -k "atomic" --cov=cognee.tasks.graph.cascade_extract --cov=cognee.modules.engine.models
```

## Test Categories

### 1. Unit Tests (145+ tests)

**Location**: `tests/unit/`

**Purpose**: Test individual components in isolation with mocked dependencies

**Categories**:
- `test_atomic_fact.py` - AtomicFact model validation (11 tests)
- `test_prompts.py` - Prompt template validation (19 tests)
- `test_extract_atomic_facts.py` - Extraction logic (32 tests)
- `test_classify_atomic_facts.py` - Classification logic (17 tests)
- `test_extraction_models.py` - Pydantic model validation (29 tests)
- `test_manage_atomic_fact_conflicts.py` - Conflict detection (10 tests)
- `test_invalidate_facts.py` - Invalidation logic (6 tests)
- `test_atomic_fact_metrics.py` - Observability (8 tests)
- `test_atomic_fact_graph_conversion.py` - Graph conversion (8 tests)

**Running Unit Tests**:
```bash
# All unit tests
pytest tests/unit/ -v -k "atomic" -s

# Specific module
pytest tests/unit/modules/engine/models/test_atomic_fact.py -v -s

# Specific test
pytest tests/unit/tasks/graph/cascade_extract/test_extract_atomic_facts.py::test_multi_round_extraction -v -s
```

### 2. Integration Tests (15+ tests)

**Location**: `tests/integration/`

**Purpose**: Test component interactions with real dependencies

**Categories**:
- `test_atomic_fact_pipeline.py` - Pipeline integration (4 tests)
- `test_atomic_fact_entity_resolution.py` - Entity resolution (7 tests)
- `test_atomic_fact_ontology_alignment.py` - Ontology alignment (5 tests)

**Running Integration Tests**:
```bash
# All integration tests
pytest tests/integration/ -v -k "atomic" -s

# Specific suite
pytest tests/integration/tasks/graph/test_atomic_fact_pipeline.py -v -s
```

### 3. E2E Tests (22 tests)

**Location**: `tests/e2e/`

**Purpose**: Validate complete pipeline with real LLM calls

**Categories**:
- `test_temporal_cascade.py` - Complete pipeline validation (7 tests)
- `test_temporal_cascade_performance.py` - Performance benchmarks (5 tests)
- `test_temporal_cascade_regression.py` - Backward compatibility (10 tests)

**Running E2E Tests**:
```bash
# All E2E tests (requires LLM API key)
pytest tests/e2e/ -v -s

# By category
pytest tests/e2e/ -v -s -m e2e           # Temporal cascade tests
pytest tests/e2e/ -v -s -m performance   # Performance tests
pytest tests/e2e/ -v -s -m regression    # Regression tests

# Specific test
pytest tests/e2e/test_temporal_cascade.py::test_static_replacement_pipeline -v -s
```

## Running Tests

### Test Execution Commands

```bash
# Run all tests
pytest tests/ -v -k "atomic"

# Run with detailed output
pytest tests/ -v -k "atomic" -s

# Run specific test file
pytest tests/unit/tasks/graph/cascade_extract/test_extract_atomic_facts.py -v -s

# Run specific test function
pytest tests/unit/tasks/graph/cascade_extract/test_extract_atomic_facts.py::test_multi_round_extraction -v -s

# Run with coverage
pytest tests/ -v -k "atomic" --cov=cognee --cov-report=html

# Run only fast tests (skip E2E)
pytest tests/unit tests/integration -v -k "atomic"

# Run in parallel (faster)
pytest tests/ -v -k "atomic" -n auto
```

### Environment Configuration

```bash
# Required for E2E tests
export LLM_API_KEY="your-openai-api-key"

# Optional configuration
export ATOMIC_EXTRACTION_ROUNDS=2
export ATOMIC_CLASSIFICATION_BATCH_SIZE=10

# Database configuration
export GRAPH_DATABASE_URL="your-graph-db-url"
export VECTOR_DATABASE_URL="your-vector-db-url"
```

### Pytest Markers

Add to `pyproject.toml` or `pytest.ini`:

```ini
[tool.pytest.ini_options]
markers = [
    "e2e: End-to-end validation tests",
    "performance: Performance validation tests",
    "regression: Backward compatibility tests",
]
```

## Using Test Fixtures

### Available Test Documents

Six comprehensive test documents are available in `tests/fixtures/temporal_documents.py`:

1. **static_replacement** - CEO succession
2. **dynamic_coexistence** - Stock prices
3. **mixed_facts** - All fact types
4. **complex_decomposition** - Multi-event extraction
5. **temporal_sequence** - Sequential invalidations
6. **confidence_override** - Confidence-based resolution

### Loading Test Documents

```python
from tests.fixtures.temporal_documents import load_temporal_document

# Load a test document
doc = load_temporal_document("static_replacement")

print(f"Text: {doc['text']}")
print(f"Expected facts: {doc['expected_facts']}")
print(f"Expected invalidations: {doc['expected_invalidations']}")

# Use in test
async def test_with_fixture():
    doc = load_temporal_document("static_replacement")
    facts = await extract_atomic_statements(doc['text'], chunk_id)

    # Validate
    assert len(facts) >= doc['expected_facts']['min']
    # ... more assertions
```

### Validation Utilities

```python
from tests.fixtures.fixture_utils import (
    validate_fact_extraction,
    validate_invalidation_chain,
    validate_performance
)

# Validate fact extraction
validate_fact_extraction(
    actual_facts=facts,
    expected_facts=doc['expected_facts'],
    allow_variance=True  # LLM can vary slightly
)

# Validate invalidation chain
validate_invalidation_chain(
    facts=facts,
    expected_chain=doc['expected_invalidations']
)

# Validate performance
validate_performance(
    latency_ms=execution_time,
    baseline_ms=1000,
    max_overhead=2.0  # 2x baseline
)
```

### Performance Baselines

```python
from tests.fixtures.performance_baselines import (
    SMALL_DOCUMENT,
    MEDIUM_DOCUMENT,
    LARGE_DOCUMENT
)

# Use in performance tests
async def test_small_document_performance():
    doc = SMALL_DOCUMENT

    start = time.time()
    facts = await extract_atomic_statements(doc['text'], chunk_id)
    latency = (time.time() - start) * 1000

    # Validate against baseline
    assert latency < doc['expected_latency_ms']
    assert len(facts) >= doc['min_facts']
```

## Performance Testing

### Performance Targets

| Component | Target | How to Measure |
|-----------|--------|----------------|
| Atomic extraction | <500ms/chunk | Time `extract_atomic_statements()` |
| Classification | <200ms/10 facts | Time `classify_atomic_facts_temporally()` |
| Invalidation check | <100ms/fact | Time `find_conflicting_facts()` |
| Total overhead | <2x base pipeline | Compare full pipeline with/without atomic extraction |

### Running Performance Tests

```bash
# Run all performance tests
pytest tests/e2e/test_temporal_cascade_performance.py -v -s

# Run specific performance test
pytest tests/e2e/test_temporal_cascade_performance.py::test_small_document_performance -v -s

# Generate performance report
pytest tests/e2e/test_temporal_cascade_performance.py -v -s --html=performance_report.html
```

### Measuring Performance

```python
import time

async def measure_extraction_performance():
    doc = load_temporal_document("static_replacement")

    # Measure extraction
    start = time.time()
    facts = await extract_atomic_statements(doc['text'], chunk_id, n_rounds=2)
    extraction_time = (time.time() - start) * 1000

    print(f"Extraction: {extraction_time:.2f}ms for {len(facts)} facts")

    # Measure classification
    start = time.time()
    classified = await classify_atomic_facts_temporally(facts)
    classification_time = (time.time() - start) * 1000

    print(f"Classification: {classification_time:.2f}ms for {len(facts)} facts")

    total = extraction_time + classification_time
    print(f"Total: {total:.2f}ms")

    # Check target
    assert total < doc['expected_latency_ms'], f"Performance target missed: {total}ms > {doc['expected_latency_ms']}ms"
```

### Performance Debugging

If performance tests fail:

1. **Check LLM latency**:
   ```python
   # Add timing to LLM calls
   from cognee.infrastructure.llm import get_llm_client

   start = time.time()
   response = await llm.acreate_structured_output(...)
   llm_latency = (time.time() - start) * 1000
   print(f"LLM call: {llm_latency:.2f}ms")
   ```

2. **Profile with cProfile**:
   ```bash
   python -m cProfile -o profile.stats your_test.py
   python -m pstats profile.stats
   ```

3. **Check batch sizes**:
   ```bash
   # Increase batch size for faster classification
   export ATOMIC_CLASSIFICATION_BATCH_SIZE=20
   ```

4. **Reduce extraction rounds**:
   ```bash
   # Faster but may miss pronoun resolutions
   export ATOMIC_EXTRACTION_ROUNDS=1
   ```

## Creating New Tests

### Unit Test Template

```python
import pytest
from cognee.modules.engine.models.AtomicFact import AtomicFact, FactType, TemporalType
from cognee.tasks.graph.cascade_extract.utils.extract_atomic_facts import extract_atomic_statements

@pytest.mark.asyncio
async def test_your_feature():
    """Test description."""
    # Arrange
    text = "John works at Google."
    chunk_id = uuid4()

    # Act
    facts = await extract_atomic_statements(text, chunk_id)

    # Assert
    assert len(facts) > 0
    assert facts[0].subject == "John"
    assert facts[0].predicate == "works at"
    assert facts[0].object == "Google"
```

### Integration Test Template

```python
import pytest
from cognee.tasks.graph import extract_graph_from_data
from cognee.modules.chunking.models.DocumentChunk import DocumentChunk

@pytest.mark.asyncio
async def test_pipeline_integration():
    """Test atomic extraction in pipeline."""
    # Arrange
    chunk = DocumentChunk(
        text="John works at Google.",
        chunk_id=uuid4(),
        document_id=uuid4()
    )

    # Act
    processed = await extract_graph_from_data([chunk])

    # Assert
    assert len(processed) > 0
    atomic_facts = [f for f in processed[0].contains if isinstance(f, AtomicFact)]
    assert len(atomic_facts) > 0
```

### E2E Test Template

```python
import pytest
from tests.fixtures.temporal_documents import load_temporal_document
from tests.fixtures.fixture_utils import validate_fact_extraction

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_end_to_end_extraction():
    """Test complete extraction pipeline with real LLM."""
    # Load fixture
    doc = load_temporal_document("static_replacement")

    # Create chunk
    chunk = DocumentChunk(
        text=doc['text'],
        chunk_id=uuid4(),
        document_id=uuid4()
    )

    # Run pipeline
    processed = await extract_graph_from_data([chunk])

    # Extract atomic facts
    atomic_facts = [f for f in processed[0].contains if isinstance(f, AtomicFact)]

    # Validate
    validate_fact_extraction(atomic_facts, doc['expected_facts'])
```

### Performance Test Template

```python
import pytest
import time
from tests.fixtures.performance_baselines import SMALL_DOCUMENT

@pytest.mark.performance
@pytest.mark.asyncio
async def test_extraction_performance():
    """Test extraction meets performance target."""
    doc = SMALL_DOCUMENT

    # Measure
    start = time.time()
    facts = await extract_atomic_statements(doc['text'], uuid4())
    latency = (time.time() - start) * 1000

    # Validate
    assert latency < doc['expected_latency_ms'], \
        f"Performance target missed: {latency:.2f}ms > {doc['expected_latency_ms']}ms"
    assert len(facts) >= doc['min_facts']
```

## Troubleshooting

### Common Issues

#### 1. Tests Fail with "LLM_API_KEY not set"

**Solution**:
```bash
export LLM_API_KEY="your-api-key"
# Or use .env file
echo "LLM_API_KEY=your-api-key" >> .env
```

#### 2. E2E Tests Take Too Long

**Solution**:
```bash
# Run only unit tests
pytest tests/unit -v -k "atomic"

# Or increase timeout
pytest tests/e2e -v --timeout=300
```

#### 3. Performance Tests Fail

**Possible Causes**:
- LLM latency higher than expected
- Network issues
- Incorrect baseline

**Solution**:
```python
# Debug by printing actual latency
print(f"Actual: {latency:.2f}ms, Expected: {expected:.2f}ms")

# Adjust baseline if needed
SMALL_DOCUMENT['expected_latency_ms'] = 1200  # Increase from 1100
```

#### 4. Fixture Not Found

**Solution**:
```bash
# Check fixture exists
ls tests/fixtures/temporal_documents.py

# Check imports
from tests.fixtures.temporal_documents import load_temporal_document
```

#### 5. Graph DB Connection Errors

**Known Issue**: Graph DB queries are placeholders

**Workaround**:
- Skip tests that require graph DB
- Or implement graph DB queries first

```python
@pytest.mark.skip(reason="Graph DB queries not implemented")
async def test_conflict_detection():
    ...
```

## Best Practices

1. **Always use fixtures** for test data instead of hardcoding
2. **Mock LLM calls in unit tests** to avoid API costs
3. **Use real LLM in E2E tests** to validate quality
4. **Measure performance** with consistent test environment
5. **Add descriptive test names** that explain what is being tested
6. **Use parametrize** for testing multiple scenarios
7. **Clean up resources** after tests (database, files, etc.)

## Example: Complete Test Workflow

```bash
# 1. Run unit tests (fast, no LLM needed)
pytest tests/unit -v -k "atomic" -s

# 2. Run integration tests (medium speed)
pytest tests/integration -v -k "atomic" -s

# 3. Run E2E tests (slow, requires LLM)
export LLM_API_KEY="your-key"
pytest tests/e2e -v -s

# 4. Check coverage
pytest tests/ -v -k "atomic" --cov=cognee --cov-report=html
open htmlcov/index.html

# 5. Generate report
pytest tests/ -v -k "atomic" --html=report.html --self-contained-html
```

## Additional Resources

- **Test Fixtures**: `tests/fixtures/temporal_documents.py`
- **Validation Utilities**: `tests/fixtures/fixture_utils.py`
- **Performance Baselines**: `tests/fixtures/performance_baselines.py`
- **E2E Report**: `.claude/session_context/2025-10-10/e2e_validation_report.md`
