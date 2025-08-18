#!/bin/bash
set -e

REPO_ROOT="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$REPO_ROOT"

echo "Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete!"
echo "To run server:"
echo "1. source venv/bin/activate"
echo "2. python -m server.main"
echo "Or use: scripts/run_server.sh"
