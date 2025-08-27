#!/bin/bash
# Quick start script for JKB Finance Insights

echo "Starting JKB Finance Insights on port 8000..."
echo "  (This will automatically stop any existing server)"

# Check if development mode is requested
if [ "$1" = "dev" ] || [ "$1" = "--dev" ]; then
    echo "  Starting in DEVELOPMENT mode with auto-reload..."
    MODE="dev"
else
    echo "  Starting in PRODUCTION mode..."
    MODE="start"
fi

# Always stop any existing server first
python3 server.py stop

# Wait a moment
sleep 1

# Start the server
python3 server.py $MODE
