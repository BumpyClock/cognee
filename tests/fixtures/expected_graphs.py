# ABOUTME: Expected graph structures for temporal test documents validation
# ABOUTME: Defines node counts, edge counts, and graph properties for E2E testing

from typing import Dict, Any, List


# ==============================================================================
# Graph Structure Specifications
# ==============================================================================
# Based on AtomicFact graph conversion (from task A3):
# - Each AtomicFact creates 2 entity nodes (subject, object) + 1 predicate edge + 1 metadata node
# - Invalidation creates additional edges between metadata nodes
# - Subject/Object entities may be shared across multiple facts


# ==============================================================================
# Document 1: CEO Succession - STATIC Replacement
# ==============================================================================

STATIC_REPLACEMENT_GRAPH = {
    "description": "CEO succession with one invalidation edge",
    "min_entity_nodes": 4,  # TechCorp, John Smith, Jane Doe, Sarah Chen, Michael Rodriguez
    "min_metadata_nodes": 5,  # One per atomic fact
    "min_predicate_edges": 5,  # subject→object edges for each fact
    "invalidation_edges": 1,  # John's CEO fact → Jane's CEO fact
    "edge_properties": {
        "predicate_edge_has": [
            "fact_id",
            "fact_type",
            "temporal_type",
            "confidence",
            "valid_from",
            "valid_until",
            "source_chunk_id",
        ],
        "invalidation_edge_has": [
            "invalidated_by",
            "invalidated_at",
            "reason",
        ],
    },
    "node_types": {
        "entity_nodes": [
            "TechCorp",
            "John Smith",
            "Jane Doe",
            # Additional entities from founding/expansion facts
        ],
        "metadata_nodes_count": 5,  # One AtomicFact metadata node per fact
    },
    "validation_checks": [
        "John Smith CEO fact has invalidated_by pointing to Jane Doe fact",
        "Jane Doe CEO fact has is_open_interval=True",
        "Invalidation edge exists from old fact metadata to new fact metadata",
        "Both CEO facts share same object entity (TechCorp)",
    ],
}


# ==============================================================================
# Document 2: Stock Prices - DYNAMIC Coexistence
# ==============================================================================

DYNAMIC_COEXISTENCE_GRAPH = {
    "description": "Stock price snapshots with NO invalidations",
    "min_entity_nodes": 2,  # Tesla stock (subject), multiple price objects
    "min_metadata_nodes": 3,  # One per price snapshot
    "min_predicate_edges": 3,  # Three "price was" edges
    "invalidation_edges": 0,  # DYNAMIC facts coexist
    "edge_properties": {
        "all_edges_have": [
            "temporal_type=DYNAMIC",
            "valid_from timestamps differ",
            "valid_until timestamps differ",
        ],
    },
    "node_types": {
        "entity_nodes": [
            "Tesla stock",
            "$250.00",
            "$252.50",
            "$255.75",
        ],
        "metadata_nodes_count": 3,
    },
    "validation_checks": [
        "All facts have temporal_type=DYNAMIC",
        "No invalidated_by fields set",
        "Timestamps form chronological sequence",
        "Subject entity (Tesla stock) is shared across all facts",
    ],
}


# ==============================================================================
# Document 3: Mixed Fact Types
# ==============================================================================

MIXED_FACTS_GRAPH = {
    "description": "Diverse fact types with different temporal classifications",
    "min_entity_nodes": 6,  # Water, 100°C, Python, data science, GPT-5, Q4 2025, company, $10M
    "min_metadata_nodes": 4,  # One per fact
    "min_predicate_edges": 4,  # One per fact
    "invalidation_edges": 0,  # No conflicts
    "edge_properties": {
        "temporal_type_diversity": [
            "ATEMPORAL (water boiling)",
            "STATIC (Python opinion, revenue)",
            "DYNAMIC (GPT-5 prediction)",
        ],
        "fact_type_diversity": [
            "FACT (water, revenue)",
            "OPINION (Python)",
            "PREDICTION (GPT-5)",
        ],
    },
    "node_types": {
        "entity_nodes": [
            "Water",
            "100 degrees Celsius",
            "Python",
            "data science",
            "GPT-5",
            "Q4 2025",
            "company",
            "$10 million",
        ],
        "metadata_nodes_count": 4,
    },
    "validation_checks": [
        "ATEMPORAL fact has no valid_until (or very distant future)",
        "OPINION has confidence < 0.9",
        "PREDICTION has confidence < 0.8",
        "Each fact has distinct fact_type and temporal_type combination",
    ],
}


# ==============================================================================
# Document 4: Complex Multi-Event Decomposition
# ==============================================================================

COMPLEX_DECOMPOSITION_GRAPH = {
    "description": "Single sentence decomposes into multiple facts sharing entities",
    "min_entity_nodes": 8,  # John Smith, Google, senior engineer, Mountain View, San Francisco, Sarah, Caltrain, 45 minutes
    "min_metadata_nodes": 6,  # One per extracted fact
    "min_predicate_edges": 6,  # Multiple relationships
    "invalidation_edges": 0,  # No conflicts
    "edge_properties": {
        "shared_subject": "John Smith appears as subject in multiple edges",
        "predicates": [
            "works at",
            "has role",
            "lives in",
            "married to",
            "commutes via",
            "located in",
        ],
    },
    "node_types": {
        "entity_nodes": [
            "John Smith",  # Appears in multiple facts
            "Google",
            "senior engineer",
            "Mountain View",
            "San Francisco",
            "Sarah",
            "Caltrain",
        ],
        "metadata_nodes_count": 6,
    },
    "validation_checks": [
        "John Smith entity is subject in at least 4 facts",
        "All facts have temporal_type=STATIC",
        "Google entity appears as both object and subject",
        "Pronoun 'He' was resolved to 'John Smith'",
    ],
}


# ==============================================================================
# Document 5: Temporal Sequence - Invalidation Chain
# ==============================================================================

TEMPORAL_SEQUENCE_GRAPH = {
    "description": "Sequential replacements create invalidation chain (A→B→C→D)",
    "min_entity_nodes": 5,  # headquarters, Palo Alto, Menlo Park, Sunnyvale, San Jose
    "min_metadata_nodes": 4,  # One per location fact
    "min_predicate_edges": 4,  # Four "located in" facts
    "invalidation_edges": 3,  # Three invalidation edges
    "edge_properties": {
        "invalidation_chain": [
            "Palo Alto fact → invalidated by Menlo Park fact",
            "Menlo Park fact → invalidated by Sunnyvale fact",
            "Sunnyvale fact → invalidated by San Jose fact",
            "San Jose fact → NOT invalidated (current)",
        ],
    },
    "node_types": {
        "entity_nodes": [
            "headquarters",  # Shared subject
            "Palo Alto",
            "Menlo Park",
            "Sunnyvale",
            "San Jose",
        ],
        "metadata_nodes_count": 4,
    },
    "validation_checks": [
        "Three facts have invalidated_by set (2010, 2015, 2020 locations)",
        "Current fact (2024) has is_open_interval=True",
        "Valid_from timestamps form chronological sequence",
        "Each valid_until matches next fact's valid_from",
    ],
}


# ==============================================================================
# Document 6: Confidence Override
# ==============================================================================

CONFIDENCE_OVERRIDE_GRAPH = {
    "description": "Higher confidence fact supersedes lower confidence fact",
    "min_entity_nodes": 4,  # merger deal, $500M, acquisition, $487M
    "min_metadata_nodes": 2,  # Two conflicting facts
    "min_predicate_edges": 2,  # Two valuation facts
    "invalidation_edges": 1,  # Official supersedes preliminary
    "edge_properties": {
        "confidence_comparison": "Official filing (0.9+) > Preliminary report (<0.7)",
    },
    "node_types": {
        "entity_nodes": [
            "merger deal",
            "$500 million",
            "acquisition",
            "$487 million",
        ],
        "metadata_nodes_count": 2,
    },
    "validation_checks": [
        "Lower confidence fact ($500M) has invalidated_by set",
        "Higher confidence fact ($487M) remains valid",
        "Subject entity may differ but represent same concept",
    ],
}


# ==============================================================================
# Helper Functions
# ==============================================================================

def get_expected_graph(doc_name: str) -> Dict[str, Any]:
    """
    Get expected graph structure for a test document.

    Args:
        doc_name: Document identifier (e.g., "static_replacement")

    Returns:
        Expected graph structure dictionary

    Raises:
        KeyError: If document name not found
    """
    graphs = {
        "static_replacement": STATIC_REPLACEMENT_GRAPH,
        "dynamic_coexistence": DYNAMIC_COEXISTENCE_GRAPH,
        "mixed_facts": MIXED_FACTS_GRAPH,
        "complex_decomposition": COMPLEX_DECOMPOSITION_GRAPH,
        "temporal_sequence": TEMPORAL_SEQUENCE_GRAPH,
        "confidence_override": CONFIDENCE_OVERRIDE_GRAPH,
    }

    if doc_name not in graphs:
        raise KeyError(
            f"Graph structure for '{doc_name}' not found. Available: {list(graphs.keys())}"
        )

    return graphs[doc_name]


def validate_graph_structure(
    graph_nodes: List[Any],
    graph_edges: List[Any],
    doc_name: str,
) -> Dict[str, Any]:
    """
    Validate actual graph structure against expected structure.

    Args:
        graph_nodes: List of graph nodes from E2E test
        graph_edges: List of graph edges from E2E test
        doc_name: Document identifier for expected structure lookup

    Returns:
        Validation result dictionary with:
        - passed: bool
        - errors: List[str]
        - warnings: List[str]
        - stats: Dict with actual counts

    Example:
        >>> result = validate_graph_structure(nodes, edges, "static_replacement")
        >>> assert result["passed"], result["errors"]
    """
    expected = get_expected_graph(doc_name)
    errors = []
    warnings = []

    # Count node types
    entity_nodes = [n for n in graph_nodes if _is_entity_node(n)]
    metadata_nodes = [n for n in graph_nodes if _is_metadata_node(n)]

    # Count edge types
    predicate_edges = [e for e in graph_edges if _is_predicate_edge(e)]
    invalidation_edges = [e for e in graph_edges if _is_invalidation_edge(e)]

    # Validate minimums
    if len(entity_nodes) < expected.get("min_entity_nodes", 0):
        errors.append(
            f"Insufficient entity nodes: {len(entity_nodes)} < {expected['min_entity_nodes']}"
        )

    if len(metadata_nodes) < expected.get("min_metadata_nodes", 0):
        errors.append(
            f"Insufficient metadata nodes: {len(metadata_nodes)} < {expected['min_metadata_nodes']}"
        )

    if len(predicate_edges) < expected.get("min_predicate_edges", 0):
        errors.append(
            f"Insufficient predicate edges: {len(predicate_edges)} < {expected['min_predicate_edges']}"
        )

    expected_invalidations = expected.get("invalidation_edges", 0)
    if len(invalidation_edges) != expected_invalidations:
        errors.append(
            f"Invalidation edge count mismatch: {len(invalidation_edges)} != {expected_invalidations}"
        )

    # Warnings for excess
    if len(entity_nodes) > expected.get("min_entity_nodes", 0) * 1.5:
        warnings.append(
            f"Unusually high entity node count: {len(entity_nodes)} (expected ~{expected['min_entity_nodes']})"
        )

    stats = {
        "entity_nodes": len(entity_nodes),
        "metadata_nodes": len(metadata_nodes),
        "predicate_edges": len(predicate_edges),
        "invalidation_edges": len(invalidation_edges),
        "total_nodes": len(graph_nodes),
        "total_edges": len(graph_edges),
    }

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
        "expected": expected,
    }


def _is_entity_node(node: Any) -> bool:
    """Check if node is an entity node (subject or object from AtomicFact)."""
    # Implementation depends on graph node structure
    # Placeholder logic: entity nodes don't have 'fact_type' attribute
    return not hasattr(node, "fact_type")


def _is_metadata_node(node: Any) -> bool:
    """Check if node is an AtomicFact metadata node."""
    # Metadata nodes have fact_type attribute
    return hasattr(node, "fact_type")


def _is_predicate_edge(edge: Any) -> bool:
    """Check if edge is a predicate edge (subject→object)."""
    # Predicate edges have 'predicate' property
    return hasattr(edge, "predicate") or "predicate" in getattr(edge, "properties", {})


def _is_invalidation_edge(edge: Any) -> bool:
    """Check if edge is an invalidation edge (fact→fact)."""
    # Invalidation edges have 'invalidated_by' or 'invalidation' property
    props = getattr(edge, "properties", {})
    return "invalidated_by" in props or "invalidation" in str(type(edge)).lower()


def get_graph_summary() -> str:
    """
    Get human-readable summary of all expected graph structures.

    Returns:
        Formatted string with graph expectations
    """
    docs = [
        "static_replacement",
        "dynamic_coexistence",
        "mixed_facts",
        "complex_decomposition",
        "temporal_sequence",
        "confidence_override",
    ]

    lines = ["Expected Graph Structures Summary:", "=" * 70]

    for doc_name in docs:
        graph = get_expected_graph(doc_name)
        lines.append(f"\n{doc_name.upper().replace('_', ' ')}")
        lines.append(f"  Description: {graph['description']}")
        lines.append(f"  Entity Nodes: >={graph.get('min_entity_nodes', 0)}")
        lines.append(f"  Metadata Nodes: >={graph.get('min_metadata_nodes', 0)}")
        lines.append(f"  Predicate Edges: >={graph.get('min_predicate_edges', 0)}")
        lines.append(f"  Invalidation Edges: {graph.get('invalidation_edges', 0)}")

    return "\n".join(lines)
