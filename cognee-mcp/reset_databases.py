#!/usr/bin/env python3
"""
Database Reset Script for Cognee MCP

This script resets all Cognee databases to a clean state:
- SQLite/Postgres relational database
- Neo4j graph database
- Qdrant vector database (if configured)
- File-based databases (Kuzu, LanceDB)

Usage:
    python reset_databases.py [options]

Options:
    --all               Reset all databases (default)
    --sqlite            Reset only the relational database (SQLite/Postgres)
    --neo4j             Reset only Neo4j database
    --qdrant            Reset only Qdrant database
    --files             Reset only file-based databases
    --skip-neo4j        Reset all except Neo4j
    --dry-run           Show what would be deleted without deleting
    -h, --help          Show this help message

Examples:
    python reset_databases.py                    # Reset all databases
    python reset_databases.py --neo4j            # Reset only Neo4j
    python reset_databases.py --skip-neo4j       # Reset all except Neo4j
    python reset_databases.py --dry-run          # Preview what would be deleted
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
from typing import List, Tuple

# Import Postgres drivers if available
POSTGRES_AVAILABLE = False
POSTGRES_DRIVER = None

try:  # psycopg (v3)
    import psycopg  # type: ignore

    POSTGRES_AVAILABLE = True
    POSTGRES_DRIVER = "psycopg"
except ImportError:
    try:  # psycopg2 fallback
        import psycopg2  # type: ignore

        POSTGRES_AVAILABLE = True
        POSTGRES_DRIVER = "psycopg2"
    except ImportError:
        POSTGRES_AVAILABLE = False
        POSTGRES_DRIVER = None

# Import neo4j driver if available
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Warning: neo4j package not installed. Neo4j reset will be skipped.")

# Import qdrant client if available
try:
    from qdrant_client import QdrantClient
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False


def load_env_file(env_path: Path) -> dict:
    """Load environment variables from .env file."""
    env_vars = {}
    if not env_path.exists():
        print(f"Warning: .env file not found at {env_path}")
        return env_vars

    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip().strip('"').strip("'")

    return env_vars


def find_sqlite_databases(base_dir: Path, env_vars: dict) -> List[Path]:
    """Find all SQLite database files."""
    db_files = []

    # Check for explicit DB_NAME in env
    db_name = env_vars.get('DB_NAME', 'cognee_db')

    # Common SQLite locations
    search_paths = [
        base_dir / '.venv',
        base_dir.parent / '.cognee_system',
        Path.home() / '.cognee' / 'system',
    ]

    # Add custom DATA_ROOT_DIRECTORY if specified
    if 'SYSTEM_ROOT_DIRECTORY' in env_vars:
        system_root = Path(env_vars['SYSTEM_ROOT_DIRECTORY'])
        if system_root.exists():
            search_paths.append(system_root)

    for search_path in search_paths:
        if not search_path.exists():
            continue

        # Find .db and .sqlite files
        for ext in ['*.db', '*.sqlite', '*.sqlite3']:
            for db_file in search_path.rglob(ext):
                # Filter by DB_NAME if possible
                if db_name in str(db_file) or 'cognee' in str(db_file).lower():
                    db_files.append(db_file)

    return list(set(db_files))  # Remove duplicates


def find_file_databases(base_dir: Path, env_vars: dict) -> List[Tuple[str, Path]]:
    """Find file-based databases (Kuzu, LanceDB)."""
    file_dbs = []

    # Common database directories - focus on data directories only
    search_paths = [
        base_dir.parent / '.cognee_system',
        base_dir.parent / '.cognee_data',
        Path.home() / '.cognee',
    ]

    # Add custom directories if specified
    if 'DATA_ROOT_DIRECTORY' in env_vars:
        data_root = Path(env_vars['DATA_ROOT_DIRECTORY'])
        if not data_root.as_posix().startswith('s3://') and data_root.exists():
            search_paths.append(data_root)

    if 'SYSTEM_ROOT_DIRECTORY' in env_vars:
        system_root = Path(env_vars['SYSTEM_ROOT_DIRECTORY'])
        if not system_root.as_posix().startswith('s3://') and system_root.exists():
            search_paths.append(system_root)

    # Paths to exclude (source code, tests, packages)
    exclude_patterns = [
        'site-packages',
        'node_modules',
        'tests',
        '__pycache__',
        '.git',
        'src',
        'cognee/modules',
        'cognee/tasks',
        'cognee/infrastructure',
    ]

    def should_exclude(path: Path) -> bool:
        """Check if path should be excluded from deletion."""
        path_str = str(path)
        return any(pattern in path_str for pattern in exclude_patterns)

    for search_path in search_paths:
        if not search_path.exists():
            continue

        # Look for Kuzu databases (*.kuzu directories)
        for kuzu_dir in search_path.rglob('*.kuzu'):
            if kuzu_dir.is_dir() and not should_exclude(kuzu_dir):
                file_dbs.append(('Kuzu', kuzu_dir))

        # Look for LanceDB databases (*.lance directories or .lancedb parent dirs)
        for lance_dir in search_path.rglob('*.lance'):
            if lance_dir.is_dir() and not should_exclude(lance_dir):
                file_dbs.append(('LanceDB', lance_dir))

        # Look for .lancedb directories
        for lancedb_dir in search_path.rglob('*.lancedb'):
            if lancedb_dir.is_dir() and not should_exclude(lancedb_dir):
                file_dbs.append(('LanceDB', lancedb_dir))

    return list(set(file_dbs))  # Remove duplicates


def reset_neo4j(env_vars: dict, dry_run: bool = False) -> bool:
    """Reset Neo4j database by deleting all nodes and relationships."""
    if not NEO4J_AVAILABLE:
        print("⚠️  Neo4j driver not available. Skipping Neo4j reset.")
        return False

    neo4j_url = env_vars.get('GRAPH_DATABASE_URL', 'bolt://localhost:7687')
    neo4j_user = env_vars.get('GRAPH_DATABASE_USERNAME', 'neo4j')
    neo4j_password = env_vars.get('GRAPH_DATABASE_PASSWORD', 'neo4j')

    print(f"\n🗑️  Neo4j Database: {neo4j_url}")

    if dry_run:
        print("   [DRY RUN] Would delete all nodes and relationships")
        return True

    try:
        driver = GraphDatabase.driver(neo4j_url, auth=(neo4j_user, neo4j_password))

        with driver.session() as session:
            # Delete all relationships first
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = result.single()['count']
            print(f"   Deleting {rel_count} relationships...")
            session.run("MATCH ()-[r]->() DELETE r")

            # Delete all nodes
            result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = result.single()['count']
            print(f"   Deleting {node_count} nodes...")
            session.run("MATCH (n) DELETE n")

            # Verify cleanup
            result = session.run("MATCH (n) RETURN count(n) as count")
            remaining = result.single()['count']

            if remaining == 0:
                print("   ✅ Neo4j database cleared successfully")
            else:
                print(f"   ⚠️  Warning: {remaining} nodes remaining")

        driver.close()
        return True

    except Exception as e:
        print(f"   ❌ Failed to reset Neo4j: {e}")
        print(f"   Make sure Neo4j is running and credentials are correct")
        return False


def reset_qdrant(env_vars: dict, dry_run: bool = False) -> bool:
    """Reset Qdrant database by deleting all collections."""
    if not QDRANT_AVAILABLE:
        print("⚠️  Qdrant client not available. Skipping Qdrant reset.")
        return False

    qdrant_url = env_vars.get('VECTOR_DB_URL', 'http://localhost:6333')
    qdrant_key = env_vars.get('VECTOR_DB_KEY')

    if not qdrant_url:
        print("⚠️  Qdrant URL not configured. Skipping Qdrant reset.")
        return False

    print(f"\n🗑️  Qdrant Database: {qdrant_url}")

    if dry_run:
        print("   [DRY RUN] Would delete all collections")
        return True

    try:
        client = QdrantClient(url=qdrant_url, api_key=qdrant_key)
        collections = client.get_collections().collections

        if not collections:
            print("   ✅ No collections found (already empty)")
            return True

        print(f"   Deleting {len(collections)} collections...")
        for collection in collections:
            print(f"   - Deleting collection: {collection.name}")
            client.delete_collection(collection.name)

        print("   ✅ Qdrant database cleared successfully")
        return True

    except Exception as e:
        print(f"   ❌ Failed to reset Qdrant: {e}")
        return False


def reset_postgres(env_vars: dict, dry_run: bool = False) -> bool:
    """Reset Postgres database by dropping and recreating the public schema."""
    if not POSTGRES_AVAILABLE or POSTGRES_DRIVER is None:
        print("⚠️  Postgres driver not available. Skipping Postgres reset.")
        return False

    db_host = env_vars.get('DB_HOST', '127.0.0.1')
    db_port = env_vars.get('DB_PORT', '5432')
    db_name = env_vars.get('DB_NAME', 'cognee_db')
    db_user = env_vars.get('DB_USERNAME', 'cognee')
    db_password = env_vars.get('DB_PASSWORD', '')

    print(f"\n🗑️  Postgres Database: {db_user}@{db_host}:{db_port}/{db_name}")

    if dry_run:
        print("   [DRY RUN] Would drop and recreate the 'public' schema (includes pgvector tables)")
        return True

    try:
        if POSTGRES_DRIVER == "psycopg":
            conn = psycopg.connect(
                host=db_host,
                port=db_port,
                dbname=db_name,
                user=db_user,
                password=db_password,
            )
        else:
            conn = psycopg2.connect(  # type: ignore[name-defined]
                host=db_host,
                port=db_port,
                dbname=db_name,
                user=db_user,
                password=db_password,
            )

        conn.autocommit = True

        with conn.cursor() as cursor:  # type: ignore[attr-defined]
            cursor.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema');"
            )
            table_count = cursor.fetchone()[0]
            print(f"   Found {table_count} user table(s) to remove...")

            cleanup_commands = [
                "DROP SCHEMA IF EXISTS public CASCADE;",
                "CREATE SCHEMA public;",
                "GRANT ALL ON SCHEMA public TO CURRENT_USER;",
                "GRANT ALL ON SCHEMA public TO public;",
            ]

            for command in cleanup_commands:
                cursor.execute(command)

            if env_vars.get('VECTOR_DB_PROVIDER', '').lower() == 'pgvector':
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        conn.close()
        print("   ✅ Postgres database cleared successfully")
        return True

    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"   ❌ Failed to reset Postgres: {exc}")
        print("   Ensure credentials are correct and the user has permission to manage schemas.")
        try:
            conn.close()
        except Exception:
            pass
        return False


def reset_sqlite(db_files: List[Path], dry_run: bool = False) -> bool:
    """Reset SQLite databases by deleting the files."""
    if not db_files:
        print("\n⚠️  No SQLite databases found")
        return False

    print(f"\n🗑️  SQLite Databases ({len(db_files)} found):")

    success = True
    for db_file in db_files:
        print(f"   - {db_file}")
        if dry_run:
            print(f"     [DRY RUN] Would delete")
        else:
            try:
                db_file.unlink()
                print(f"     ✅ Deleted")
            except Exception as e:
                print(f"     ❌ Failed: {e}")
                success = False

    return success


def reset_relational(env_vars: dict, sqlite_dbs: List[Path], dry_run: bool = False) -> bool:
    """Reset the configured relational database (SQLite or Postgres)."""
    provider = env_vars.get('DB_PROVIDER', 'sqlite').lower()

    if provider == 'sqlite':
        return reset_sqlite(sqlite_dbs, dry_run)

    if provider.startswith('postgres'):
        return reset_postgres(env_vars, dry_run)

    print(f"\n⚠️  Unsupported relational database provider '{provider}'.")
    return False


def reset_file_databases(file_dbs: List[Tuple[str, Path]], dry_run: bool = False) -> bool:
    """Reset file-based databases by deleting directories."""
    if not file_dbs:
        print("\n⚠️  No file-based databases found")
        return False

    print(f"\n🗑️  File-based Databases ({len(file_dbs)} found):")

    success = True
    for db_type, db_path in file_dbs:
        print(f"   - {db_type}: {db_path}")
        if dry_run:
            print(f"     [DRY RUN] Would delete directory")
        else:
            try:
                shutil.rmtree(db_path)
                print(f"     ✅ Deleted")
            except Exception as e:
                print(f"     ❌ Failed: {e}")
                success = False

    return success


def main():
    parser = argparse.ArgumentParser(
        description="Reset Cognee databases to a clean state",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--all', action='store_true', help='Reset all databases (default)')
    parser.add_argument('--sqlite', action='store_true', help='Reset only the relational database (SQLite/Postgres)')
    parser.add_argument('--neo4j', action='store_true', help='Reset only Neo4j database')
    parser.add_argument('--qdrant', action='store_true', help='Reset only Qdrant database')
    parser.add_argument('--files', action='store_true', help='Reset only file-based databases')
    parser.add_argument('--skip-neo4j', action='store_true', help='Reset all except Neo4j')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted')

    args = parser.parse_args()

    # Determine what to reset
    reset_all = args.all or not (args.sqlite or args.neo4j or args.qdrant or args.files or args.skip_neo4j)

    # Load environment variables
    script_dir = Path(__file__).parent
    env_file = script_dir / '.env'
    env_vars = load_env_file(env_file)

    print("=" * 80)
    print("🔄 Cognee Database Reset Script")
    print("=" * 80)

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No actual changes will be made\n")

    relational_provider = env_vars.get('DB_PROVIDER', 'sqlite')

    # Find databases
    sqlite_dbs = []
    if relational_provider.lower() == 'sqlite':
        sqlite_dbs = find_sqlite_databases(script_dir, env_vars)
    file_dbs = find_file_databases(script_dir, env_vars)

    # Track results
    results = []

    # Reset SQLite
    if (reset_all or args.sqlite) and not args.skip_neo4j:
        provider_display = relational_provider or 'sqlite'
        provider_lower = provider_display.lower()
        if provider_lower == 'sqlite':
            provider_display = 'SQLite'
        elif provider_lower.startswith('postgres'):
            provider_display = 'Postgres'
        else:
            provider_display = provider_display

        relational_label = f"Relational ({provider_display})"
        results.append((relational_label, reset_relational(env_vars, sqlite_dbs, args.dry_run)))

    # Reset Neo4j
    if (reset_all or args.neo4j) and not args.skip_neo4j:
        if env_vars.get('GRAPH_DATABASE_PROVIDER') == 'neo4j':
            results.append(('Neo4j', reset_neo4j(env_vars, args.dry_run)))
        else:
            print("\n⚠️  Neo4j not configured as graph database provider")

    # Reset Qdrant
    if (reset_all or args.qdrant) and not args.skip_neo4j:
        if env_vars.get('VECTOR_DB_PROVIDER') == 'qdrant':
            results.append(('Qdrant', reset_qdrant(env_vars, args.dry_run)))
        else:
            print("\n⚠️  Qdrant not configured as vector database provider")

    # Reset file databases
    if (reset_all or args.files) and not args.skip_neo4j:
        results.append(('File DBs', reset_file_databases(file_dbs, args.dry_run)))

    # Summary
    print("\n" + "=" * 80)
    print("📊 Summary")
    print("=" * 80)

    if not results:
        print("⚠️  No databases were reset")
    else:
        for db_name, success in results:
            status = "✅ Success" if success else "❌ Failed"
            print(f"   {db_name}: {status}")

    if args.dry_run:
        print("\n💡 Run without --dry-run to actually delete databases")

    print()


if __name__ == '__main__':
    main()
