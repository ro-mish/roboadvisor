#!/bin/bash
set -e

REPO_ROOT="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$REPO_ROOT"

source venv/bin/activate
echo "Starting Streamlit UI on http://localhost:8501"
streamlit run app/streamlit_app.py
