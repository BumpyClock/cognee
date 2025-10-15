import asyncio
from typing import List
from uuid import uuid4

from cognee.modules.chunking.models.DocumentChunk import DocumentChunk
from cognee.shared.data_models import KnowledgeGraph
from cognee.modules.ontology.base_ontology_resolver import BaseOntologyResolver
from cognee.modules.config import get_temporal_config
from cognee.tasks.graph.cascade_extract.utils.extract_nodes import extract_nodes
from cognee.tasks.graph.cascade_extract.utils.extract_content_nodes_and_relationship_names import (
    extract_content_nodes_and_relationship_names,
)
from cognee.tasks.graph.cascade_extract.utils.extract_edge_triplets import (
    extract_edge_triplets,
)
from cognee.tasks.graph.cascade_extract.utils.extract_atomic_facts import extract_atomic_statements
from cognee.tasks.graph.cascade_extract.utils.classify_atomic_facts import classify_atomic_facts_temporally
from cognee.tasks.graph.extract_graph_from_data import integrate_chunk_graphs
from cognee.tasks.storage.manage_atomic_fact_storage import detect_and_invalidate_conflicting_facts
from cognee.modules.observability.atomic_fact_metrics import (
    track_extraction,
    track_classification,
)
from cognee.shared.logging_utils import get_logger

logger = get_logger("extract_graph_from_data_v2")


async def extract_graph_from_data(
    data_chunks: List[DocumentChunk],
    n_rounds: int = 2,
    ontology_adapter: BaseOntologyResolver = None,
) -> List[DocumentChunk]:
    """Extract and update graph data from document chunks using cascade extraction.

    This function performs multi-step graph extraction from document chunks,
    using cascade extraction techniques to build comprehensive knowledge graphs.
    Atomic fact extraction is always enabled (now the default pipeline behavior).

    Args:
        data_chunks: List of document chunks to process
        n_rounds: Number of extraction rounds to perform (default: 2)
        ontology_adapter: Resolver for validating entities against ontology

    Returns:
        List of updated DocumentChunk objects with extracted graph data
    """
    # Load temporal config for extraction rounds configuration
    temporal_config = get_temporal_config()

    # STEP 1: Extract atomic facts from each chunk
    logger.info(f"Extracting atomic facts from {len(data_chunks)} chunks")
    correlation_id = str(uuid4())

    import time
    start_time = time.time()

    # Extract and classify atomic facts for all chunks in parallel
    atomic_fact_tasks = []
    for chunk in data_chunks:
        async def process_chunk_facts(chunk):
            chunk_start = time.time()

            # Extract atomic facts
            facts = await extract_atomic_statements(
                text=chunk.text,
                source_chunk_id=chunk.id,
                n_rounds=temporal_config.extraction_rounds,
            )

            extraction_latency = (time.time() - chunk_start) * 1000
            await track_extraction(
                count=len(facts),
                latency_ms=extraction_latency,
                correlation_id=correlation_id
            )

            # Classify facts
            classify_start = time.time()
            classified_facts = await classify_atomic_facts_temporally(
                facts=facts,
                context=f"Document chunk {chunk.chunk_index}",
                batch_size=temporal_config.classification_batch_size
            )

            classification_latency = (time.time() - classify_start) * 1000
            await track_classification(
                batch_size=len(classified_facts),
                latency_ms=classification_latency,
                correlation_id=correlation_id
            )

            return chunk, classified_facts

        atomic_fact_tasks.append(process_chunk_facts(chunk))

    # Wait for all atomic fact extraction to complete
    chunk_fact_results = await asyncio.gather(*atomic_fact_tasks)

    # Collect all facts for conflict detection
    all_facts = []
    for chunk, classified_facts in chunk_fact_results:
        all_facts.extend(classified_facts)

    total_facts = len(all_facts)
    logger.info(
        f"Extracted and classified {total_facts} atomic facts in "
        f"{(time.time() - start_time)*1000:.2f}ms (correlation_id={correlation_id})"
    )

    # STEP 1.5: Detect and resolve conflicts before adding to chunks
    if total_facts > 0:
        conflict_start = time.time()
        all_facts = await detect_and_invalidate_conflicting_facts(
            atomic_facts=all_facts,
            correlation_id=correlation_id,
        )
        logger.info(
            f"Conflict detection completed in {(time.time() - conflict_start)*1000:.2f}ms"
        )

    # Add atomic facts to chunk.contains after conflict resolution
    fact_index = 0
    for chunk, classified_facts in chunk_fact_results:
        if chunk.contains is None:
            chunk.contains = []
        # Get the processed facts for this chunk
        chunk_fact_count = len(classified_facts)
        processed_facts = all_facts[fact_index:fact_index + chunk_fact_count]
        chunk.contains.extend(processed_facts)
        fact_index += chunk_fact_count

    # STEP 2: Continue with existing cascade extraction
    chunk_nodes = await asyncio.gather(
        *[extract_nodes(chunk.text, n_rounds) for chunk in data_chunks]
    )

    chunk_results = await asyncio.gather(
        *[
            extract_content_nodes_and_relationship_names(chunk.text, nodes, n_rounds)
            for chunk, nodes in zip(data_chunks, chunk_nodes)
        ]
    )

    updated_nodes, relationships = zip(*chunk_results)

    chunk_graphs = await asyncio.gather(
        *[
            extract_edge_triplets(chunk.text, nodes, rels, n_rounds)
            for chunk, nodes, rels in zip(data_chunks, updated_nodes, relationships)
        ]
    )

    return await integrate_chunk_graphs(
        data_chunks=data_chunks,
        chunk_graphs=chunk_graphs,
        graph_model=KnowledgeGraph,
        ontology_adapter=ontology_adapter,
    )
