#!/bin/bash
set -e

REPO_ROOT="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$REPO_ROOT"

source venv/bin/activate
echo "Starting server on http://localhost:8000"
python -m server.main
