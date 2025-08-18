#!/bin/bash
cd "$(dirname "$0")/.."
echo "Starting RoboAdvisor API server..."
source venv/bin/activate
./venv/bin/python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload