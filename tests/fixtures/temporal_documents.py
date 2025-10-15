# ABOUTME: Comprehensive temporal test documents for E2E validation of atomic fact extraction
# ABOUTME: Each document tests specific temporal patterns (STATIC replacement, DYNAMIC coexistence, mixed types)

from typing import Dict, List, Any
from datetime import datetime, timezone


# ==============================================================================
# Document 1: CEO Succession - STATIC Replacement Pattern
# ==============================================================================
# Tests: STATIC→STATIC invalidation when facts conflict
# Expected behavior: Old CEO fact should be invalidated by new CEO fact

STATIC_REPLACEMENT_DOC = """
TechCorp Incorporated was founded in 2010 by Sarah Chen and Michael Rodriguez.
John Smith became CEO in January 2015, leading the company through rapid growth.
Under his leadership, TechCorp expanded from 50 to 500 employees.
In March 2024, Jane Doe was appointed as the new CEO, replacing John Smith
who moved to an advisory role on the board of directors.
"""

STATIC_REPLACEMENT_EXPECTED = {
    "description": "CEO succession creates STATIC→STATIC replacement with invalidation",
    "min_facts": 5,  # founded by, became CEO, expanded, appointed CEO, moved to advisory
    "critical_facts": [
        {
            "subject": "John Smith",
            "predicate": "was CEO of",
            "object": "TechCorp",
            "fact_type": "FACT",
            "temporal_type": "STATIC",
            "valid_from": "2015-01",
            "valid_until": "2024-03",
            "should_be_invalidated": True,
            "invalidated_by_triplet": ("Jane Doe", "is CEO of", "TechCorp"),
        },
        {
            "subject": "Jane Doe",
            "predicate": "is CEO of",
            "object": "TechCorp",
            "fact_type": "FACT",
            "temporal_type": "STATIC",
            "valid_from": "2024-03",
            "is_open_interval": True,
            "should_invalidate": ("John Smith", "CEO", "TechCorp"),
        },
    ],
    "invalidation_count": 1,
    "test_focus": [
        "STATIC fact replacement",
        "Temporal sequence detection (2015 → 2024)",
        "Invalidation chain creation",
        "Open interval for current CEO",
    ],
}


# ==============================================================================
# Document 2: Stock Prices - DYNAMIC Coexistence Pattern
# ==============================================================================
# Tests: DYNAMIC facts coexist without invalidating each other
# Expected behavior: All price snapshots remain valid with distinct timestamps

DYNAMIC_COEXISTENCE_DOC = """
Tesla's stock (TSLA) opened at $250.00 on January 2, 2024 at 9:30 AM EST.
Trading was active in the morning session. By 10:00 AM, the price had risen
to $252.50 as buyers entered the market. Midday trading saw continued momentum.
At market close (4:00 PM EST), Tesla stock was trading at $255.75,
representing a gain of 2.3% for the day.
"""

DYNAMIC_COEXISTENCE_EXPECTED = {
    "description": "Stock prices create DYNAMIC facts that coexist without invalidation",
    "min_facts": 3,  # Three distinct price points
    "critical_facts": [
        {
            "subject": "Tesla stock",
            "predicate": "price was",
            "object": "$250.00",
            "fact_type": "FACT",
            "temporal_type": "DYNAMIC",
            "valid_from": "2024-01-02T09:30",
            "valid_until": "2024-01-02T10:00",
            "should_be_invalidated": False,
        },
        {
            "subject": "Tesla stock",
            "predicate": "price was",
            "object": "$252.50",
            "fact_type": "FACT",
            "temporal_type": "DYNAMIC",
            "valid_from": "2024-01-02T10:00",
            "valid_until": "2024-01-02T16:00",
            "should_be_invalidated": False,
        },
        {
            "subject": "Tesla stock",
            "predicate": "price was",
            "object": "$255.75",
            "fact_type": "FACT",
            "temporal_type": "DYNAMIC",
            "valid_from": "2024-01-02T16:00",
            "is_open_interval": False,  # Specific point in time
            "should_be_invalidated": False,
        },
    ],
    "invalidation_count": 0,  # DYNAMIC facts don't invalidate each other
    "test_focus": [
        "DYNAMIC fact coexistence",
        "Precise timestamp preservation",
        "No invalidation between snapshots",
        "Time-ordered sequence validation",
    ],
}


# ==============================================================================
# Document 3: Mixed Fact Types - Classification Edge Cases
# ==============================================================================
# Tests: ATEMPORAL, OPINION, PREDICTION, and regular FACT classification
# Expected behavior: Correct fact_type and temporal_type for each statement

MIXED_FACTS_DOC = """
Water boils at 100 degrees Celsius at sea level, a fundamental physical property.
I believe Python is the best programming language for data science applications.
The new GPT-5 AI model will likely be released in Q4 2025, according to industry analysts.
The company reported Q4 2023 revenue of $10 million, marking a 25% increase year-over-year.
"""

MIXED_FACTS_EXPECTED = {
    "description": "Mixed statement types test fact_type and temporal_type classification",
    "min_facts": 4,
    "critical_facts": [
        {
            "subject": "Water",
            "predicate": "boils at",
            "object": "100 degrees Celsius",
            "fact_type": "FACT",
            "temporal_type": "ATEMPORAL",  # Timeless physical law
            "confidence_min": 0.9,
            "is_open_interval": False,
        },
        {
            "subject": "Python",
            "predicate": "is best for",
            "object": "data science",
            "fact_type": "OPINION",  # Subjective judgment
            "temporal_type": "STATIC",  # Opinions can change but slowly
            "confidence_max": 0.8,  # Lower confidence for opinions
        },
        {
            "subject": "GPT-5",
            "predicate": "will be released",
            "object": "Q4 2025",
            "fact_type": "PREDICTION",  # Future claim
            "temporal_type": "DYNAMIC",  # Future events are dynamic
            "confidence_max": 0.7,  # Predictions have lower confidence
        },
        {
            "subject": "company",
            "predicate": "reported revenue of",
            "object": "$10 million",
            "fact_type": "FACT",
            "temporal_type": "STATIC",  # Historical fact, doesn't change
            "valid_from": "2023-Q4",
            "confidence_min": 0.85,
        },
    ],
    "invalidation_count": 0,  # Different fact types, no conflicts
    "test_focus": [
        "ATEMPORAL fact detection (physical laws)",
        "OPINION classification (subjective statements)",
        "PREDICTION detection (future claims)",
        "Confidence scoring variation by fact type",
    ],
}


# ==============================================================================
# Document 4: Complex Multi-Event Decomposition
# ==============================================================================
# Tests: Pronoun resolution, nested relationships, implicit facts
# Expected behavior: Single sentence decomposes into multiple atomic facts

COMPLEX_SENTENCE_DOC = """
John Smith, who works as a senior engineer at Google in Mountain View, California,
lives in San Francisco with his wife Sarah and their two children. He commutes
daily via Caltrain, which takes approximately 45 minutes each way.
"""

COMPLEX_DECOMPOSITION_EXPECTED = {
    "description": "Complex sentence with nested relationships tests decomposition and pronoun resolution",
    "min_facts": 6,  # Multiple implicit relationships
    "critical_facts": [
        {
            "subject": "John Smith",
            "predicate": "works at",
            "object": "Google",
            "fact_type": "FACT",
            "temporal_type": "STATIC",
        },
        {
            "subject": "John Smith",
            "predicate": "has role",
            "object": "senior engineer",
            "fact_type": "FACT",
            "temporal_type": "STATIC",
        },
        {
            "subject": "Google",
            "predicate": "located in",
            "object": "Mountain View",
            "fact_type": "FACT",
            "temporal_type": "STATIC",
        },
        {
            "subject": "John Smith",
            "predicate": "lives in",
            "object": "San Francisco",
            "fact_type": "FACT",
            "temporal_type": "STATIC",
        },
        {
            "subject": "John Smith",
            "predicate": "married to",
            "object": "Sarah",
            "fact_type": "FACT",
            "temporal_type": "STATIC",
        },
        {
            "subject": "John Smith",
            "predicate": "commutes via",
            "object": "Caltrain",
            "fact_type": "FACT",
            "temporal_type": "STATIC",
        },
    ],
    "invalidation_count": 0,
    "test_focus": [
        "Multi-event decomposition (single sentence → many facts)",
        "Pronoun resolution (He → John Smith)",
        "Nested relationship extraction",
        "Implicit fact discovery",
    ],
}


# ==============================================================================
# Document 5: Temporal Sequence - Multiple Invalidations
# ==============================================================================
# Tests: Sequential replacements creating invalidation chains
# Expected behavior: Each new fact invalidates the previous one

TEMPORAL_SEQUENCE_DOC = """
The company's headquarters was initially located in a garage in Palo Alto in 2010.
In 2015, they moved to a small office building in Menlo Park to accommodate growth.
By 2020, rapid expansion required relocating to a large campus in Sunnyvale.
As of 2024, the company operates from its current headquarters in downtown San Jose.
"""

TEMPORAL_SEQUENCE_EXPECTED = {
    "description": "Sequential location changes create invalidation chain",
    "min_facts": 4,
    "critical_facts": [
        {
            "subject": "headquarters",
            "predicate": "located in",
            "object": "Palo Alto",
            "valid_from": "2010",
            "valid_until": "2015",
            "should_be_invalidated": True,
        },
        {
            "subject": "headquarters",
            "predicate": "located in",
            "object": "Menlo Park",
            "valid_from": "2015",
            "valid_until": "2020",
            "should_be_invalidated": True,
        },
        {
            "subject": "headquarters",
            "predicate": "located in",
            "object": "Sunnyvale",
            "valid_from": "2020",
            "valid_until": "2024",
            "should_be_invalidated": True,
        },
        {
            "subject": "headquarters",
            "predicate": "located in",
            "object": "San Jose",
            "valid_from": "2024",
            "is_open_interval": True,
            "should_be_invalidated": False,  # Current location
        },
    ],
    "invalidation_count": 3,  # Three historical facts invalidated
    "test_focus": [
        "Sequential STATIC replacements",
        "Invalidation chain (A→B→C→D)",
        "Temporal ordering preservation",
        "Current fact has open interval",
    ],
}


# ==============================================================================
# Document 6: Confidence Overrides - Same Subject-Predicate
# ==============================================================================
# Tests: Higher confidence fact supersedes lower confidence fact
# Expected behavior: Conflict resolution based on confidence scores

CONFIDENCE_OVERRIDE_DOC = """
According to preliminary reports, the merger deal was valued at approximately $500 million.
However, the official SEC filing confirmed the acquisition price was exactly $487 million.
"""

CONFIDENCE_OVERRIDE_EXPECTED = {
    "description": "Higher confidence fact (official filing) supersedes lower confidence fact (preliminary report)",
    "min_facts": 2,
    "critical_facts": [
        {
            "subject": "merger deal",
            "predicate": "valued at",
            "object": "$500 million",
            "fact_type": "FACT",
            "temporal_type": "STATIC",
            "confidence_max": 0.7,  # Preliminary report
            "should_be_invalidated": True,
        },
        {
            "subject": "acquisition",
            "predicate": "priced at",
            "object": "$487 million",
            "fact_type": "FACT",
            "temporal_type": "STATIC",
            "confidence_min": 0.9,  # Official filing
            "should_invalidate": ("merger", "valued at", "$500 million"),
        },
    ],
    "invalidation_count": 1,
    "test_focus": [
        "Confidence-based conflict resolution",
        "Official source supersedes preliminary",
        "Subject synonymy (merger deal = acquisition)",
    ],
}


# ==============================================================================
# Helper Functions
# ==============================================================================

def get_all_test_documents() -> Dict[str, tuple]:
    """
    Get all test documents with their expected outputs.

    Returns:
        Dictionary mapping document name to (text, expected) tuples
    """
    return {
        "static_replacement": (STATIC_REPLACEMENT_DOC, STATIC_REPLACEMENT_EXPECTED),
        "dynamic_coexistence": (DYNAMIC_COEXISTENCE_DOC, DYNAMIC_COEXISTENCE_EXPECTED),
        "mixed_facts": (MIXED_FACTS_DOC, MIXED_FACTS_EXPECTED),
        "complex_decomposition": (COMPLEX_SENTENCE_DOC, COMPLEX_DECOMPOSITION_EXPECTED),
        "temporal_sequence": (TEMPORAL_SEQUENCE_DOC, TEMPORAL_SEQUENCE_EXPECTED),
        "confidence_override": (CONFIDENCE_OVERRIDE_DOC, CONFIDENCE_OVERRIDE_EXPECTED),
    }


def get_document(name: str) -> str:
    """
    Get test document by name.

    Args:
        name: Document identifier (e.g., "static_replacement")

    Returns:
        Document text

    Raises:
        KeyError: If document name not found
    """
    docs = get_all_test_documents()
    if name not in docs:
        raise KeyError(
            f"Document '{name}' not found. Available: {list(docs.keys())}"
        )
    return docs[name][0]


def get_expected(name: str) -> Dict[str, Any]:
    """
    Get expected output structure for a test document.

    Args:
        name: Document identifier (e.g., "static_replacement")

    Returns:
        Expected output dictionary with critical_facts, invalidation_count, etc.

    Raises:
        KeyError: If document name not found
    """
    docs = get_all_test_documents()
    if name not in docs:
        raise KeyError(
            f"Document '{name}' not found. Available: {list(docs.keys())}"
        )
    return docs[name][1]


def get_document_summary() -> str:
    """
    Get human-readable summary of all test documents.

    Returns:
        Formatted string listing all documents and their purposes
    """
    docs = get_all_test_documents()
    lines = ["Available Test Documents:", "=" * 60]

    for name, (text, expected) in docs.items():
        lines.append(f"\n{name.upper()}")
        lines.append(f"  Description: {expected['description']}")
        lines.append(f"  Min Facts: {expected['min_facts']}")
        lines.append(f"  Invalidations: {expected['invalidation_count']}")
        lines.append(f"  Focus: {', '.join(expected['test_focus'][:2])}")

    return "\n".join(lines)
