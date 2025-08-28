#!/usr/bin/env python3
"""
 ┌─────────────────────────────────────┐
 │         SERVER MANAGEMENT           │
 └─────────────────────────────────────┘
 Easy server management for JKB Finance Insights
 
 Provides simple commands to start, stop, and restart the server.
"""

import os
import sys
import subprocess
import signal
import time
import argparse
from pathlib import Path
from debugger import debug_info, debug_warning, debug_error, debug_success
from config import (
    APP_NAME, MAIN_FILE, DEFAULT_PORT, VENV_ACTIVATE,
    UVICORN_HOST, UVICORN_RELOAD, UVICORN_RELOAD_DIR, UVICORN_LOG_LEVEL,
    get_uvicorn_command, get_server_info
)

def get_python_processes():
    """Get all running Python processes for this app"""
    pids = []
    
    # Method 1: pgrep for python processes running main.py
    try:
        result = subprocess.run(['pgrep', '-f', f'python.*{MAIN_FILE}'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids.extend(result.stdout.strip().split('\n'))
    except Exception:
        pass
    
    # Method 2: pgrep for uvicorn processes
    try:
        result = subprocess.run(['pgrep', '-f', 'uvicorn'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids.extend(result.stdout.strip().split('\n'))
    except Exception:
        pass
    
    # Method 3: lsof for port 8000
    try:
        result = subprocess.run(['lsof', '-ti', f':{DEFAULT_PORT}'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids.extend(result.stdout.strip().split('\n'))
    except Exception:
        pass
    
    # Remove duplicates and empty strings
    pids = list(set([pid.strip() for pid in pids if pid.strip()]))
    return pids

def kill_processes(pids):
    """Kill processes by PID"""
    for pid in pids:
        if pid.strip():
            try:
                os.kill(int(pid), signal.SIGTERM)
                debug_info(f"  Killed process {pid}")
            except Exception as e:
                debug_error(f"  Error killing process {pid}: {e}")

def stop_server():
    """Stop the running server"""
    debug_info(f"Stopping {APP_NAME}...")
    
    # First, try to kill any processes using port 8000
    try:
        result = subprocess.run(['lsof', '-ti', f':{DEFAULT_PORT}'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            port_pids = result.stdout.strip().split('\n')
            for pid in port_pids:
                if pid.strip():
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                        debug_info(f"  Killed process {pid} using port {DEFAULT_PORT}")
                    except Exception as e:
                        debug_error(f"  Error killing port process {pid}: {e}")
    except Exception:
        pass
    
    # Then kill all Python processes related to our app
    pids = get_python_processes()
    if pids:
        debug_info(f"  Found {len(pids)} related process(es)")
        kill_processes(pids)
    else:
        debug_info("  No related processes found")
    
    # Wait longer for processes to terminate
    time.sleep(3)
    
    # Force kill any remaining processes
    remaining = get_python_processes()
    if remaining:
        debug_warning("  Force killing remaining processes...")
        for pid in remaining:
            try:
                os.kill(int(pid), signal.SIGKILL)
                debug_info(f"  Force killed process {pid}")
            except Exception as e:
                debug_error(f"  Error force killing process {pid}: {e}")
    
    # Final check - kill anything still using port 8000
    try:
        result = subprocess.run(['lsof', '-ti', f':{DEFAULT_PORT}'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            final_pids = result.stdout.strip().split('\n')
            for pid in final_pids:
                if pid.strip():
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                        debug_info(f"  Final kill for process {pid} on port {DEFAULT_PORT}")
                    except Exception as e:
                        debug_error(f"  Error in final kill for {pid}: {e}")
    except Exception:
        pass
    
    debug_success("Server stopped")

def start_server(port=None, reload=None):
    """Start the server"""
    if port is None:
        port = DEFAULT_PORT
    
    # Default to auto-reload if not specified
    if reload is None:
        reload = True  # Always default to auto-reload
    
    mode = "Development (Auto-reload)" if reload else "Production"
    debug_info(f"Starting {APP_NAME} on port {port} in {mode} mode...")
    
    # Always stop any existing server first
    debug_info("  Ensuring no existing server is running...")
    stop_server()
    time.sleep(2)
    
    # Check if virtual environment exists
    if not Path(VENV_ACTIVATE).exists():
        debug_error("ERROR: Virtual environment not found!")
        debug_error("   Please run: python3 -m venv .venv")
        debug_error("   Then: source .venv/bin/activate")
        debug_error("   And: pip install -r requirements.txt")
        return False
    
    # Check if main.py exists
    if not Path(MAIN_FILE).exists():
        debug_error(f"ERROR: {MAIN_FILE} not found!")
        return False
    
    # Double-check port is available after stopping
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                debug_info(f"  Port {port} is available")
                break
        except OSError:
            if attempt < max_attempts - 1:
                debug_warning(f"  Port {port} still in use, waiting... (attempt {attempt + 1}/{max_attempts})")
                time.sleep(1)
            else:
                debug_error(f"ERROR: Port {port} is still in use after multiple attempts!")
                debug_error("   There may be another application using this port")
                return False
    
    try:
        # Start the server
        if reload:
            # Development mode with auto-reload
            uvicorn_cmd = get_uvicorn_command(port)
            cmd = f"cd {os.getcwd()} && source {VENV_ACTIVATE} && {uvicorn_cmd}"
            debug_info(f"  Running: {cmd}")
        else:
            # Production mode
            cmd = f"cd {os.getcwd()} && source {VENV_ACTIVATE} && python {MAIN_FILE}"
            debug_info(f"  Running: {cmd}")
        
        # Use subprocess.Popen to start the server
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment to see if it starts successfully
        time.sleep(3)
        
        if process.poll() is None:
            debug_success(f"Server started successfully on port {port}")
            debug_info(f"  Process ID: {process.pid}")
            debug_info(f"  Access at: http://localhost:{port}")
            return True
        else:
            stdout, stderr = process.communicate()
            debug_error("ERROR: Server failed to start!")
            if stderr:
                debug_error(f"  Error: {stderr}")
            return False
            
    except Exception as e:
        debug_error(f"ERROR: Error starting server: {e}")
        return False

def restart_server(port=None, reload=None):
    """Restart the server"""
    debug_info(f"Restarting {APP_NAME}...")
    stop_server()
    time.sleep(1)
    return start_server(port, reload)

def status():
    """Show server status"""
    debug_info(f"{APP_NAME}")
    debug_info("=" * 50)
    
    pids = get_python_processes()
    if pids:
        debug_success(f"Status: Running")
        debug_info(f"Process IDs: {', '.join(pids)}")
        debug_info(f"Port: {DEFAULT_PORT}")
        debug_info(f"URL: http://localhost:{DEFAULT_PORT}")
    else:
        debug_warning("Status: Not running")
    
    debug_info("\nEnvironment:")
    debug_info(f"  main.py: {'Available' if Path(MAIN_FILE).exists() else 'Missing'}")
    debug_info(f"  venv: {'Available' if Path(VENV_ACTIVATE).exists() else 'Missing'}")
    
    # Check port availability
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', DEFAULT_PORT))
            debug_info(f"  Port {DEFAULT_PORT}: Available")
    except OSError:
        debug_warning(f"  Port {DEFAULT_PORT}: In use")

def config():
    """Show current configuration"""
    from config import get_config_summary
    
    debug_info(f"{APP_NAME} Configuration")
    debug_info("=" * 50)
    
    config_data = get_config_summary()
    
    debug_info("Server Configuration:")
    debug_info(f"  Host: {config_data['server']['host']}")
    debug_info(f"  Port: {config_data['server']['port']}")
    debug_info(f"  Auto-reload: {config_data['server']['reload']}")
    debug_info(f"  Workers: {config_data['server']['workers']}")
    
    debug_info("\nDatabase Configuration:")
    debug_info(f"  URL: {config_data['database']['url']}")
    
    debug_info("\nEnvironment:")
    debug_info(f"  Mode: {config_data['environment']['mode']}")
    debug_info(f"  Debug: {config_data['environment']['debug']}")
    
    debug_info("\nUvicorn Configuration:")
    debug_info(f"  Host: {config_data['uvicorn']['host']}")
    debug_info(f"  Log Level: {config_data['uvicorn']['log_level']}")
    
    debug_info("\nConfiguration Source:")
    debug_info(f"  .env file: {'Found' if Path('.env').exists() else 'Not found'}")
    debug_info(f"  Using defaults: {'Yes' if not Path('.env').exists() else 'No'}")

def main():
    parser = argparse.ArgumentParser(
        description=f'Manage {APP_NAME} server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python server.py start     # Start server with auto-reload on default port 8000
  python server.py dev       # Start server with auto-reload (development)
  python server.py stop      # Stop running server
  python server.py restart   # Restart server with auto-reload
  python server.py status    # Show server status
  python server.py config    # Show current configuration
        """
    )
    parser.add_argument('action', choices=['start', 'dev', 'stop', 'restart', 'status', 'config'], 
                       help='Action to perform')
    parser.add_argument('--port', '-p', type=int, default=DEFAULT_PORT,
                       help=f'Port to use (default: {DEFAULT_PORT})')
    parser.add_argument('--reload', '-r', action='store_true',
                       help='Enable auto-reload (development mode)')
    
    args = parser.parse_args()
    
    if args.action == 'start':
        start_server(args.port, reload=True)  # Always use auto-reload for start
    elif args.action == 'dev':
        start_server(args.port, reload=True)
    elif args.action == 'stop':
        stop_server()
    elif args.action == 'restart':
        restart_server(args.port, reload=True)  # Always use auto-reload for restart
    elif args.action == 'status':
        status()
    elif args.action == 'config':
        config()

if __name__ == "__main__":
    main()
