# ABOUTME: Helper utilities for E2E temporal cascade testing and validation
# ABOUTME: Provides functions to load fixtures, validate facts, and compare graph structures

from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from uuid import UUID
import re
from datetime import datetime, timezone

# Lazy import to avoid circular dependencies and module initialization issues
if TYPE_CHECKING:
    from cognee.modules.engine.models.AtomicFact import AtomicFact, FactType, TemporalType


# ==============================================================================
# Document Loading
# ==============================================================================

def load_temporal_document(doc_name: str) -> str:
    """
    Load test document by name from temporal_documents.py.

    Args:
        doc_name: Document identifier (e.g., "static_replacement", "dynamic_coexistence")

    Returns:
        Document text as string

    Raises:
        ImportError: If temporal_documents module cannot be imported
        KeyError: If document name not found

    Example:
        >>> text = load_temporal_document("static_replacement")
        >>> assert "TechCorp" in text
    """
    try:
        from tests.fixtures.temporal_documents import get_document
        return get_document(doc_name)
    except ImportError as e:
        raise ImportError(
            f"Cannot import temporal_documents: {e}. "
            "Ensure tests/fixtures/temporal_documents.py exists."
        )


def load_expected_output(doc_name: str) -> Dict[str, Any]:
    """
    Load expected output structure for a test document.

    Args:
        doc_name: Document identifier

    Returns:
        Dictionary with expected facts, invalidations, and metadata

    Raises:
        ImportError: If temporal_documents module cannot be imported
        KeyError: If document name not found

    Example:
        >>> expected = load_expected_output("static_replacement")
        >>> assert expected["invalidation_count"] == 1
    """
    try:
        from tests.fixtures.temporal_documents import get_expected
        return get_expected(doc_name)
    except ImportError as e:
        raise ImportError(
            f"Cannot import temporal_documents: {e}. "
            "Ensure tests/fixtures/temporal_documents.py exists."
        )


def load_expected_graph(doc_name: str) -> Dict[str, Any]:
    """
    Load expected graph structure for a test document.

    Args:
        doc_name: Document identifier

    Returns:
        Dictionary with expected node counts, edge counts, and properties

    Raises:
        ImportError: If expected_graphs module cannot be imported
        KeyError: If document name not found

    Example:
        >>> graph = load_expected_graph("static_replacement")
        >>> assert graph["invalidation_edges"] == 1
    """
    try:
        from tests.fixtures.expected_graphs import get_expected_graph
        return get_expected_graph(doc_name)
    except ImportError as e:
        raise ImportError(
            f"Cannot import expected_graphs: {e}. "
            "Ensure tests/fixtures/expected_graphs.py exists."
        )


# ==============================================================================
# Fact Validation
# ==============================================================================

def validate_fact_extraction(
    actual_facts: List["AtomicFact"],
    expected: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate extracted facts match expected output.

    Performs the following checks:
    - Fact count meets minimum expectations
    - Critical facts are present
    - Fact types are correct (FACT, OPINION, PREDICTION)
    - Temporal types are correct (ATEMPORAL, STATIC, DYNAMIC)
    - Confidence scores are within expected ranges

    Args:
        actual_facts: List of AtomicFact instances from extraction
        expected: Expected output dictionary from load_expected_output()

    Returns:
        Validation result dictionary with:
        - passed: bool
        - errors: List[str]
        - warnings: List[str]
        - matched_facts: List[Dict]
        - missing_facts: List[Dict]

    Example:
        >>> result = validate_fact_extraction(facts, expected)
        >>> assert result["passed"], result["errors"]
    """
    errors = []
    warnings = []
    matched_facts = []
    missing_facts = []

    # Check minimum fact count
    min_facts = expected.get("min_facts", 0)
    if len(actual_facts) < min_facts:
        errors.append(
            f"Insufficient facts extracted: {len(actual_facts)} < {min_facts}"
        )

    # Validate critical facts
    critical_facts = expected.get("critical_facts", [])
    for critical in critical_facts:
        match = _find_matching_fact(actual_facts, critical)
        if match:
            # Validate fact properties
            fact_errors = _validate_fact_properties(match, critical)
            if fact_errors:
                errors.extend(fact_errors)
            else:
                matched_facts.append(critical)
        else:
            missing_facts.append(critical)
            errors.append(
                f"Missing critical fact: ({critical.get('subject')}, "
                f"{critical.get('predicate')}, {critical.get('object')})"
            )

    # Warnings for excess facts
    if len(actual_facts) > min_facts * 1.5:
        warnings.append(
            f"Unusually high fact count: {len(actual_facts)} (expected ~{min_facts})"
        )

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "matched_facts": matched_facts,
        "missing_facts": missing_facts,
        "total_facts": len(actual_facts),
        "expected_min_facts": min_facts,
    }


def _find_matching_fact(
    facts: List["AtomicFact"],
    expected_fact: Dict[str, Any],
) -> Optional["AtomicFact"]:
    """
    Find a fact matching expected subject/predicate/object (fuzzy matching).

    Args:
        facts: List of actual facts
        expected_fact: Expected fact dictionary

    Returns:
        Matching AtomicFact or None
    """
    expected_subject = expected_fact.get("subject", "").lower()
    expected_predicate = expected_fact.get("predicate", "").lower()
    expected_object = expected_fact.get("object", "").lower()

    for fact in facts:
        # Fuzzy match (contains or exact)
        subject_match = (
            expected_subject in fact.subject.lower()
            or fact.subject.lower() in expected_subject
        )
        predicate_match = (
            expected_predicate in fact.predicate.lower()
            or fact.predicate.lower() in expected_predicate
        )
        object_match = (
            expected_object in fact.object.lower()
            or fact.object.lower() in expected_object
        )

        if subject_match and predicate_match and object_match:
            return fact

    return None


def _validate_fact_properties(
    fact: "AtomicFact",
    expected: Dict[str, Any],
) -> List[str]:
    """
    Validate fact properties against expected values.

    Args:
        fact: Actual AtomicFact instance
        expected: Expected properties dictionary

    Returns:
        List of error messages (empty if all valid)
    """
    errors = []

    # Validate fact_type
    if "fact_type" in expected:
        expected_type = expected["fact_type"]
        if fact.fact_type.value != expected_type:
            errors.append(
                f"Fact type mismatch for {fact.subject}: "
                f"expected {expected_type}, got {fact.fact_type.value}"
            )

    # Validate temporal_type
    if "temporal_type" in expected:
        expected_temporal = expected["temporal_type"]
        if fact.temporal_type.value != expected_temporal:
            errors.append(
                f"Temporal type mismatch for {fact.subject}: "
                f"expected {expected_temporal}, got {fact.temporal_type.value}"
            )

    # Validate confidence range
    if "confidence_min" in expected:
        if fact.confidence < expected["confidence_min"]:
            errors.append(
                f"Confidence too low for {fact.subject}: "
                f"{fact.confidence} < {expected['confidence_min']}"
            )

    if "confidence_max" in expected:
        if fact.confidence > expected["confidence_max"]:
            errors.append(
                f"Confidence too high for {fact.subject}: "
                f"{fact.confidence} > {expected['confidence_max']}"
            )

    # Validate is_open_interval
    if "is_open_interval" in expected:
        if fact.is_open_interval != expected["is_open_interval"]:
            errors.append(
                f"is_open_interval mismatch for {fact.subject}: "
                f"expected {expected['is_open_interval']}, got {fact.is_open_interval}"
            )

    # Validate invalidation status
    if expected.get("should_be_invalidated", False):
        if fact.invalidated_by is None:
            errors.append(f"Fact should be invalidated but isn't: {fact.subject}")

    if expected.get("should_be_invalidated", True) is False:
        if fact.invalidated_by is not None:
            errors.append(f"Fact should NOT be invalidated but is: {fact.subject}")

    return errors


# ==============================================================================
# Graph Validation
# ==============================================================================

def validate_graph_structure(
    graph_nodes: List[Any],
    graph_edges: List[Any],
    doc_name: str,
) -> Dict[str, Any]:
    """
    Validate graph structure against expected structure.

    This is a convenience wrapper that calls expected_graphs.validate_graph_structure().

    Args:
        graph_nodes: List of graph nodes
        graph_edges: List of graph edges
        doc_name: Document identifier

    Returns:
        Validation result dictionary

    Example:
        >>> result = validate_graph_structure(nodes, edges, "static_replacement")
        >>> assert result["passed"], result["errors"]
    """
    try:
        from tests.fixtures.expected_graphs import validate_graph_structure as validate
        return validate(graph_nodes, graph_edges, doc_name)
    except ImportError as e:
        return {
            "passed": False,
            "errors": [f"Cannot import expected_graphs: {e}"],
            "warnings": [],
            "stats": {},
        }


# ==============================================================================
# Invalidation Validation
# ==============================================================================

def validate_invalidation_chain(
    facts: List["AtomicFact"],
    expected_invalidations: int,
) -> Dict[str, Any]:
    """
    Validate invalidation relationships between facts.

    Checks:
    - Correct number of invalidations
    - Invalidation timestamps are consistent
    - Invalidated facts have expired_at set
    - No circular invalidations

    Args:
        facts: List of AtomicFact instances
        expected_invalidations: Expected number of invalidation relationships

    Returns:
        Validation result dictionary with:
        - passed: bool
        - errors: List[str]
        - invalidation_count: int
        - chains: List[List[UUID]] (invalidation chains)

    Example:
        >>> result = validate_invalidation_chain(facts, expected_invalidations=2)
        >>> assert result["passed"], result["errors"]
    """
    errors = []
    invalidated_facts = [f for f in facts if f.invalidated_by is not None]
    invalidation_count = len(invalidated_facts)

    # Check count
    if invalidation_count != expected_invalidations:
        errors.append(
            f"Invalidation count mismatch: expected {expected_invalidations}, "
            f"got {invalidation_count}"
        )

    # Validate each invalidated fact
    for fact in invalidated_facts:
        # Should have invalidated_at timestamp
        if fact.invalidated_at is None:
            errors.append(
                f"Fact {fact.id} has invalidated_by but missing invalidated_at"
            )

        # Should have expired_at set
        if fact.expired_at is None:
            errors.append(
                f"Fact {fact.id} is invalidated but missing expired_at"
            )

        # Check temporal consistency
        if fact.invalidated_at and fact.valid_from:
            if fact.invalidated_at < fact.valid_from:
                errors.append(
                    f"Fact {fact.id} invalidated_at ({fact.invalidated_at}) "
                    f"before valid_from ({fact.valid_from})"
                )

    # Detect invalidation chains
    chains = _build_invalidation_chains(facts)

    # Detect circular invalidations
    circular = _detect_circular_invalidations(facts)
    if circular:
        errors.append(f"Circular invalidation detected: {circular}")

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "invalidation_count": invalidation_count,
        "chains": chains,
        "circular_invalidations": circular,
    }


def _build_invalidation_chains(facts: List["AtomicFact"]) -> List[List[UUID]]:
    """
    Build invalidation chains from facts.

    Returns list of chains, where each chain is a list of fact IDs
    ordered from oldest to newest (A→B→C).
    """
    # Build invalidation graph
    invalidations = {}  # old_id -> new_id
    for fact in facts:
        if fact.invalidated_by:
            invalidations[fact.id] = fact.invalidated_by

    # Find chain roots (facts that invalidate others but aren't invalidated)
    all_old = set(invalidations.keys())
    all_new = set(invalidations.values())
    roots = all_old - all_new

    # Build chains from roots
    chains = []
    for root in roots:
        chain = [root]
        current = root
        while current in invalidations:
            next_id = invalidations[current]
            chain.append(next_id)
            current = next_id
        chains.append(chain)

    return chains


def _detect_circular_invalidations(facts: List["AtomicFact"]) -> List[UUID]:
    """
    Detect circular invalidation chains.

    Returns list of fact IDs involved in circular chain, or empty list if none.
    """
    visited = set()
    rec_stack = set()

    def has_cycle(fact_id: UUID, invalidation_map: Dict[UUID, UUID]) -> bool:
        visited.add(fact_id)
        rec_stack.add(fact_id)

        if fact_id in invalidation_map:
            next_id = invalidation_map[fact_id]
            if next_id not in visited:
                if has_cycle(next_id, invalidation_map):
                    return True
            elif next_id in rec_stack:
                return True

        rec_stack.remove(fact_id)
        return False

    # Build invalidation map
    invalidation_map = {f.id: f.invalidated_by for f in facts if f.invalidated_by}

    # Check each fact
    for fact in facts:
        if fact.id not in visited:
            if has_cycle(fact.id, invalidation_map):
                return list(rec_stack)

    return []


# ==============================================================================
# Performance Validation
# ==============================================================================

def validate_performance(
    actual_time_ms: float,
    actual_fact_count: int,
    doc_size: str,
) -> Dict[str, Any]:
    """
    Validate performance against baseline expectations.

    This is a convenience wrapper that calls performance_baselines.validate_performance().

    Args:
        actual_time_ms: Measured processing time in milliseconds
        actual_fact_count: Number of facts extracted
        doc_size: Document size ("small", "medium", or "large")

    Returns:
        Validation result dictionary

    Example:
        >>> result = validate_performance(1200, 6, "small")
        >>> assert result["passed"], f"Exceeded 2x overhead"
    """
    try:
        from tests.fixtures.performance_baselines import validate_performance as validate
        return validate(actual_time_ms, actual_fact_count, doc_size)
    except ImportError as e:
        return {
            "passed": False,
            "errors": [f"Cannot import performance_baselines: {e}"],
            "warnings": [],
        }


# ==============================================================================
# Timestamp Utilities
# ==============================================================================

def parse_timestamp_string(timestamp_str: str) -> Optional[int]:
    """
    Parse timestamp string into milliseconds since epoch.

    Handles formats:
    - ISO dates: "2024-03-15", "2024-03-15T10:30:00"
    - Year-month: "2015-01", "2024-Q4"
    - Year only: "2015", "2020"
    - Special values: "unknown", "open", "now"

    Args:
        timestamp_str: Timestamp string to parse

    Returns:
        Timestamp in milliseconds since epoch, or None for "open"

    Example:
        >>> ts = parse_timestamp_string("2024-03-15")
        >>> assert ts > 0
    """
    if not timestamp_str or timestamp_str.lower() == "unknown":
        return None

    if timestamp_str.lower() == "open":
        return None

    if timestamp_str.lower() == "now":
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    # Try ISO datetime
    iso_patterns = [
        (r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})", True),  # Full datetime
        (r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})", False),  # No seconds
        (r"(\d{4})-(\d{2})-(\d{2})", False),  # Date only
        (r"(\d{4})-(\d{2})", False),  # Year-month
        (r"(\d{4})", False),  # Year only
    ]

    for pattern, has_seconds in iso_patterns:
        match = re.match(pattern, timestamp_str)
        if match:
            groups = match.groups()
            try:
                if len(groups) == 1:  # Year only
                    dt = datetime(int(groups[0]), 1, 1, tzinfo=timezone.utc)
                elif len(groups) == 2:  # Year-month
                    dt = datetime(int(groups[0]), int(groups[1]), 1, tzinfo=timezone.utc)
                elif len(groups) == 3:  # Date only
                    dt = datetime(int(groups[0]), int(groups[1]), int(groups[2]), tzinfo=timezone.utc)
                elif len(groups) == 5:  # No seconds
                    dt = datetime(int(groups[0]), int(groups[1]), int(groups[2]),
                                  int(groups[3]), int(groups[4]), tzinfo=timezone.utc)
                else:  # Full datetime
                    dt = datetime(int(groups[0]), int(groups[1]), int(groups[2]),
                                  int(groups[3]), int(groups[4]), int(groups[5]),
                                  tzinfo=timezone.utc)
                return int(dt.timestamp() * 1000)
            except (ValueError, OverflowError):
                continue

    # If all parsing fails, return None
    return None


def timestamp_to_readable(timestamp_ms: Optional[int]) -> str:
    """
    Convert timestamp in milliseconds to human-readable format.

    Args:
        timestamp_ms: Timestamp in milliseconds since epoch

    Returns:
        Formatted date string or "None" if timestamp is None

    Example:
        >>> readable = timestamp_to_readable(1710460800000)
        >>> assert "2024" in readable
    """
    if timestamp_ms is None:
        return "None"

    try:
        dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, OSError):
        return f"Invalid timestamp: {timestamp_ms}"
