"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │            DATABASE                 │
 *  └─────────────────────────────────────┘
 *  Database connection and session management
 * 
 *  Provides centralized database connection handling with
 *  context managers for safe resource management.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - Database connection utilities
 * 
 *  Notes:
 *  - Uses context managers for automatic cleanup
 *  - Supports both sync and async operations
 */
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional
import os
from pathlib import Path

from config import DATABASE_URL
from debugger import debug_info, debug_error


class DatabaseConfig:
    """
     ┌─────────────────────────────────────┐
     │        DATABASECONFIG               │
     └─────────────────────────────────────┘
     Database configuration settings
     
     Centralizes database-related configuration.
    """
    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url
        self.timeout = 30.0
        self.check_same_thread = False
        
    @property
    def connection_kwargs(self) -> dict:
        """Get kwargs for sqlite3.connect()"""
        return {
            'timeout': self.timeout,
            'check_same_thread': self.check_same_thread
        }


class DatabaseManager:
    """
     ┌─────────────────────────────────────┐
     │        DATABASEMANAGER              │
     └─────────────────────────────────────┘
     Manages database connections and sessions
     
     Provides context managers for safe database access
     with automatic resource cleanup.
     
     Parameters:
     - config: DatabaseConfig instance
     
     Returns:
     - DatabaseManager instance
     
     Notes:
     - Use get_connection() for raw connections
     - Use get_session() for row factory connections
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure database file exists"""
        db_path = Path(self.config.database_url)
        if not db_path.exists():
            debug_info(f"Creating database at {db_path}")
            db_path.parent.mkdir(parents=True, exist_ok=True)
            # Touch the file to create it
            db_path.touch()
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
         ┌─────────────────────────────────────┐
         │        GET_CONNECTION               │
         └─────────────────────────────────────┘
         Get raw database connection
         
         Context manager that provides a raw SQLite connection
         and ensures proper cleanup.
         
         Returns:
         - sqlite3.Connection within context
         
         Notes:
         - Automatically commits on success
         - Rolls back on exception
        """
        conn = None
        try:
            conn = sqlite3.connect(
                self.config.database_url,
                **self.config.connection_kwargs
            )
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            debug_error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_session(self) -> Generator[sqlite3.Connection, None, None]:
        """
         ┌─────────────────────────────────────┐
         │         GET_SESSION                 │
         └─────────────────────────────────────┘
         Get database connection with row factory
         
         Context manager that provides a connection configured
         with sqlite3.Row factory for dict-like row access.
         
         Returns:
         - sqlite3.Connection with row factory
         
         Notes:
         - Rows can be accessed like dictionaries
         - Automatically handles transactions
        """
        conn = None
        try:
            conn = sqlite3.connect(
                self.config.database_url,
                **self.config.connection_kwargs
            )
            conn.row_factory = sqlite3.Row
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            debug_error(f"Database session error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_script(self, script: str):
        """
         ┌─────────────────────────────────────┐
         │        EXECUTE_SCRIPT               │
         └─────────────────────────────────────┘
         Execute SQL script
         
         Executes a multi-statement SQL script, useful for
         migrations and schema creation.
         
         Parameters:
         - script: SQL script to execute
         
         Notes:
         - Use for CREATE TABLE statements
         - Automatically commits changes
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(script)
    
    def initialize_schema(self):
        """
         ┌─────────────────────────────────────┐
         │       INITIALIZE_SCHEMA             │
         └─────────────────────────────────────┘
         Initialize database schema
         
         Creates all required tables if they don't exist.
         This replaces the functionality in database_schema.py.
        """
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
            AIAnalysisStatus TEXT DEFAULT 'empty',
            FOREIGN KEY (type) REFERENCES feed_names (name)
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_insights_type ON insights(type);
        CREATE INDEX IF NOT EXISTS idx_insights_symbol ON insights(symbol);
        CREATE INDEX IF NOT EXISTS idx_insights_status ON insights(AIAnalysisStatus);
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
            AIAnalysisStatus TEXT NOT NULL DEFAULT 'completed'
        );
        
        -- Create indexes for reports table
        CREATE INDEX IF NOT EXISTS idx_reports_symbol ON reports(symbol);
        CREATE INDEX IF NOT EXISTS idx_reports_timeFetched ON reports(timeFetched);
        CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(AIAnalysisStatus);
        """
        
        self.execute_script(schema_script)
        debug_info("Database schema initialized")


# Global instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """
     ┌─────────────────────────────────────┐
     │         GET_DB_MANAGER              │
     └─────────────────────────────────────┘
     Get global database manager instance
     
     Returns singleton DatabaseManager instance,
     creating it if necessary.
     
     Returns:
     - DatabaseManager instance
    """
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



