# Temporal Cascade Extension - Parallelized Sprint Plan

## Executive Summary
This sprint plan transforms the linear 10-phase Temporal Cascade Extension into a parallelized implementation using 4 concurrent AI agents. The plan maximizes throughput by separating independent work into distinct workstreams while carefully managing dependencies. All workstreams can begin immediately with minimal blocking, achieving approximately 70% parallel execution efficiency.

## Dependency Analysis

### Critical Path Dependencies
1. **AtomicFact Model** (A1) → Graph Utils Extension (A3) → Pipeline Integration (Phase 5)
2. **Prompt Templates** (B1-B2) → Extraction/Classification Implementations (C1-C2)
3. **All Workstreams** → Integration Phase → End-to-End Validation

### Parallel Opportunities
- **Models & Infrastructure** (Workstream A) - Independent foundation work
- **Prompt Engineering** (Workstream B) - Can proceed in parallel with models
- **Core Extraction Logic** (Workstream C) - Can start with stub models
- **Storage & Invalidation** (Workstream D) - Independent conflict management system

## Detailed Task Breakdown

### Sprint 1 - Parallel Foundation (Days 1-3)

#### WORKSTREAM A: Data Models & Infrastructure
**Focus**: Building the foundational data models and graph integration

##### A1: Create AtomicFact Model [Complexity: Medium]
- **Files**:
  - `/home/adityasharma/Projects/cognee/cognee/modules/engine/models/AtomicFact.py` (create)
  - `/home/adityasharma/Projects/cognee/cognee/modules/engine/models/__init__.py` (update)
- **Requirements**:
  - Inherit from DataPoint base class
  - Fields: subject (str), predicate (str), object (str), source_chunk_id (UUID), source_text (str)
  - Temporal fields: episodic_type (Enum: EPISODIC/NON_EPISODIC), temporal_type (Enum: ATEMPORAL/STATIC/DYNAMIC)
  - Validity fields: valid_from (Timestamp), valid_until (Optional[Timestamp]), confidence (float)
  - Classification: fact_type (Enum: FACT/OPINION/PREDICTION)
  - Metadata: extracted_at (int), invalidated_by (Optional[UUID])
- **Tests**:
  - Unit test for model validation in `tests/unit/modules/engine/models/test_atomic_fact.py`
  - Test all field validations and enum constraints
- **Dependencies**: None

##### A2: Update Data Models Registry [Complexity: Low]
- **Files**:
  - `/home/adityasharma/Projects/cognee/cognee/shared/data_models.py` (update if exists, create if not)
- **Requirements**:
  - Import and export AtomicFact model
  - Ensure serialization compatibility
- **Tests**: Import verification test
- **Dependencies**: Depends on A1

##### A3: Extend Graph Utils for AtomicFact [Complexity: High]
- **Files**:
  - `/home/adityasharma/Projects/cognee/cognee/modules/graph/utils/get_graph_from_model.py` (update)
  - `/home/adityasharma/Projects/cognee/cognee/modules/graph/utils/__init__.py` (verify exports)
- **Requirements**:
  - Add AtomicFact → node/edge conversion logic
  - Map temporal attributes to edge metadata
  - Handle validity window representation
  - Support invalidation edges
- **Tests**:
  - Unit test AtomicFact to graph conversion
  - Test temporal metadata preservation
- **Dependencies**: Depends on A1

##### A4: Create Configuration System [Complexity: Low]
- **Files**:
  - `/home/adityasharma/Projects/cognee/cognee/modules/config/temporal_config.py` (create)
  - `/home/adityasharma/Projects/cognee/cognee/.env.example` (update)
- **Requirements**:
  - Add ENABLE_ATOMIC_FACTS env variable (default: False)
  - Add ATOMIC_EXTRACTION_ROUNDS config (default: 2)
  - Configuration class with validation
- **Tests**: Configuration loading test
- **Dependencies**: None

#### WORKSTREAM B: Prompt Engineering & Templates
**Focus**: Creating all prompt templates for atomic fact extraction and classification

##### B1: Atomic Fact Extraction Prompts [Complexity: Medium]
- **Files**:
  - `/home/adityasharma/Projects/cognee/cognee/tasks/graph/cascade_extract/prompts/extract_atomic_facts_prompt_system.txt` (create)
  - `/home/adityasharma/Projects/cognee/cognee/tasks/graph/cascade_extract/prompts/extract_atomic_facts_prompt_input.txt` (create)
- **Requirements**:
  - System prompt: Instructions for breaking complex sentences into atomic triplets
  - Include examples of pronoun resolution
  - Handle multi-event sentence decomposition
  - Input template with context variables: {text}, {previous_facts}, {round_number}
- **Tests**:
  - Prompt rendering test with fixture data
  - Validate template variable substitution
- **Dependencies**: None

##### B2: Temporal Classification Prompts [Complexity: Medium]
- **Files**:
  - `/home/adityasharma/Projects/cognee/cognee/tasks/graph/cascade_extract/prompts/classify_atomic_fact_prompt_system.txt` (create)
  - `/home/adityasharma/Projects/cognee/cognee/tasks/graph/cascade_extract/prompts/classify_atomic_fact_prompt_input.txt` (create)
- **Requirements**:
  - System prompt for episodic/temporal classification
  - Examples for FACT vs OPINION vs PREDICTION
  - Examples for ATEMPORAL vs STATIC vs DYNAMIC
  - Confidence scoring guidelines
  - Input template with fact triplet and context
- **Tests**:
  - Prompt rendering with various fact types
  - Edge case handling (ambiguous facts)
- **Dependencies**: None

##### B3: Prompt Testing Suite [Complexity: Low]
- **Files**:
  - `/home/adityasharma/Projects/cognee/tests/unit/tasks/graph/cascade_extract/test_prompts.py` (create)
- **Requirements**:
  - Test all prompt templates render correctly
  - Verify variable substitution
  - Test with edge case inputs (empty, very long text)
- **Tests**: Comprehensive prompt validation suite
- **Dependencies**: Depends on B1, B2

#### WORKSTREAM C: Extraction & Classification Implementation
**Focus**: Core logic for atomic fact extraction and temporal classification

##### C1: Implement Atomic Fact Extraction [Complexity: High]
- **Files**:
  - `/home/adityasharma/Projects/cognee/cognee/tasks/graph/cascade_extract/utils/extract_atomic_facts.py` (create)
- **Requirements**:
  - Async function: `extract_atomic_statements(text: str, n_rounds: int = 2) -> List[AtomicFact]`
  - Multi-round extraction with deduplication
  - Pronoun resolution logic
  - Response model using Pydantic
  - Integration with LLMGateway
- **Tests**:
  - Unit tests with mock LLM responses
  - Multi-event sentence decomposition tests
  - Pronoun resolution verification
- **Dependencies**: Soft dependency on B1 (can use stub prompts initially)

##### C2: Implement Temporal Classification [Complexity: High]
- **Files**:
  - `/home/adityasharma/Projects/cognee/cognee/tasks/graph/cascade_extract/utils/classify_atomic_facts.py` (create)
- **Requirements**:
  - Async function: `classify_atomic_facts_temporally(facts: List[AtomicFact]) -> List[AtomicFact]`
  - Batch processing for efficiency
  - Assign episodic_type, temporal_type, confidence
  - Determine validity windows based on classification
- **Tests**:
  - Classification accuracy tests
  - Edge case handling (contradictory facts)
  - Batch processing verification
- **Dependencies**: Soft dependency on B2, C1

##### C3: Create Extraction Response Models [Complexity: Low]
- **Files**:
  - `/home/adityasharma/Projects/cognee/cognee/tasks/graph/cascade_extract/models/extraction_models.py` (create)
- **Requirements**:
  - Pydantic models for LLM responses
  - AtomicFactResponse model
  - TemporalClassificationResponse model
  - Validation rules
- **Tests**: Model validation tests
- **Dependencies**: Depends on A1

#### WORKSTREAM D: Storage, Invalidation & Observability
**Focus**: Conflict detection, invalidation handling, and monitoring

##### D1: Implement Conflict Detection [Complexity: High]
- **Files**:
  - `/home/adityasharma/Projects/cognee/cognee/tasks/storage/manage_atomic_fact_conflicts.py` (create)
- **Requirements**:
  - Function: `find_conflicting_facts(new_fact: AtomicFact, existing_facts: List[AtomicFact]) -> List[AtomicFact]`
  - Subject-predicate matching logic
  - STATIC vs DYNAMIC conflict rules
  - Confidence-based resolution
- **Tests**:
  - Conflict detection scenarios
  - Edge cases (partial matches, different confidence levels)
- **Dependencies**: Soft dependency on A1 (can use dict representation initially)

##### D2: Implement Invalidation Workflow [Complexity: Medium]
- **Files**:
  - `/home/adityasharma/Projects/cognee/cognee/tasks/storage/invalidate_facts.py` (create)
- **Requirements**:
  - Function: `invalidate_fact(fact_id: UUID, new_fact_id: UUID, reason: str)`
  - Create invalidation edges in graph
  - Update expired_at timestamps
  - Maintain invalidation history
- **Tests**:
  - Invalidation chain tests
  - Timestamp update verification
- **Dependencies**: Depends on D1

##### D3: Add Observability & Metrics [Complexity: Medium]
- **Files**:
  - `/home/adityasharma/Projects/cognee/cognee/modules/observability/atomic_fact_metrics.py` (create)
  - `/home/adityasharma/Projects/cognee/cognee/shared/logging_utils.py` (update)
- **Requirements**:
  - Structured logging for extraction counts
  - Classification latency metrics
  - Invalidation event tracking
  - Conflict resolution statistics
  - Integration with existing observability framework
- **Tests**:
  - Metric collection verification
  - Log format validation
- **Dependencies**: None

##### D4: Create Storage Integration Tests [Complexity: Low]
- **Files**:
  - `/home/adityasharma/Projects/cognee/tests/integration/tasks/storage/test_atomic_fact_storage.py` (create)
- **Requirements**:
  - Test fact persistence
  - Test conflict detection with database
  - Test invalidation workflow
- **Tests**: Integration test suite
- **Dependencies**: Depends on D1, D2

### Sprint 2 - Integration & Validation (Days 4-5)

#### INTEGRATION PHASE (All Agents Collaborate)

##### I1: Pipeline Integration [Complexity: High]
- **Files**:
  - `/home/adityasharma/Projects/cognee/cognee/tasks/graph/extract_graph_from_data_v2.py` (update)
  - `/home/adityasharma/Projects/cognee/cognee/api/v1/cognify/cognify.py` (update)
- **Requirements**:
  - Integrate atomic fact extraction before existing cascade steps
  - Add feature flag checking
  - Update DocumentChunk.contains with facts
  - Pass facts to existing extraction functions
  - Wire invalidation checks in add_data_points
- **Tests**:
  - Integration test with feature flag on/off
  - Backward compatibility verification
- **Dependencies**: Depends on A1-A4, C1-C2, D1-D2

##### I2: Entity Resolution Alignment [Complexity: Medium]
- **Files**:
  - `/home/adityasharma/Projects/cognee/cognee/modules/graph/utils/entity_resolution.py` (review/update if exists)
- **Requirements**:
  - Ensure fact-derived entities align with ontology resolver
  - Update alias handling if needed
  - Maintain backward compatibility
- **Tests**:
  - Regression test for ontology matching
  - Fact-to-entity mapping tests
- **Dependencies**: Depends on I1

##### I3: End-to-End Validation [Complexity: High]
- **Files**:
  - `/home/adityasharma/Projects/cognee/tests/e2e/test_temporal_cascade.py` (create)
  - `/home/adityasharma/Projects/cognee/tests/fixtures/temporal_documents.py` (create)
- **Requirements**:
  - Complete pipeline test with temporal documents
  - Verify graph structure with atomic facts
  - Test invalidation scenarios
  - Performance benchmarking
  - Document LLM call overhead findings
- **Tests**:
  - Full pipeline execution
  - Graph validation
  - Performance metrics
- **Dependencies**: Depends on I1, I2

##### I4: Documentation & Configuration [Complexity: Low]
- **Files**:
  - `/home/adityasharma/Projects/cognee/README.md` (update)
  - `/home/adityasharma/Projects/cognee/docs/temporal_cascade.md` (create)
  - `/home/adityasharma/Projects/cognee/.ai_agents/improvements.md` (update)
- **Requirements**:
  - Document new pipeline stages
  - Configuration guide
  - API usage examples
  - Performance considerations
- **Tests**: Documentation build verification
- **Dependencies**: Depends on I3

## Execution Timeline

### Day 1-2: Foundation Sprint
- **Agent A**: Complete A1 (AtomicFact model) → A2 (Registry) → Start A3 (Graph Utils)
- **Agent B**: Complete B1 (Extraction prompts) → B2 (Classification prompts) → B3 (Testing)
- **Agent C**: Start C1 with stub model → Complete C3 (Response models)
- **Agent D**: Complete D1 (Conflict detection) → Start D2 (Invalidation)

### Day 2-3: Implementation Sprint
- **Agent A**: Complete A3 (Graph Utils) → A4 (Config)
- **Agent B**: Support C with prompt refinements
- **Agent C**: Complete C1 (Extraction) → C2 (Classification)
- **Agent D**: Complete D2 (Invalidation) → D3 (Observability) → D4 (Storage tests)

### Day 4: Integration Sprint
- **All Agents**: Collaborate on I1 (Pipeline Integration)
- **Agent A + B**: Work on I2 (Entity Resolution)
- **Agent C + D**: Start I3 (E2E Validation)

### Day 5: Validation & Documentation
- **Agent C + D**: Complete I3 (E2E Validation)
- **Agent A + B**: Complete I4 (Documentation)
- **All Agents**: Final testing and bug fixes

## Risk Mitigation

### Technical Risks
1. **LLM Performance**: Mitigated by configurable n_rounds and batch processing
2. **Backward Compatibility**: Feature flag ensures safe rollout
3. **Graph Complexity**: Invalidation edges kept separate from main graph

### Coordination Risks
1. **Model Dependencies**: C1/C2 can use dict representations initially
2. **Prompt Dependencies**: Stub prompts allow parallel development
3. **Integration Conflicts**: Clear interface definitions prevent issues

## Success Metrics
- All unit tests passing (minimum 80% coverage)
- Integration tests demonstrating temporal cascade functionality
- Performance: < 2x overhead compared to non-temporal pipeline
- Zero regression in existing functionality
- Feature flag successfully toggles functionality

## Critical Synchronization Points
1. **End of Day 1**: A1 (AtomicFact model) must be complete for others to integrate
2. **End of Day 3**: All extraction/classification logic ready for integration
3. **Start of Day 4**: All agents sync for integration phase
4. **Day 5**: Final validation requires all components complete

## Notes for Implementation
- Each agent should create unit tests alongside implementation
- Use type hints and comprehensive docstrings
- Follow existing code patterns in the codebase
- Coordinate on shared interfaces early
- Document any deviations from the plan in session context