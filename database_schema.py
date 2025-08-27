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
from typing import List, Tuple
from config import DATABASE_URL as DATABASE

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
            AITextSummary TEXT,
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
            print("Added symbol column to insights table")
        
        # Add exchange column if it doesn't exist
        if 'exchange' not in columns:
            cursor.execute("ALTER TABLE insights ADD COLUMN exchange TEXT")
            print("Added exchange column to insights table")
            
    except sqlite3.OperationalError as e:
        print(f"Migration error: {e}")

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
        print("Database initialized successfully")
        
    except Exception as e:
        print(f"Database initialization error: {e}")
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
        print("Insights table structure:")
        for col in insights_columns:
            print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULLABLE'}")
        
        # Check feed_names table structure
        cursor.execute("PRAGMA table_info(feed_names)")
        feed_columns = cursor.fetchall()
        print("Feed_names table structure:")
        for col in feed_columns:
            print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULLABLE'}")
        
        # Check sample data
        cursor.execute("SELECT COUNT(*) FROM insights")
        insights_count = cursor.fetchone()[0]
        print(f"Total insights in database: {insights_count}")
        
        cursor.execute("SELECT COUNT(*) FROM feed_names")
        feeds_count = cursor.fetchone()[0]
        print(f"Total feed names in database: {feeds_count}")
        
        if insights_count > 0:
            # Check if symbol and exchange columns exist
            cursor.execute("PRAGMA table_info(insights)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'symbol' in columns and 'exchange' in columns:
                cursor.execute("SELECT id, timeFetched, timePosted, type, title, symbol, exchange FROM insights ORDER BY id DESC LIMIT 1")
                latest = cursor.fetchone()
                print(f"Latest insight:")
                print(f"  ID: {latest[0]}")
                print(f"  timeFetched: {latest[1]}")
                print(f"  timePosted: {latest[2]}")
                print(f"  type: {latest[3]}")
                print(f"  title: {latest[4]}")
                print(f"  symbol: {latest[5]}")
                print(f"  exchange: {latest[6]}")
            else:
                cursor.execute("SELECT id, timeFetched, timePosted, type, title FROM insights ORDER BY id DESC LIMIT 1")
                latest = cursor.fetchone()
                print(f"Latest insight:")
                print(f"  ID: {latest[0]}")
                print(f"  timeFetched: {latest[1]}")
                print(f"  timePosted: {latest[2]}")
                print(f"  type: {latest[3]}")
                print(f"  title: {latest[4]}")
                print(f"  symbol/exchange: Columns not yet added")
    
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
        print("Database tables dropped")
        
        # Reinitialize
        init_database()
        
    except Exception as e:
        print(f"Database reset error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("Database Schema Management")
    print("=" * 50)
    
    # Check current structure
    print("\nCurrent database structure:")
    check_database_structure()
    
    # Option to reset database
    print("\nOptions:")
    print("1. Check structure (current)")
    print("2. Initialize database")
    print("3. Reset database (WARNING: This will delete all data)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "2":
        init_database()
    elif choice == "3":
        confirm = input("Are you sure you want to reset the database? (yes/no): ").strip().lower()
        if confirm == "yes":
            reset_database()
        else:
            print("Database reset cancelled")
    else:
        print("No changes made")
