# Temporal Cascade Extension - Agent Coordination Instructions

## Session Date: 2025-10-10

## Mission
Implement temporal atomic fact extraction for Cognee's knowledge graph pipeline. Enable long-term AI agents to reason about changes over time by storing temporally precise "atomic facts."

## Beta Philosophy
- **NO FEATURE FLAGS**: All changes go live immediately
- **FAIL FAST**: If it breaks, we fix it quickly
- **SIMPLE CODE**: No conditional paths, no toggles
- All atomic fact extraction is always enabled in the pipeline

## Your Role
You are one of 4 parallel agents implementing different workstreams. Work independently but coordinate through shared files.

## Shared Resources

### Tasklist (Source of Truth)
- **File**: `/home/adityasharma/Projects/cognee/.ai_agents/improvements_tasklist_parallel.md`
- **Update**: Mark your completed tasks with `[x]`
- **Check**: Review before starting to see what others have completed

### Work Logs (Communication)
- **Your log**: `.claude/session_context/2025-10-10/agent_[A|B|C|D]_worklog.md`
- **Format**:
  ```markdown
  # Agent X Work Log - 2025-10-10

  ## Completed Tasks
  - [x] Task ID: Brief description + file paths

  ## API Changes / Interface Decisions
  - Decision: What you decided and why (affects other agents)

  ## Blockers / Issues
  - Issue: What's blocking you (other agents check this)

  ## Next Steps
  - What you're working on next
  ```

### Coordination File (Check Before Starting)
- **File**: `.claude/session_context/2025-10-10/shared_decisions.md`
- **Purpose**: Critical decisions that affect multiple workstreams
- **Update**: When you make a decision that changes interfaces used by others

## Quality Standards
- **Test Coverage**: Minimum 80% per module
- **Type Hints**: All functions must have type annotations
- **Docstrings**: Comprehensive docstrings for all public functions
- **Async Handling**: All async functions properly handle exceptions
- **Code Patterns**: Follow existing patterns in cognee codebase

## Performance Targets
- Atomic extraction: <500ms per chunk
- Classification: <200ms per batch of 10 facts
- Invalidation check: <100ms per fact
- Total overhead: <2x base pipeline

## Critical Dependencies

### Hard Blockers
- **Agent C, D**: Cannot finalize until Agent A completes A1 (AtomicFact model)
  - **Workaround**: Use dict stubs `{"subject": "", "predicate": "", "object": ""}` initially
  - **Update**: Switch to AtomicFact once A1 is complete

### Soft Dependencies
- **Agent C**: Can start with stub prompts, update when Agent B completes B1/B2
- **Agent D**: Can use dict-based conflict detection initially

## Communication Protocol

### When to Update Shared Files
1. **Immediately**: When you complete A1 (AtomicFact model) - unblocks C & D
2. **Immediately**: When you change an interface/API that others use
3. **After each task**: Update tasklist with `[x]` marker
4. **Daily**: Update your work log with progress

### What to Document
- ✅ Field names and types you added to AtomicFact
- ✅ Function signatures you created (esp. if others will call them)
- ✅ Enum values you defined (FACT/OPINION/PREDICTION, etc.)
- ✅ Prompt template variable names ({{text}}, {{context}}, etc.)
- ❌ Implementation details that don't affect others

## Emergency Escalation
If you discover a fundamental architectural issue that invalidates the plan:
1. Document in your work log under "## CRITICAL BLOCKER"
2. Update `.ai_agents/improvements.md` with the issue
3. Stop work on affected tasks until resolved

## Final Deliverable
When you complete your workstream:
1. Mark all tasks `[x]` in tasklist
2. Run all tests - ensure they pass
3. Update work log with summary
4. Create summary in: `.claude/session_context/2025-10-10/agent_[X]_summary.md`

## Questions?
Check `.ai_agents/improvements_tasklist_parallel.md` for detailed task requirements.
