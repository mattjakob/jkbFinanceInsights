# Server Management

Easy commands to start, stop, and manage the JKB Finance Insights server.

## Quick Commands

### 🚀 Start Server
```bash
./start.sh
# or
python server.py start
```

### 🛑 Stop Server
```bash
./stop.sh
# or
python server.py stop
```

### 🔄 Restart Server
```bash
./restart.sh
# or
python server.py restart
```

### 📊 Check Status
```bash
./status.sh
# or
python server.py status
```

## Advanced Usage

### Custom Port
```bash
python server.py start --port 8004
python server.py restart --port 8004
```

### Help
```bash
python server.py --help
```

## What Each Command Does

- **start**: Starts the server on port 8000 (automatically stops any existing server)
- **stop**: Stops all running server processes
- **restart**: Stops the server and starts it again on port 8000
- **status**: Shows if the server is running, process IDs, and port availability

## Features

- ✅ **Always runs on port 8000** - Consistent port usage
- ✅ **Automatically stops existing servers** - No port conflicts
- ✅ **Multiple detection methods** - Finds processes by name, uvicorn, and port
- ✅ **Aggressive process killing** - Uses SIGKILL for stubborn processes
- ✅ **Port verification** - Double-checks port availability after stopping
- ✅ **Virtual environment detection** - Ensures proper setup
- ✅ **Clear status reporting** - Shows all running processes and port status

## Troubleshooting

If you get permission errors:
```bash
chmod +x *.sh
chmod +x server.py
```

If port is already in use:
```bash
./stop.sh
./start.sh
```

If virtual environment is missing:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
