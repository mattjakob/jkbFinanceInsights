#!/usr/bin/env python3
"""
 ┌─────────────────────────────────────┐
 │         TASKS_RESET_SCRIPT          │
 └─────────────────────────────────────┘
 Command-line script to reset all tasks and clear the queue

 This script provides a comprehensive way to stop all background workers,
 clear the task queue, and reset the system state from the command line.
"""

import asyncio
import sqlite3
import sys
from pathlib import Path

def clear_all_tasks_direct():
    """
     ┌─────────────────────────────────────┐
     │      CLEAR_ALL_TASKS_DIRECT         │
     └─────────────────────────────────────┘
     Clear all tasks directly from database
     
     Bypasses the task manager to directly clear all tasks
     from the database. This is useful when the workers
     are not running or accessible.
     
     Returns:
     - int: Number of tasks cleared
    """
    db_path = Path("finance_insights.db")
    if not db_path.exists():
        print("Database not found. No tasks to clear.")
        return 0
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current task count and status breakdown
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM async_tasks 
            GROUP BY status
        """)
        status_counts = cursor.fetchall()
        
        cursor.execute("SELECT COUNT(*) FROM async_tasks")
        total_tasks = cursor.fetchone()[0]
        
        if total_tasks == 0:
            print("No tasks found in database.")
            conn.close()
            return 0
        
        # Show task breakdown before clearing
        print(f"📊 Current task status breakdown:")
        for status, count in status_counts:
            print(f"   {status}: {count} tasks")
        print()
        
        # Clear all tasks
        cursor.execute("DELETE FROM async_tasks")
        conn.commit()
        conn.close()
        
        print(f"🗑️  Cleared {total_tasks} tasks from database.")
        return total_tasks
        
    except Exception as e:
        print(f"❌ Error clearing tasks: {e}")
        return 0

def check_worker_processes():
    """
     ┌─────────────────────────────────────┐
     │      CHECK_WORKER_PROCESSES         │
     └─────────────────────────────────────┘
     Check for running worker processes
     
     Looks for Python processes that might be running
     the finance insights server or workers.
     
     Returns:
     - bool: True if workers are running
    """
    try:
        import psutil
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python3' or proc.info['name'] == 'python':
                    cmdline = proc.info['cmdline']
                    if cmdline and any('server.py' in arg for arg in cmdline):
                        print(f"Found running server process: PID {proc.info['pid']}")
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return False
        
    except ImportError:
        print("Note: psutil not available, skipping process check")
        return False

def main():
    """
     ┌─────────────────────────────────────┐
     │              MAIN                   │
     └─────────────────────────────────────┘
     Main execution function
     
     Provides command-line interface to stop workers
     and clear tasks.
    """
    print("🔄 Tasks Reset Script")
    print("=" * 40)
    
    # Check if workers are running
    workers_running = check_worker_processes()
    
    if workers_running:
        print("⚠️  Warning: Server processes appear to be running.")
        print("   Consider stopping the server first for clean shutdown.")
        print()
    
    # Clear tasks
    print("🗑️  Clearing all tasks from database...")
    cleared_count = clear_all_tasks_direct()
    
    if cleared_count > 0:
        print(f"✅ Successfully cleared {cleared_count} tasks.")
    else:
        print("✅ No tasks to clear.")
    
    print()
    print("📋 Next steps:")
    print("   1. If server is running, restart it to clear worker state")
    print("   2. Or use the API endpoints:")
    print("      - POST /api/tasks/stop-all")
    print("      - POST /api/tasks/clear-all")
    print("      - POST /api/tasks/restart-workers")
    print("   3. Check tasks status: GET /tasks")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
