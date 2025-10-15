# Temporal Cascade Test Fixtures

Comprehensive test fixtures for E2E validation of the temporal cascade feature (atomic fact extraction, classification, conflict detection, and graph construction).

## Overview

This directory contains:
- **6 test documents** covering all temporal patterns
- **Expected outputs** for fact extraction and classification
- **Expected graph structures** for validation
- **Performance baselines** for 3 document sizes
- **Validation utilities** with fuzzy matching

## Quick Start

```python
from tests.fixtures import (
    load_temporal_document,
    load_expected_output,
    validate_fact_extraction,
    validate_invalidation_chain,
    validate_graph_structure,
    validate_performance,
)

# 1. Load test data
text = load_temporal_document("static_replacement")
expected = load_expected_output("static_replacement")

# 2. Run your pipeline
facts = await extract_and_classify(text, chunk_id)

# 3. Validate results
result = validate_fact_extraction(facts, expected)
assert result["passed"], result["errors"]
```

## Test Documents

### 1. static_replacement
**Pattern**: STATIC→STATIC invalidation
**Example**: CEO succession (John Smith → Jane Doe)
**Tests**: Fact replacement, invalidation chain creation, temporal sequences

### 2. dynamic_coexistence
**Pattern**: DYNAMIC facts coexist (no invalidation)
**Example**: Stock prices at different times
**Tests**: Time-series data, precise timestamps, no conflict detection

### 3. mixed_facts
**Pattern**: All fact types in one document
**Example**: ATEMPORAL (water boils at 100°C), OPINION (Python is best), PREDICTION (GPT-5 release), FACT (Q4 revenue)
**Tests**: Fact type classification, confidence scoring

### 4. complex_decomposition
**Pattern**: Multi-event extraction from single sentence
**Example**: "John, who works at Google, lives in SF with Sarah"
**Tests**: Pronoun resolution, nested relationships, implicit facts

### 5. temporal_sequence
**Pattern**: Sequential replacements creating invalidation chain
**Example**: Headquarters moved Palo Alto → Menlo Park → Sunnyvale → San Jose
**Tests**: Invalidation chains (A→B→C→D), temporal ordering

### 6. confidence_override
**Pattern**: Higher confidence fact supersedes lower confidence
**Example**: Preliminary report ($500M) vs Official filing ($487M)
**Tests**: Confidence-based conflict resolution

## Performance Baselines

Three document sizes for performance validation:

| Size   | Words | Facts | Expected Time | Max Acceptable (2x) |
|--------|-------|-------|---------------|---------------------|
| Small  | 52    | 5     | 550ms         | 1100ms              |
| Medium | 289   | 28    | 1000ms        | 2000ms              |
| Large  | 1085  | 115   | 2680ms        | 5360ms              |

**Usage**:
```python
from tests.fixtures import get_baseline_document, validate_performance

text = get_baseline_document("small")
# ... run pipeline ...
result = validate_performance(elapsed_ms, fact_count, "small")
assert result["passed"], f"Exceeded 2x overhead: {result['overhead_multiplier']}"
```

## Validation Utilities

### Fact Extraction Validation
```python
validate_fact_extraction(actual_facts, expected)
```
**Checks**:
- Minimum fact count met
- Critical facts present (fuzzy matching)
- Fact types correct (FACT, OPINION, PREDICTION)
- Temporal types correct (ATEMPORAL, STATIC, DYNAMIC)
- Confidence scores in expected ranges

**Fuzzy Matching**: Handles LLM variation
- "John Smith became CEO" matches "John Smith was appointed as CEO"
- "merger deal" matches "acquisition"

### Invalidation Validation
```python
validate_invalidation_chain(facts, expected_count)
```
**Checks**:
- Correct number of invalidations
- Timestamp consistency (invalidated_at ≥ valid_from)
- expired_at set for invalidated facts
- No circular invalidations (A→B→A)

**Output**: Builds invalidation chains automatically

### Graph Structure Validation
```python
validate_graph_structure(nodes, edges, doc_name)
```
**Checks**:
- Minimum entity nodes present
- Minimum predicate edges present
- Exact invalidation edge count
- Edge properties correct

**Note**: Uses minimums (not exact counts) due to entity deduplication variance

### Performance Validation
```python
validate_performance(time_ms, fact_count, doc_size)
```
**Checks**:
- Total time ≤ 2x expected
- Fact count within ±30% of expected

**Output**: Overhead multiplier, warnings for approaching limits

## File Structure

```
tests/fixtures/
├── README.md                       (this file)
├── __init__.py                     (package exports)
├── temporal_documents.py           (6 test documents with expected outputs)
├── expected_graphs.py              (graph structure specifications)
├── performance_baselines.py        (3 baseline documents with timing)
└── fixture_utils.py                (validation helper functions)
```

## Design Principles

### 1. Fuzzy Matching
LLM extraction is non-deterministic, so fixtures use flexible matching:
- Subject/predicate/object use "contains" matching
- Confidence uses ranges (min/max) instead of exact values
- Graph validation uses minimum counts

### 2. Minimum Thresholds
Expect at least N facts/nodes/edges, not exactly N:
- **Reason**: LLM may extract more facts in multi-round extraction
- **Solution**: Validate critical facts are present, warn on excess

### 3. Clear Error Messages
Validation failures clearly indicate what broke:
```python
{
    "passed": False,
    "errors": [
        "Missing critical fact: (John Smith, is CEO of, TechCorp)",
        "Invalidation count mismatch: expected 1, got 0"
    ],
    "warnings": [
        "Fact count deviation >30%: expected 5, got 8"
    ]
}
```

## Testing Recommendations

### Priority 1: Core Functionality (MUST PASS)
1. `static_replacement` - Validates STATIC→STATIC invalidation
2. `dynamic_coexistence` - Validates DYNAMIC coexistence (no invalidation)
3. `temporal_sequence` - Validates invalidation chains

### Priority 2: Edge Cases
4. `mixed_facts` - Validates all fact type classifications
5. `complex_decomposition` - Validates multi-event extraction
6. `confidence_override` - Validates confidence-based resolution

### Priority 3: Performance
7. Small baseline (5 facts, <1100ms)
8. Medium baseline (28 facts, <2000ms)
9. Large baseline (115 facts, <5360ms)

## Example E2E Test

```python
import pytest
from tests.fixtures import (
    load_temporal_document,
    load_expected_output,
    validate_fact_extraction,
    validate_invalidation_chain,
    validate_graph_structure,
)

@pytest.mark.asyncio
async def test_static_replacement_e2e():
    # 1. Load test data
    text = load_temporal_document("static_replacement")
    expected = load_expected_output("static_replacement")

    # 2. Run pipeline
    chunk_id = create_test_chunk(text)
    facts = await extract_atomic_facts(text, chunk_id)
    facts = await classify_facts_temporally(facts)
    facts = await detect_and_invalidate_conflicts(facts)
    graph = await build_graph(facts)

    # 3. Validate facts
    fact_result = validate_fact_extraction(facts, expected)
    assert fact_result["passed"], fact_result["errors"]

    # 4. Validate invalidations
    inv_result = validate_invalidation_chain(facts, expected["invalidation_count"])
    assert inv_result["passed"], inv_result["errors"]

    # 5. Validate graph
    graph_result = validate_graph_structure(graph.nodes, graph.edges, "static_replacement")
    assert graph_result["passed"], graph_result["errors"]
```

## Known Limitations

### 1. Subject Synonymy
Fuzzy matching may not catch all synonyms:
- "company" vs "organization" may NOT match
- **Mitigation**: Use contains-based matching in expected facts

### 2. Graph Structure Variance
Exact node count depends on entity resolution implementation:
- **Mitigation**: Validate minimum counts, not exact

### 3. LLM Non-Determinism
Same text may produce different fact counts across runs:
- **Mitigation**: Validate critical facts are present, not total count

## Contributing

When adding new test documents:
1. Add document text and expected output to `temporal_documents.py`
2. Add graph structure to `expected_graphs.py`
3. Document the temporal pattern being tested
4. Add validation test in E2E suite

## Support

For questions or issues with fixtures:
- See work log: `.ai_agents/session_context/2025-10-10/agent_validation_prep_worklog.md`
- See summary: `.ai_agents/session_context/2025-10-10/docs/validation_prep_summary.md`
