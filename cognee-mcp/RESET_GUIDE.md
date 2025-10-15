# Database Reset Guide

This guide explains how to reset Cognee databases to start fresh.

## Quick Start

### Reset Everything (SQLite + Neo4j + Qdrant + Files)

```bash
# Preview what would be deleted (safe)
./reset.sh --dry-run

# Actually reset all databases
./reset.sh
```

### Reset Specific Databases

```bash
# Reset only Neo4j
./reset.sh --neo4j

# Reset only SQLite
./reset.sh --sqlite

# Reset everything EXCEPT Neo4j (keep graph data)
./reset.sh --skip-neo4j

# Reset only file-based databases (Kuzu, LanceDB)
./reset.sh --files
```

## What Gets Deleted?

### SQLite Database
- Location: `.venv/` or `~/.cognee/system/`
- Contains: User data, datasets, metadata, relational tables
- File: `cognee_db.db` or similar `.db`/`.sqlite` files

### Neo4j Database
- Location: Remote at `bolt://localhost:7687`
- Contains: Knowledge graph, entities, relationships, atomic facts
- Action: Deletes all nodes and relationships (but keeps Neo4j itself running)

### Qdrant Database (if configured)
- Location: Remote at configured URL
- Contains: Vector embeddings for semantic search
- Action: Deletes all collections

### File-based Databases
- Kuzu: `.kuzu` directories
- LanceDB: `.lance` directories
- Location: `.venv/`, `~/.cognee/data/`, etc.

## Prerequisites

### Required Python Packages

The script needs these packages installed:

```bash
# Neo4j support
pip install neo4j

# Qdrant support (optional)
pip install qdrant-client
```

If a package is missing, that database type will be skipped with a warning.

### Neo4j Must Be Running

Make sure Neo4j is running before resetting:

```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Start Neo4j if needed (example)
docker start neo4j
```

## Usage Examples

### Safe Preview (Recommended First Step)

```bash
# See what would be deleted without actually deleting
./reset.sh --dry-run
```

Output:
```
================================================================================
🔄 Cognee Database Reset Script
================================================================================

⚠️  DRY RUN MODE - No actual changes will be made

🗑️  SQLite Databases (2 found):
   - /path/to/cognee-mcp/.venv/cognee_db.db
     [DRY RUN] Would delete
   - /home/user/.cognee/system/cognee_db.db
     [DRY RUN] Would delete

🗑️  Neo4j Database: bolt://localhost:7687
   [DRY RUN] Would delete all nodes and relationships

================================================================================
📊 Summary
================================================================================
   SQLite: ✅ Success
   Neo4j: ✅ Success
```

### Reset After Testing

```bash
# Reset everything after running tests
./reset.sh

# Or reset just what you need
./reset.sh --neo4j --sqlite
```

### Keep Graph Data, Reset Everything Else

```bash
# Useful when you want to keep your knowledge graph
# but reset other databases
./reset.sh --skip-neo4j
```

### Development Workflow

```bash
# 1. Run your tests or experiments
python test_client.py

# 2. Preview what data was created
./reset.sh --dry-run

# 3. Reset to start fresh
./reset.sh

# 4. Verify clean state
python -c "import cognee; print('Ready for new test')"
```

## Troubleshooting

### "Neo4j driver not available"

Install the Neo4j Python driver:
```bash
pip install neo4j
```

### "Failed to reset Neo4j: [Connection refused]"

Neo4j is not running. Start it:
```bash
# Docker
docker start neo4j

# Or check docker-compose
docker-compose up -d neo4j
```

### "Failed to reset Neo4j: [Authentication failed]"

Check your credentials in `.env`:
```bash
GRAPH_DATABASE_USERNAME=neo4j
GRAPH_DATABASE_PASSWORD=semantic-search  # Update if different
```

### No Databases Found

The script searches these locations:
- `.venv/` - Default location for file-based DBs
- `~/.cognee/system/` - SQLite databases
- `~/.cognee/data/` - Data files
- Custom `DATA_ROOT_DIRECTORY` from `.env`
- Custom `SYSTEM_ROOT_DIRECTORY` from `.env`

If your databases are elsewhere, update `.env` with custom paths.

### Permission Denied

Make sure the scripts are executable:
```bash
chmod +x reset.sh reset_databases.py
```

## Advanced Usage

### Direct Python Script

You can also call the Python script directly:

```bash
# With virtual environment activated
source .venv/bin/activate
python reset_databases.py --dry-run

# Or using absolute path
python /full/path/to/reset_databases.py
```

### Integration with CI/CD

Add to your test pipeline:

```yaml
# GitHub Actions example
- name: Reset Cognee databases
  run: |
    cd cognee-mcp
    ./reset.sh
```

### Custom Database Locations

If you have custom database paths, update `.env`:

```bash
# .env
DATA_ROOT_DIRECTORY="/custom/path/data"
SYSTEM_ROOT_DIRECTORY="/custom/path/system"
```

The script will automatically find databases in these locations.

## Safety Features

1. **Dry Run Mode**: Preview deletions before executing
2. **Selective Reset**: Choose exactly what to reset
3. **Error Handling**: Continues even if one database fails
4. **Summary Report**: Shows what succeeded/failed
5. **Skip Options**: Preserve important data (e.g., `--skip-neo4j`)

## When to Reset

### Always Reset After:
- Running integration tests
- Experimenting with new features
- Corrupted data or errors
- Major schema changes
- Switching between projects

### Consider NOT Resetting:
- Production data (obviously!)
- When graph structure took hours to build
- During active development (use `--skip-neo4j`)
- When debugging requires previous state

## Help

```bash
# Show all options
./reset.sh --help

# Or
python reset_databases.py --help
```

## Files

- `reset_databases.py` - Main Python script (detailed, flexible)
- `reset.sh` - Bash wrapper (quick access)
- `RESET_GUIDE.md` - This file (documentation)

## Configuration

The script reads database settings from `.env` in the same directory:

```bash
# Relational Database
DB_PROVIDER="sqlite"
DB_NAME=cognee_db

# Graph Database
GRAPH_DATABASE_PROVIDER="neo4j"
GRAPH_DATABASE_URL=bolt://localhost:7687
GRAPH_DATABASE_USERNAME=neo4j
GRAPH_DATABASE_PASSWORD=semantic-search

# Vector Database
VECTOR_DB_PROVIDER="qdrant"
VECTOR_DB_URL=http://localhost:6333
```

## Support

If you encounter issues:

1. Run with `--dry-run` first to diagnose
2. Check that all services are running
3. Verify credentials in `.env`
4. Check Python package dependencies
5. Review error messages in the output

---

**⚠️ Warning**: This script PERMANENTLY DELETES data. Always use `--dry-run` first when unsure.
