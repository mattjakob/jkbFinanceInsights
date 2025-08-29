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
  export $(cat .env | xargs)
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Kill any existing server processes
pkill -f "uvicorn main:app"

# Start the server with autoreload and console output
uvicorn main:app --host $SERVER_HOST --port $SERVER_PORT --reload --log-level info
