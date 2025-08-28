"""
 ┌─────────────────────────────────────┐
 │         DATABASE SCHEMA             │
 └─────────────────────────────────────┘
 Database schema management for JKB Finance Insights
 
 Provides centralized database initialization, schema creation,
 and migration functions for the application.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Tuple, Dict, Any
from config import DATABASE_URL as DATABASE
from debugger import debug_info, debug_warning, debug_error, debug_success

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_feed_names_table(cursor: sqlite3.Cursor) -> None:
    """Create the feed_names table"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feed_names (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TEXT NOT NULL
        )
    ''')

def create_insights_table(cursor: sqlite3.Cursor) -> None:
    """Create the insights table with symbol and exchange fields"""
    cursor.execute('''
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
            FOREIGN KEY (type) REFERENCES feed_names (name)
        )
    ''')

def insert_default_feeds(cursor: sqlite3.Cursor) -> None:
    """Insert default feed names if they don't exist"""
    default_feeds = [
        ('TD IDEAS RECENT', 'TD Ameritrade recent ideas feed'),
        ('TD IDEAS POPULAR', 'TD Ameritrade popular ideas feed'),
        ('TD OPINIONS', 'TD Ameritrade opinions feed'),
        ('TD NEWS', 'TD Ameritrade news feed')
    ]
    
    for feed_name, description in default_feeds:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO feed_names (name, description, created_at) 
                VALUES (?, ?, ?)
            ''', (feed_name, description, datetime.now().isoformat()))
        except sqlite3.IntegrityError:
            # Feed name already exists, skip
            pass

def migrate_existing_insights(cursor: sqlite3.Cursor) -> None:
    """Migrate existing insights table to add symbol and exchange columns"""
    try:
        # Check if symbol column exists
        cursor.execute("PRAGMA table_info(insights)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add symbol column if it doesn't exist
        if 'symbol' not in columns:
            cursor.execute("ALTER TABLE insights ADD COLUMN symbol TEXT")
            debug_success("Added symbol column to insights table")
        
        # Add exchange column if it doesn't exist
        if 'exchange' not in columns:
            cursor.execute("ALTER TABLE insights ADD COLUMN exchange TEXT")
            debug_success("Added exchange column to insights table")
            
    except sqlite3.OperationalError as e:
        debug_error(f"Migration error: {e}")

def init_database() -> None:
    """
     ┌─────────────────────────────────────┐
     │         INIT_DATABASE               │
     └─────────────────────────────────────┘
     Initialize the SQLite database with all required tables
     
     Creates the database tables if they don't exist and handles
     any necessary migrations for existing databases.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create tables
        create_feed_names_table(cursor)
        create_insights_table(cursor)
        
        # Insert default data
        insert_default_feeds(cursor)
        
        # Migrate existing data if needed
        migrate_existing_insights(cursor)
        
        conn.commit()
        debug_success("Database initialized successfully")
        
    except Exception as e:
        debug_error(f"Database initialization error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def check_database_structure() -> None:
    """Check the current database structure for debugging"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check insights table structure
        cursor.execute("PRAGMA table_info(insights)")
        insights_columns = cursor.fetchall()
        debug_info("Insights table structure:")
        for col in insights_columns:
            debug_info(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULLABLE'}")
        
        # Check feed_names table structure
        cursor.execute("PRAGMA table_info(feed_names)")
        feed_columns = cursor.fetchall()
        debug_info("Feed_names table structure:")
        for col in feed_columns:
            debug_info(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULLABLE'}")
        
        # Check sample data
        cursor.execute("SELECT COUNT(*) FROM insights")
        insights_count = cursor.fetchone()[0]
        debug_info(f"Total insights in database: {insights_count}")
        
        cursor.execute("SELECT COUNT(*) FROM feed_names")
        feeds_count = cursor.fetchone()[0]
        debug_info(f"Total feed names in database: {feeds_count}")
        
        if insights_count > 0:
            # Check if symbol and exchange columns exist
            cursor.execute("PRAGMA table_info(insights)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'symbol' in columns and 'exchange' in columns:
                cursor.execute("SELECT id, timeFetched, timePosted, type, title, symbol, exchange FROM insights ORDER BY id DESC LIMIT 1")
                latest = cursor.fetchone()
                debug_info(f"Latest insight:")
                debug_info(f"  ID: {latest[0]}")
                debug_info(f"  timeFetched: {latest[1]}")
                debug_info(f"  timePosted: {latest[2]}")
                debug_info(f"  type: {latest[3]}")
                debug_info(f"  title: {latest[4]}")
                debug_info(f"  symbol: {latest[5]}")
                debug_info(f"  exchange: {latest[6]}")
            else:
                cursor.execute("SELECT id, timeFetched, timePosted, type, title FROM insights ORDER BY id DESC LIMIT 1")
                latest = cursor.fetchone()
                debug_info(f"Latest insight:")
                debug_info(f"  ID: {latest[0]}")
                debug_info(f"  timeFetched: {latest[1]}")
                debug_info(f"  timePosted: {latest[2]}")
                debug_info(f"  type: {latest[3]}")
                debug_info(f"  title: {latest[4]}")
                debug_info(f"  symbol/exchange: Columns not yet added")
    
    finally:
        conn.close()

def reset_database() -> None:
    """Reset the database by dropping all tables and recreating them"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Drop existing tables
        cursor.execute("DROP TABLE IF EXISTS insights")
        cursor.execute("DROP TABLE IF EXISTS feed_names")
        
        conn.commit()
        debug_success("Database tables dropped")
        
        # Reinitialize
        init_database()
        
    except Exception as e:
        debug_error(f"Database reset error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_duplicate_insights() -> List[Dict[str, Any]]:
    """
     ┌─────────────────────────────────────┐
     │      GET_DUPLICATE_INSIGHTS         │
     └─────────────────────────────────────┘
     Find potential duplicate insights in the database
     
     Identifies insights with similar titles or content.
     
     Returns:
     - List of potential duplicate groups
     
     Notes:
     - Groups insights by similar titles
     - Useful for cleanup operations
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Find insights with similar titles
    cursor.execute('''
        SELECT 
            i1.id as id1,
            i1.title as title1,
            i1.type as type1,
            i1.timePosted as time1,
            i2.id as id2,
            i2.title as title2,
            i2.type as type2,
            i2.timePosted as time2
        FROM insights i1
        JOIN insights i2 ON i1.id < i2.id
        WHERE i1.type = i2.type
        AND i1.symbol = i2.symbol
        AND (
            i1.title = i2.title
            OR LOWER(i1.title) = LOWER(i2.title)
        )
        ORDER BY i1.title, i1.timePosted
    ''')
    
    duplicates = []
    for row in cursor.fetchall():
        duplicate = {
            'id1': row['id1'],
            'title1': row['title1'],
            'type1': row['type1'],
            'time1': row['time1'],
            'id2': row['id2'],
            'title2': row['title2'],
            'type2': row['type2'],
            'time2': row['time2']
        }
        duplicates.append(duplicate)
    
    conn.close()
    return duplicates

def cleanup_duplicates(dry_run: bool = True) -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │       CLEANUP_DUPLICATES            │
     └─────────────────────────────────────┘
     Remove duplicate insights from the database
     
     Finds and optionally removes duplicate insights, keeping
     the most recent version.
     
     Parameters:
     - dry_run: If True, only report duplicates without deleting
     
     Returns:
     - Dictionary with cleanup statistics
     
     Notes:
     - Keeps the most recent insight when duplicates found
     - Logs all deletions for audit trail
    """
    import items_management
    
    duplicates = get_duplicate_insights()
    
    if dry_run:
        return {
            'dry_run': True,
            'duplicates_found': len(duplicates),
            'duplicates': duplicates
        }
    
    deleted_count = 0
    kept_insights = []
    deleted_insights = []
    
    # Process each duplicate pair
    processed_ids = set()
    
    for dup in duplicates:
        # Skip if already processed
        if dup['id1'] in processed_ids or dup['id2'] in processed_ids:
            continue
        
        # Keep the more recent one
        if dup['time1'] > dup['time2']:
            keep_id, delete_id = dup['id1'], dup['id2']
        else:
            keep_id, delete_id = dup['id2'], dup['id1']
        
        # Delete the older duplicate
        if items_management.delete_insight(delete_id):
            deleted_count += 1
            deleted_insights.append(delete_id)
            kept_insights.append(keep_id)
            processed_ids.add(delete_id)
            debug_info(f"Deleted duplicate insight {delete_id}, kept {keep_id}")
    
    return {
        'dry_run': False,
        'duplicates_found': len(duplicates),
        'deleted_count': deleted_count,
        'kept_insights': kept_insights,
        'deleted_insights': deleted_insights
    }

if __name__ == "__main__":
    debug_info("Database Schema Management")
    debug_info("=" * 50)
    
    # Check current structure
    debug_info("\nCurrent database structure:")
    check_database_structure()
    
    # Option to reset database
    debug_info("\nOptions:")
    debug_info("1. Check structure (current)")
    debug_info("2. Initialize database")
    debug_info("3. Reset database (WARNING: This will delete all data)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "2":
        init_database()
    elif choice == "3":
        confirm = input("Are you sure you want to reset the database? (yes/no): ").strip().lower()
        if confirm == "yes":
            reset_database()
        else:
            debug_info("Database reset cancelled")
    else:
        debug_info("No changes made")
