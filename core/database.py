"""
Database connection and session management with WAL mode and retry logic.
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional
import os
from pathlib import Path
import time
import threading

from config import DATABASE_URL, DATABASE_TIMEOUT, DATABASE_MAX_RETRIES, DATABASE_RETRY_DELAY, DATABASE_WAL_MODE
from debugger import debug_info, debug_error, debug_warning


class DatabaseConfig:
    """Database configuration settings"""
    
    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url
        self.timeout = DATABASE_TIMEOUT / 1000.0  # Convert milliseconds to seconds
        self.check_same_thread = False
        self.max_retries = DATABASE_MAX_RETRIES
        self.retry_delay = DATABASE_RETRY_DELAY / 1000.0  # Convert milliseconds to seconds
        
    @property
    def connection_kwargs(self) -> dict:
        """Get kwargs for sqlite3.connect()"""
        return {
            'timeout': self.timeout,
            'check_same_thread': self.check_same_thread,
            'isolation_level': None,  # Enable autocommit mode
        }


class DatabaseManager:
    """Manages database connections and sessions with retry logic"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._write_lock = threading.Lock()
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure database file exists"""
        db_path = Path(self.config.database_url)
        if not db_path.exists():
            debug_info(f"Creating database at {db_path}")
            db_path.parent.mkdir(parents=True, exist_ok=True)
            db_path.touch()
    
    def _configure_connection(self, conn: sqlite3.Connection):
        """Configure SQLite connection with WAL mode and optimizations"""
        if DATABASE_WAL_MODE:
            try:
                # Enable WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode=WAL")
                # Set synchronous to NORMAL for better performance
                conn.execute("PRAGMA synchronous=NORMAL")
                # Increase cache size
                conn.execute("PRAGMA cache_size=10000")
                # Use memory for temp storage
                conn.execute("PRAGMA temp_store=MEMORY")
                # Set busy timeout to 60 seconds (60000ms) for better lock handling
                conn.execute("PRAGMA busy_timeout=60000")
                # Optimize for multi-threaded access
                conn.execute("PRAGMA locking_mode=EXCLUSIVE")
                # Set page size for better performance
                conn.execute("PRAGMA page_size=4096")
                # Enable mmap for better performance
                conn.execute("PRAGMA mmap_size=268435456")  # 256MB
                #debug_info("WAL mode enabled for database connection")
            except Exception as e:
                debug_warning(f"Failed to enable WAL mode: {e}")
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get raw database connection with retry logic"""
        # Retry logic happens BEFORE yielding
        conn = None
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                conn = sqlite3.connect(
                    self.config.database_url,
                    **self.config.connection_kwargs
                )
                
                # Configure connection with WAL mode and optimizations
                self._configure_connection(conn)
                
                # Connection successful, break out of retry loop
                break
                
            except sqlite3.OperationalError as e:
                last_error = e
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
                    conn = None
                    
                if "database is locked" in str(e).lower() and attempt < self.config.max_retries - 1:
                    debug_warning(f"Database locked, retrying in {self.config.retry_delay}s (attempt {attempt + 1}/{self.config.max_retries})")
                    time.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    # Either not a lock error or we're out of retries
                    raise
                    
        if conn is None:
            if last_error:
                debug_error(f"Failed to establish database connection after {self.config.max_retries} retries: {last_error}")
                raise last_error
            else:
                raise RuntimeError("Failed to establish database connection")
        
        # Now yield the connection
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    @contextmanager
    def get_session(self) -> Generator[sqlite3.Connection, None, None]:
        """Get database connection with row factory and retry logic"""
        # Retry logic happens BEFORE yielding
        conn = None
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                conn = sqlite3.connect(
                    self.config.database_url,
                    **self.config.connection_kwargs
                )
                
                # Enable row factory for dict-like access
                conn.row_factory = sqlite3.Row
                
                # Configure connection with WAL mode and optimizations
                self._configure_connection(conn)
                
                # Connection successful, break out of retry loop
                break
                
            except sqlite3.OperationalError as e:
                last_error = e
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
                    conn = None
                    
                if "database is locked" in str(e).lower() and attempt < self.config.max_retries - 1:
                    debug_warning(f"Database session locked, retrying in {self.config.retry_delay}s (attempt {attempt + 1}/{self.config.max_retries})")
                    time.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    # Either not a lock error or we're out of retries
                    raise
                    
        if conn is None:
            if last_error:
                debug_error(f"Failed to establish database session after {self.config.max_retries} retries: {last_error}")
                raise last_error
            else:
                raise RuntimeError("Failed to establish database session")
        
        # Now yield the connection
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    @contextmanager
    def get_write_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get database connection for write operations with exclusive lock"""
        with _db_write_lock:
            # Use regular connection but with global write lock
            with self.get_connection() as conn:
                yield conn
    
    @contextmanager
    def get_write_session(self) -> Generator[sqlite3.Connection, None, None]:
        """Get database session for write operations with exclusive lock"""
        with _db_write_lock:
            # Use regular session but with global write lock
            with self.get_session() as conn:
                yield conn
    
    def execute_write_with_retry(self, operation_name: str, operation_func):
        """Execute write operation with retry logic for database locks"""
        max_retries = 5
        base_delay = 0.1  # 100ms
        
        for attempt in range(max_retries):
            try:
                with _db_write_lock:
                    return operation_func()
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    debug_warning(f"Database locked during {operation_name}, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    raise
            except Exception as e:
                raise
    
    def execute_script(self, script: str):
        """Execute SQL script"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(script)
    
    def initialize_schema(self):
        """Initialize database schema"""
        schema_script = """
        -- Feed names table
        CREATE TABLE IF NOT EXISTS feed_names (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TEXT NOT NULL
        );
        
        -- Insights table with all fields
        CREATE TABLE IF NOT EXISTS insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timeFetched TEXT NOT NULL,
            timePosted TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            symbol TEXT,
            exchange TEXT,
            imageURL TEXT,
            AIImageSummary TEXT,
            AISummary TEXT,
            AIAction TEXT,
            AIConfidence REAL,
            AIEventTime TEXT,
            AILevels TEXT,
            TaskStatus TEXT DEFAULT 'empty',
            TaskName TEXT DEFAULT 'ai_analysis',
            FOREIGN KEY (type) REFERENCES feed_names (name)
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_insights_type ON insights(type);
        CREATE INDEX IF NOT EXISTS idx_insights_symbol ON insights(symbol);
        CREATE INDEX IF NOT EXISTS idx_insights_status ON insights(TaskStatus);
        CREATE INDEX IF NOT EXISTS idx_insights_timePosted ON insights(timePosted);
        
        -- Insert default feed names
        INSERT OR IGNORE INTO feed_names (name, description, created_at) VALUES
            ('TD NEWS', 'TradingView news feed', datetime('now')),
            ('TD IDEAS RECENT', 'TradingView recent ideas feed', datetime('now')),
            ('TD IDEAS POPULAR', 'TradingView popular ideas feed', datetime('now')),
            ('TD OPINIONS', 'TradingView opinions feed', datetime('now'));
        
        -- Reports table for AI analysis reports
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timeFetched TEXT NOT NULL,
            symbol TEXT NOT NULL,
            AISummary TEXT NOT NULL,
            AIAction TEXT NOT NULL,
            AIConfidence REAL NOT NULL,
            AIEventTime TEXT,
            AILevels TEXT,
            TaskStatus TEXT NOT NULL DEFAULT 'completed',
            TaskName TEXT NOT NULL DEFAULT 'ai_analysis'
        );
        
        -- Create indexes for reports table
        CREATE INDEX IF NOT EXISTS idx_reports_symbol ON reports(symbol);
        CREATE INDEX IF NOT EXISTS idx_reports_timeFetched ON reports(timeFetched);
        CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(TaskStatus);
        """
        
        self.execute_script(schema_script)
        debug_info("Database schema initialized")


# Global instance
_db_manager: Optional[DatabaseManager] = None

# Global write lock for database operations
_db_write_lock = threading.RLock()


def get_db_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.initialize_schema()
    return _db_manager


# Convenience functions
@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Convenience function for getting database connection"""
    with get_db_manager().get_connection() as conn:
        yield conn


@contextmanager
def get_db_session() -> Generator[sqlite3.Connection, None, None]:
    """Convenience function for getting database session with row factory"""
    with get_db_manager().get_session() as conn:
        yield conn


@contextmanager
def get_db_write_connection() -> Generator[sqlite3.Connection, None, None]:
    """Convenience function for getting database connection for write operations"""
    with get_db_manager().get_write_connection() as conn:
        yield conn


@contextmanager
def get_db_write_session() -> Generator[sqlite3.Connection, None, None]:
    """Convenience function for getting database session for write operations"""
    with get_db_manager().get_write_session() as conn:
        yield conn 
