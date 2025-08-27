#!/bin/bash
# Development script for JKB Finance Insights

echo "Starting JKB Finance Insights in DEVELOPMENT mode..."
echo "  Port: 8000"
echo "  Auto-reload: Enabled"
echo "  Watching: All files in current directory"

# Always stop any existing server first
python3 server.py stop

# Wait a moment
sleep 1

# Start the server in development mode
python3 server.py dev

echo ""
echo "Development server started!"
echo "  - Server will auto-reload when files change"
echo "  - Press Ctrl+C to stop"
echo "  - Access at: http://localhost:8000"
