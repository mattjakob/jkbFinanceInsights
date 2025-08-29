#!/usr/bin/env bash
# -----------------------------------------------------------------------------
#  JKB FINANCE INSIGHTS – START SCRIPT
# -----------------------------------------------------------------------------
#  Boots the FastAPI server with sensible defaults, ensuring that:
#    1. A Python virtual environment is present and activated.
#    2. Environment variables from .env (if present) are loaded.
#    3. Required packages are installed (only if not already satisfied).
#    4. Uvicorn is launched in auto-reload mode with console output.
#
#  Usage:
#      ./start.sh [PORT]
#
#  Parameters:
#    PORT – Optional. Overrides SERVER_PORT/.env value. Defaults to 8000.
# -----------------------------------------------------------------------------

set -euo pipefail

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_ROOT"

# -----------------------------------------------------------------------------
# Helper: Print step with prefix
# -----------------------------------------------------------------------------
log() { echo -e "\033[1;32m[START]\033[0m $1"; }

# -----------------------------------------------------------------------------
# 1. Load environment variables
# -----------------------------------------------------------------------------
if [[ -f ".env" ]]; then
  log "Loading environment from .env"
  while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
    # Trim whitespace
    key="${key##*( )}"
    key="${key%%*( )}"
    value="${value##*( )}"
    value="${value%%*( )}"
    export "$key"="$value"
  done < .env
fi

# Allow PORT override via CLI argument (highest priority)
SERVER_PORT="${1:-${SERVER_PORT:-8000}}"
export SERVER_PORT

# -----------------------------------------------------------------------------
# 2. Ensure virtual environment
# -----------------------------------------------------------------------------
VENV_DIR="$PROJECT_ROOT/venv"
if [[ ! -d "$VENV_DIR" ]]; then
  log "Creating virtual environment in ./venv"
  python3 -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"
log "Virtual environment activated"

# -----------------------------------------------------------------------------
# 3. Install dependencies if needed
# -----------------------------------------------------------------------------
if [[ -f "requirements.txt" ]]; then
  log "Installing Python dependencies (if missing)"
  pip install --quiet --upgrade -r requirements.txt
fi

# -----------------------------------------------------------------------------
# 4. Launch Uvicorn with auto-reload
# -----------------------------------------------------------------------------
HOST="${SERVER_HOST:-127.0.0.1}"
LOG_LEVEL="${UVICORN_LOG_LEVEL:-info}"

log "Starting Uvicorn on $HOST:$SERVER_PORT (reload enabled)"
exec uvicorn main:app \
  --host "$HOST" \
  --port "$SERVER_PORT" \
  --log-level "$LOG_LEVEL" \
  --reload \
  --reload-dir "$PROJECT_ROOT" \
  --access-log
