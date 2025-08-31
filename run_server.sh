#!/bin/bash

#  ┌─────────────────────────────────────┐
#  │            RUN_SERVER              │
#  └─────────────────────────────────────┘
#  Initializes the environment, checks installations, and runs the server.
#
#  This script sets up the Python virtual environment, installs dependencies,
#  kills any existing server processes, and starts the server with autoreload
#  and console output enabled.
#
#  Notes:
#  - Ensure you have Python 3.8+ installed.
#  - Customize the SERVER_HOST and SERVER_PORT in the .env file.

# Load environment variables
if [ -f .env ]; then
  # Export only valid environment variables (skip comments and empty lines)
  export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Kill any existing server processes
echo "Stopping any existing server processes..."
pkill -f "uvicorn main:app" 2>/dev/null || true
# Also kill any process on port 8000
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
sleep 1

# Set default values if not defined in .env
SERVER_HOST=${SERVER_HOST:-0.0.0.0}
SERVER_PORT=${SERVER_PORT:-8000}

# Function to cleanup on exit
cleanup() {
    echo "🛑 Force killing server processes..."
    # Kill the background uvicorn process
    if [ ! -z "$SERVER_PID" ]; then
        kill -9 $SERVER_PID 2>/dev/null || true
    fi
    # Kill all uvicorn processes
    pkill -9 -f "uvicorn main:app" 2>/dev/null || true
    pkill -9 -f "uvicorn" 2>/dev/null || true
    # Kill processes on the port
    lsof -ti :$SERVER_PORT | xargs kill -9 2>/dev/null || true
    # Kill any Python processes in this directory
    pkill -9 -f "jkbFinanceInsights" 2>/dev/null || true
    echo "💀 All server processes killed"
    exit 0
}

# Set trap for cleanup on SIGINT and SIGTERM
trap cleanup SIGINT SIGTERM

# Start the server with autoreload and console output
echo "Starting server on http://$SERVER_HOST:$SERVER_PORT"
echo "Press Ctrl+C to stop the server"
uvicorn main:app --host $SERVER_HOST --port $SERVER_PORT --log-level info &

# Wait for the background process
SERVER_PID=$!
wait $SERVER_PID
