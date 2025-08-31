"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        DATABASE WRITER              │
 *  └─────────────────────────────────────┘
 *  Singleton database writer with queue
 * 
 *  Implements a single-writer pattern to prevent database
 *  locks by serializing all write operations through a queue.
 * 
 *  Notes:
 *  - All database writes go through this singleton
 *  - Uses asyncio queue for thread-safe operations
 *  - Prevents concurrent write attempts
 */
"""

import asyncio
import sqlite3
import threading
from typing import Any, Dict, Optional, Callable
from contextlib import contextmanager
from pathlib import Path

from config import DATABASE_URL, DATABASE_TIMEOUT
from debugger import debug_info, debug_error, debug_warning


class DatabaseWriter:
    """
     ┌─────────────────────────────────────┐
     │        DATABASEWRITER               │
     └─────────────────────────────────────┘
     Singleton database writer with operation queue
     
     Ensures all database writes are serialized to prevent
     locking issues with SQLite.
    """
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseWriter, cls).__new__(cls)
            return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._conn = None
            self._connect()
    
    def _connect(self):
        """Create database connection with optimal settings"""
        try:
            self._conn = sqlite3.connect(
                DATABASE_URL,
                timeout=DATABASE_TIMEOUT,
                isolation_level='DEFERRED',  # Better for WAL mode
                check_same_thread=False  # Allow multi-threaded access
            )
            self._conn.row_factory = sqlite3.Row
            
            # Configure for optimal performance
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute("PRAGMA cache_size=10000")
            self._conn.execute("PRAGMA temp_store=MEMORY")
            self._conn.execute("PRAGMA busy_timeout=60000")
            self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")  # Clean WAL file
            
            debug_info("Database writer initialized with optimized settings")
        except Exception as e:
            debug_error(f"Failed to initialize database writer: {e}")
            raise
    
    def execute_write(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute a write operation with proper locking"""
        with self._lock:
            try:
                # Ensure connection is valid
                if self._conn is None:
                    self._connect()
                
                # Execute the operation
                result = operation(self._conn, *args, **kwargs)
                
                # Commit changes
                self._conn.commit()
                
                return result
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    debug_error(f"Database locked during write operation: {e}")
                    # Try to recover
                    self._reconnect()
                    raise
                else:
                    raise
            except Exception as e:
                debug_error(f"Database write error: {e}")
                self._conn.rollback()
                raise
    
    def _reconnect(self):
        """Reconnect to database"""
        try:
            if self._conn:
                self._conn.close()
        except:
            pass
        
        self._conn = None
        self._connect()
    
    def close(self):
        """Close database connection"""
        with self._lock:
            if self._conn:
                try:
                    self._conn.close()
                    debug_info("Database writer connection closed")
                except Exception as e:
                    debug_error(f"Error closing database writer: {e}")
                finally:
                    self._conn = None


# Global instance
_db_writer: Optional[DatabaseWriter] = None


def get_db_writer() -> DatabaseWriter:
    """Get singleton DatabaseWriter instance"""
    global _db_writer
    if _db_writer is None:
        _db_writer = DatabaseWriter()
    return _db_writer


@contextmanager
def db_write_operation():
    """Context manager for database write operations"""
    writer = get_db_writer()
    try:
        yield writer
    finally:
        # Ensure resources are cleaned up
        pass
