#!/bin/bash
cd "$(dirname "$0")/.."
echo "Starting RoboAdvisor Streamlit UI..."
source venv/bin/activate
./venv/bin/python -m streamlit run app/streamlit_app.py --server.port 8501