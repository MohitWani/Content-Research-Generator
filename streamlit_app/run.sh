#!/bin/bash
# Run Streamlit UI

cd "$(dirname "$0")"

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "Installing Streamlit..."
    pip install -r requirements.txt
fi

echo "Starting AI Research Agent UI..."
echo "Open http://localhost:8501 in your browser"

streamlit run app.py --server.port 8501 --server.address 0.0.0.0

