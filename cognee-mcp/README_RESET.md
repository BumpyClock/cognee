# Database Reset Scripts

Quick scripts to reset Cognee databases and start fresh.

## TL;DR

```bash
# Preview what would be deleted (safe, recommended first)
./reset.sh --dry-run

# Reset everything
./reset.sh

# Reset only Neo4j (keep other data)
./reset.sh --neo4j

# Reset everything EXCEPT Neo4j (keep graph data)
./reset.sh --skip-neo4j
```

## What These Scripts Do

- **`reset.sh`** - Simple bash wrapper (just run this)
- **`reset_databases.py`** - Full Python implementation (more features)
- **`RESET_GUIDE.md`** - Complete documentation

## Databases Reset

1. **SQLite** - Relational database (users, datasets, metadata)
2. **Neo4j** - Graph database (knowledge graph, entities, relationships)
3. **Qdrant** - Vector database (embeddings for semantic search)
4. **File DBs** - Kuzu and LanceDB files

## Quick Examples

```bash
# Safe preview - see what would be deleted
./reset.sh --dry-run

# Reset after running tests
./reset.sh

# Reset only graph database
./reset.sh --neo4j

# Keep graph, reset everything else
./reset.sh --skip-neo4j

# Get help
./reset.sh --help
```

## Prerequisites

```bash
# Neo4j must be running
docker ps | grep neo4j

# Python packages (usually already installed)
pip install neo4j qdrant-client
```

## Safety

✅ **Always Safe**:
- `--dry-run` flag previews without deleting
- Selective reset options
- Summary report shows what happened

⚠️ **Be Careful**:
- Data is permanently deleted
- No confirmation prompt (by design)
- Make sure Neo4j is running first

## More Info

See `RESET_GUIDE.md` for complete documentation including:
- Detailed usage examples
- Troubleshooting guide
- Custom configurations
- CI/CD integration
- Safety features

## Common Issues

**"Neo4j driver not available"**
```bash
pip install neo4j
```

**"Failed to reset Neo4j: Connection refused"**
```bash
docker start neo4j  # or docker-compose up -d neo4j
```

**"No databases found"**
- Databases may be in custom locations
- Check `.env` for `DATA_ROOT_DIRECTORY` and `SYSTEM_ROOT_DIRECTORY`
- Run `--dry-run` to see search paths

---

**Need help?** Check `RESET_GUIDE.md` or run `./reset.sh --help`
