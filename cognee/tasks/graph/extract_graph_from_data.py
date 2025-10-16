import asyncio
from typing import Type, List, Optional
from pydantic import BaseModel

from cognee.infrastructure.databases.graph import get_graph_engine
from cognee.modules.ontology.ontology_env_config import get_ontology_env_config
from cognee.tasks.storage.add_data_points import add_data_points
from cognee.modules.ontology.ontology_config import Config
from cognee.modules.ontology.get_default_ontology_resolver import (
    get_default_ontology_resolver,
    get_ontology_resolver_from_env,
)
from cognee.modules.ontology.base_ontology_resolver import BaseOntologyResolver
from cognee.modules.chunking.models.DocumentChunk import DocumentChunk
from cognee.modules.graph.utils import (
    expand_with_nodes_and_edges,
    retrieve_existing_edges,
)
from cognee.shared.data_models import KnowledgeGraph
from cognee.tasks.graph.exceptions import (
    InvalidGraphModelError,
    InvalidDataChunksError,
    InvalidChunkGraphInputError,
    InvalidOntologyAdapterError,
)
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
from cognee.tasks.storage.manage_atomic_fact_storage import detect_and_invalidate_conflicting_facts
from cognee.modules.observability.atomic_fact_metrics import (
    track_extraction,
    track_classification,
)
from cognee.shared.logging_utils import get_logger


async def integrate_chunk_graphs(
    data_chunks: list[DocumentChunk],
    chunk_graphs: list,
    graph_model: Type[BaseModel],
    ontology_resolver: BaseOntologyResolver,
) -> List[DocumentChunk]:
    """Integrate chunk graphs with ontology validation and store in databases.

    This function processes document chunks and their associated knowledge graphs,
    validates entities against an ontology resolver, and stores the integrated
    data points and edges in the configured databases.

    Args:
        data_chunks: List of document chunks containing source data
        chunk_graphs: List of knowledge graphs corresponding to each chunk
        graph_model: Pydantic model class for graph data validation
        ontology_resolver: Resolver for validating entities against ontology

    Returns:
        List of updated DocumentChunk objects with integrated data

    Raises:
        InvalidChunkGraphInputError: If input validation fails
        InvalidGraphModelError: If graph model validation fails
        InvalidOntologyAdapterError: If ontology resolver validation fails
    """

    if not isinstance(data_chunks, list) or not isinstance(chunk_graphs, list):
        raise InvalidChunkGraphInputError("data_chunks and chunk_graphs must be lists.")
    if len(data_chunks) != len(chunk_graphs):
        raise InvalidChunkGraphInputError(
            f"length mismatch: {len(data_chunks)} chunks vs {len(chunk_graphs)} graphs."
        )
    if not isinstance(graph_model, type) or not issubclass(graph_model, BaseModel):
        raise InvalidGraphModelError(graph_model)
    if ontology_resolver is None or not hasattr(ontology_resolver, "get_subgraph"):
        raise InvalidOntologyAdapterError(
            type(ontology_resolver).__name__ if ontology_resolver else "None"
        )

    graph_engine = await get_graph_engine()

    if graph_model is not KnowledgeGraph:
        for chunk_index, chunk_graph in enumerate(chunk_graphs):
            data_chunks[chunk_index].contains = chunk_graph

        return data_chunks

    existing_edges_map = await retrieve_existing_edges(
        data_chunks,
        chunk_graphs,
    )

    graph_nodes, graph_edges = expand_with_nodes_and_edges(
        data_chunks, chunk_graphs, ontology_resolver, existing_edges_map
    )

    if len(graph_nodes) > 0:
        await add_data_points(graph_nodes)

    if len(graph_edges) > 0:
        await graph_engine.add_edges(graph_edges)

    return data_chunks


logger = get_logger("extract_graph_from_data")


async def extract_graph_from_data(
    data_chunks: List[DocumentChunk],
    graph_model: Type[BaseModel] | None = None,
    config: Config | None = None,
    custom_prompt: Optional[str] = None,
    n_rounds: Optional[int] = None,
    ontology_adapter: Optional[BaseOntologyResolver] = None,
) -> List[DocumentChunk]:
    """
    Unified graph extractor (temporal cascade by default) with backward-compatible signature.

    Accepts legacy parameters (graph_model, config, custom_prompt) but ignores them for the
    extraction path—atomic fact cascade is now the default. If an ontology adapter is not
    supplied, one is resolved from environment/config.
    """

    if not isinstance(data_chunks, list) or not data_chunks:
        raise InvalidDataChunksError("must be a non-empty list of DocumentChunk.")
    if not all(hasattr(c, "text") for c in data_chunks):
        raise InvalidDataChunksError("each chunk must have a 'text' attribute")

    # Resolve ontology adapter
    if ontology_adapter is None:
        if config is None:
            ontology_config = get_ontology_env_config()
            if (
                ontology_config.ontology_file_path
                and ontology_config.ontology_resolver
                and ontology_config.matching_strategy
            ):
                config = {
                    "ontology_config": {
                        "ontology_resolver": get_ontology_resolver_from_env(
                            **ontology_config.to_dict()
                        )
                    }
                }
            else:
                config = {
                    "ontology_config": {"ontology_resolver": get_default_ontology_resolver()}
                }
        ontology_adapter = config["ontology_config"]["ontology_resolver"]

    # Determine rounds
    temporal_config = get_temporal_config()
    rounds = n_rounds or temporal_config.extraction_rounds

    # STEP 1: Extract and classify atomic facts (temporal cascade)
    logger.info(f"Extracting atomic facts from {len(data_chunks)} chunks (rounds={rounds})")

    import time
    start_time = time.time()

    async def process_chunk_facts(chunk: DocumentChunk):
        chunk_start = time.time()
        facts = await extract_atomic_statements(
            text=chunk.text, source_chunk_id=chunk.id, n_rounds=rounds
        )
        extraction_latency = (time.time() - chunk_start) * 1000
        await track_extraction(
            count=len(facts), latency_ms=extraction_latency, correlation_id="unified"
        )
        classify_start = time.time()
        classified = await classify_atomic_facts_temporally(
            facts=facts, context=f"Document chunk {chunk.chunk_index}", batch_size=temporal_config.classification_batch_size
        )
        classification_latency = (time.time() - classify_start) * 1000
        await track_classification(
            batch_size=len(classified), latency_ms=classification_latency, correlation_id="unified"
        )
        return chunk, classified

    chunk_fact_results = await asyncio.gather(
        *[process_chunk_facts(chunk) for chunk in data_chunks]
    )

    # Collect and resolve conflicts across all facts
    all_facts = []
    for chunk, classified in chunk_fact_results:
        all_facts.extend(classified)

    if all_facts:
        all_facts = await detect_and_invalidate_conflicting_facts(
            atomic_facts=all_facts, correlation_id="unified"
        )

    # Attach atomic facts back to chunks
    idx = 0
    for chunk, classified in chunk_fact_results:
        if chunk.contains is None:
            chunk.contains = []
        count = len(classified)
        chunk.contains.extend(all_facts[idx : idx + count])
        idx += count

    # STEP 2: Cascade node/edge extraction
    chunk_nodes = await asyncio.gather(
        *[extract_nodes(chunk.text, rounds) for chunk in data_chunks]
    )
    node_rel_results = await asyncio.gather(
        *[
            extract_content_nodes_and_relationship_names(chunk.text, nodes, rounds)
            for chunk, nodes in zip(data_chunks, chunk_nodes)
        ]
    )
    updated_nodes, relationships = zip(*node_rel_results)
    chunk_graphs = await asyncio.gather(
        *[
            extract_edge_triplets(chunk.text, nodes, rels, rounds)
            for chunk, nodes, rels in zip(data_chunks, updated_nodes, relationships)
        ]
    )

    # Integrate into graph storage
    return await integrate_chunk_graphs(
        data_chunks=data_chunks,
        chunk_graphs=chunk_graphs,
        graph_model=KnowledgeGraph,
        ontology_resolver=ontology_adapter,
    )
