#!/bin/bash
# Quick restart script for JKB Finance Insights

echo "Restarting JKB Finance Insights on port 8000..."
echo "  (This will automatically stop any existing server)"

# Check if development mode is requested
if [ "$1" = "dev" ] || [ "$1" = "--dev" ]; then
    echo "  Restarting in DEVELOPMENT mode with auto-reload..."
    MODE="dev"
else
    echo "  Restarting in PRODUCTION mode..."
    MODE="start"
fi

# Restart the server (which includes stopping first)
python3 server.py restart --reload
