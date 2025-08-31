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

# Start the server with autoreload and console output
echo "Starting server on http://$SERVER_HOST:$SERVER_PORT"
uvicorn main:app --host $SERVER_HOST --port $SERVER_PORT --reload --log-level info
