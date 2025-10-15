# Temporal Cascade Extension Tasklist (2025-10-10)

## Context
- Goal: upgrade Cognee’s knowledge graph pipeline to store temporally precise “atomic facts” so long-term AI agents can reason about changes over time.
- Motivation: complex sentences hide multiple events; breaking them into atomic statements enables accurate timestamping, conflict invalidation, and multi-hop retrieval.
- Scope: extend the cascade extractor pathway with three new capabilities — atomic fact extraction, temporal classification (episodic + temporal typing), and invalidation handling — without regressing existing ontology resolution or storage flows.
- Constraints: reuse the current Task pipeline, keep ontology-driven canonicalization intact, and allow feature toggling for legacy deployments.
- Scaffolding:
  - Spin up feature branch `feature/atomic-temporal-cascade` (or sub-branches per phase) so diff stays isolated.
  - Maintain prompt assets in ASCII; run `poetry run pytest` for affected modules plus any new snapshot tests.
  - Use `.ai_agents/session_context/YYYY-MM-DD/session_context###.md` to note progress; update checklist here as phases complete.
  - Before merging, run cascade integration test suite (`poetry run pytest cognee/tests/tasks/graph -k cascade`) and vector/graph indexing smoke tests.

## Phase 1 – Data & Models
- [ ] Define `AtomicFact` datapoint in `cognee/modules/engine/models/AtomicFact.py` with required fields (subject, predicate, object, source references, episodic/temporal enums, validity timestamps, confidence).
- [ ] Export new model via `cognee/modules/engine/models/__init__.py` and ensure `cognee/shared/data_models.py` imports/aliases it if needed for serialization.
- [ ] Extend `cognee/modules/graph/utils/get_graph_from_model.py` to emit nodes/edges for `AtomicFact`, carrying temporal attributes into edge metadata.

## Phase 2 – Prompt Assets
- [ ] Draft `extract_atomic_facts_prompt_system/input` templates under `cognee/tasks/graph/cascade_extract/prompts/`.
- [ ] Draft `classify_atomic_fact_prompt_system/input` templates for episodic/temporal tagging.
- [ ] Sanity-check prompt rendering via `render_prompt` using fixture text (ideally unit-tested with frozen inputs).

## Phase 3 – Atomic Fact Extraction Stage
- [ ] Implement `extract_atomic_statements` coroutine in new module `cognee/tasks/graph/cascade_extract/utils/extract_atomic_facts.py` (LLM call, multi-round dedupe, returns `AtomicFact` list).
- [ ] Write unit tests covering multi-event sentences and pronoun resolution expectations.
- [ ] Ensure extracted facts are appended to `DocumentChunk.contains`.

## Phase 4 – Temporal Agent Classification
- [ ] Implement `classify_atomic_facts_temporally` helper to annotate episodic/temporal types, validity windows, and confidence scores.
- [ ] Add prompt-driven tests verifying classification outputs for FACT/OPINION/PREDICTION and ATEMPORAL/STATIC/DYNAMIC cases.

## Phase 5 – Cascade Pipeline Integration
- [ ] Update `extract_graph_from_data_v2` to call new extraction + classification helpers before existing cascade steps.
- [ ] Derive candidate node/relationship sets from `AtomicFact` outputs and pass into `extract_nodes`, `extract_content_nodes_and_relationship_names`, and `extract_edge_triplets`.
- [ ] Verify `DocumentChunk.contains` retains both facts and downstream entity/event objects without duplication.

## Phase 6 – Invalidation Workflow
- [ ] Create `cognee/tasks/storage/manage_atomic_fact_conflicts.py` providing conflict detection (`find_conflicting_facts`) and `invalidate_fact` routines.
- [ ] Integrate invalidation checks into `add_data_points` or wrapper Task before persisting `AtomicFact` nodes/edges.
- [ ] Write unit tests simulating STATIC→STATIC replacement and DYNAMIC supersession scenarios, ensuring `expired_at` and `invalidated_by` edge creation.

## Phase 7 – Task Pipeline Wiring
- [ ] Register new Tasks in `get_default_tasks` (`cognee/api/v1/cognify/cognify.py`) post-chunking layer; ensure batch configs align with existing stages.
- [ ] Provide configuration flag to toggle atomic processing (env var + default).
- [ ] Update pipeline docs / README to describe new stages and configuration.

## Phase 8 – Entity Resolution Alignment
- [ ] Review `_create_entity_node` / `_create_type_node` behavior with fact-derived names; adjust mappings if alias handling needs enhancements.
- [ ] Add regression test covering ontology match substitution with new facts.

## Phase 9 – Observability & Logging
- [ ] Add structured logs for atomic fact counts, classification latency, invalidation events.
- [ ] Expose simple metrics (e.g., via `cognee/modules/observability`) for monitoring fact extraction/invalidation throughput.

## Phase 10 – End-to-End Validation
- [ ] Build integration test running cascade pipeline on sample document containing multiple temporal statements; assert resulting graph nodes/edges and fact metadata.
- [ ] Benchmark LLM call overhead and tune default `n_rounds`; document findings.
- [ ] Update `.ai_agents/improvements.md` and session context with progress checkpoints.
