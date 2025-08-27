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
                print(f"  Killed process {pid}")
            except Exception as e:
                print(f"  Error killing process {pid}: {e}")

def stop_server():
    """Stop the running server"""
    print(f"Stopping {APP_NAME}...")
    
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
                        print(f"  Killed process {pid} using port {DEFAULT_PORT}")
                    except Exception as e:
                        print(f"  Error killing port process {pid}: {e}")
    except Exception:
        pass
    
    # Then kill all Python processes related to our app
    pids = get_python_processes()
    if pids:
        print(f"  Found {len(pids)} related process(es)")
        kill_processes(pids)
    else:
        print("  No related processes found")
    
    # Wait longer for processes to terminate
    time.sleep(3)
    
    # Force kill any remaining processes
    remaining = get_python_processes()
    if remaining:
        print("  Force killing remaining processes...")
        for pid in remaining:
            try:
                os.kill(int(pid), signal.SIGKILL)
                print(f"  Force killed process {pid}")
            except Exception as e:
                print(f"  Error force killing process {pid}: {e}")
    
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
                        print(f"  Final kill for process {pid} on port {DEFAULT_PORT}")
                    except Exception as e:
                        print(f"  Error in final kill for {pid}: {e}")
    except Exception:
        pass
    
    print("Server stopped")

def start_server(port=None, reload=False):
    """Start the server"""
    if port is None:
        port = DEFAULT_PORT
    
    mode = "Development (Auto-reload)" if reload else "Production"
    print(f"Starting {APP_NAME} on port {port} in {mode} mode...")
    
    # Always stop any existing server first
    print("  Ensuring no existing server is running...")
    stop_server()
    time.sleep(2)
    
    # Check if virtual environment exists
    if not Path(VENV_ACTIVATE).exists():
        print("ERROR: Virtual environment not found!")
        print("   Please run: python3 -m venv .venv")
        print("   Then: source .venv/bin/activate")
        print("   And: pip install -r requirements.txt")
        return False
    
    # Check if main.py exists
    if not Path(MAIN_FILE).exists():
        print(f"ERROR: {MAIN_FILE} not found!")
        return False
    
    # Double-check port is available after stopping
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                print(f"  Port {port} is available")
                break
        except OSError:
            if attempt < max_attempts - 1:
                print(f"  Port {port} still in use, waiting... (attempt {attempt + 1}/{max_attempts})")
                time.sleep(1)
            else:
                print(f"ERROR: Port {port} is still in use after multiple attempts!")
                print("   There may be another application using this port")
                return False
    
    try:
        # Start the server
        if reload:
            # Development mode with auto-reload
            uvicorn_cmd = get_uvicorn_command(port)
            cmd = f"cd {os.getcwd()} && source {VENV_ACTIVATE} && {uvicorn_cmd}"
            print(f"  Running: {cmd}")
        else:
            # Production mode
            cmd = f"cd {os.getcwd()} && source {VENV_ACTIVATE} && python {MAIN_FILE}"
            print(f"  Running: {cmd}")
        
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
            print(f"Server started successfully on port {port}")
            print(f"  Process ID: {process.pid}")
            print(f"  Access at: http://localhost:{port}")
            return True
        else:
            stdout, stderr = process.communicate()
            print("ERROR: Server failed to start!")
            if stderr:
                print(f"  Error: {stderr}")
            return False
            
    except Exception as e:
        print(f"ERROR: Error starting server: {e}")
        return False

def restart_server(port=None, reload=False):
    """Restart the server"""
    print(f"Restarting {APP_NAME}...")
    stop_server()
    time.sleep(1)
    return start_server(port, reload)

def status():
    """Show server status"""
    print(f"{APP_NAME}")
    print("=" * 50)
    
    pids = get_python_processes()
    if pids:
        print(f"Status: Running")
        print(f"Process IDs: {', '.join(pids)}")
        print(f"Port: {DEFAULT_PORT}")
        print(f"URL: http://localhost:{DEFAULT_PORT}")
    else:
        print("Status: Not running")
    
    print("\nEnvironment:")
    print(f"  main.py: {'Available' if Path(MAIN_FILE).exists() else 'Missing'}")
    print(f"  .venv: {'Available' if Path(VENV_ACTIVATE).exists() else 'Missing'}")
    
    # Check port availability
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', DEFAULT_PORT))
            print(f"  Port {DEFAULT_PORT}: Available")
    except OSError:
        print(f"  Port {DEFAULT_PORT}: In use")

def config():
    """Show current configuration"""
    from config import get_config_summary
    
    print(f"{APP_NAME} Configuration")
    print("=" * 50)
    
    config_data = get_config_summary()
    
    print("Server Configuration:")
    print(f"  Host: {config_data['server']['host']}")
    print(f"  Port: {config_data['server']['port']}")
    print(f"  Auto-reload: {config_data['server']['reload']}")
    print(f"  Workers: {config_data['server']['workers']}")
    
    print("\nDatabase Configuration:")
    print(f"  URL: {config_data['database']['url']}")
    
    print("\nEnvironment:")
    print(f"  Mode: {config_data['environment']['mode']}")
    print(f"  Debug: {config_data['environment']['debug']}")
    
    print("\nUvicorn Configuration:")
    print(f"  Host: {config_data['uvicorn']['host']}")
    print(f"  Log Level: {config_data['uvicorn']['log_level']}")
    
    print("\nConfiguration Source:")
    print(f"  .env file: {'Found' if Path('.env').exists() else 'Not found'}")
    print(f"  Using defaults: {'Yes' if not Path('.env').exists() else 'No'}")

def main():
    parser = argparse.ArgumentParser(
        description=f'Manage {APP_NAME} server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python server.py start     # Start server on default port 8000
  python server.py dev       # Start server with auto-reload (development)
  python server.py stop      # Stop running server
  python server.py restart   # Restart server
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
        start_server(args.port, args.reload)
    elif args.action == 'dev':
        start_server(args.port, reload=True)
    elif args.action == 'stop':
        stop_server()
    elif args.action == 'restart':
        restart_server(args.port, args.reload)
    elif args.action == 'status':
        status()
    elif args.action == 'config':
        config()

if __name__ == "__main__":
    main()
