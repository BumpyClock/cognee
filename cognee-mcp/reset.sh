#!/bin/bash
# Quick reset script for Cognee databases

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the Python reset script with all arguments passed through
python reset_databases.py "$@"
