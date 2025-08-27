#!/bin/bash
# Run the Australian Postcodes MCP Server

echo "Starting Australian Postcodes MCP Server..."
echo "========================================"

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f ".deps_installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    touch .deps_installed
fi

# Run the server
echo "Starting server..."
python3 src/server.py "$@"