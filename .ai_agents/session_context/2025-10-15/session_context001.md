# Session Context - 2025-10-15
Created: 2025-10-15
Agent: Codex

## Notes
- Session resumed to advise on prompt strategy for Cognee memory tooling.
- Serena project `cognee` activated and onboarding reminder acknowledged.

## Plan
- [x] Establish session context
- [x] Review existing documentation and task state as needed
- [x] Provide guidance on Cognee prompt updates

## Decisions
- None yet.

## Work Log
- 2025-10-15T19:44:00Z: Created session context and confirmed Serena activation.
- 2025-10-15T19:52:00Z: Reviewed MCP tool docstrings related to memory storage/retrieval guidance.
- 2025-10-15T19:55:00Z: Drafted recommendations for adjusting client-facing prompts.
- 2025-10-15T20:05:00Z: Updated MCP tool docstrings and README with long-term memory workflow guidance.
- 2025-10-15T20:30:00Z: Enhanced graph completion prompts and fallback handling for empty memory retrievals.
- 2025-10-15T20:45:00Z: Strengthened atomic fact extraction and classification prompts for temporal invalidation.
- 2025-10-15T22:55:00Z: Clarified MCP stdio behavior where cognify runs as a background task to dodge transport timeouts.
- 2025-10-15T23:40:00Z: Added Postgres reset support to `cognee-mcp/reset_databases.py` and attempted dry-run (blocked by sandbox cache permissions).
