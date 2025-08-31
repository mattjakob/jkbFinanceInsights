#!/bin/bash

#  ┌─────────────────────────────────────┐
#  │           KILL_SERVER               │
#  └─────────────────────────────────────┘
#  Force kill all server processes

echo "Force killing all server processes..."

# Kill uvicorn processes
pkill -9 -f "uvicorn main:app" 2>/dev/null || true
pkill -9 -f "uvicorn" 2>/dev/null || true

# Kill Python processes running the server
pkill -9 -f "python.*main" 2>/dev/null || true

# Kill processes on port 8000
lsof -ti :8000 | xargs kill -9 2>/dev/null || true

# Kill any remaining Python processes in this directory
pkill -9 -f "jkbFinanceInsights" 2>/dev/null || true

echo "All server processes killed"
