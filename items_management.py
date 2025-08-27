"""
 ┌─────────────────────────────────────┐
 │         ITEMS MANAGEMENT            │
 └─────────────────────────────────────┘
 CRUD operations for finance insights
 
 Provides functions to create, read, update, and delete finance insights
 in the database. All database operations are handled through this module.
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any

DATABASE = "finance_insights.db"

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def add_insight(
    type: str,
    title: str,
    content: str,
    timePosted: Optional[str] = None,
    symbol: Optional[str] = None,
    exchange: Optional[str] = None,
    imageURL: Optional[str] = None,
    AITextSummary: Optional[str] = None,
    AIImageSummary: Optional[str] = None,
    AISummary: Optional[str] = None,
    AIAction: Optional[str] = None,
    AIConfidence: Optional[float] = None,
    AIEventTime: Optional[str] = None,
    AILevels: Optional[str] = None
) -> int:
    """
     ┌─────────────────────────────────────┐
     │          ADD_INSIGHT                │
     └─────────────────────────────────────┘
     Add a new insight to the database
     
     Creates a new insight record with provided data and returns the ID.
     
     Parameters:
     - type: Feed type (must match feed_names table)
     - title: Insight title
     - content: Main content
     - timePosted: When content was originally posted (optional)
     - symbol: Stock symbol/ticker (optional)
     - exchange: Stock exchange (optional)
     - imageURL: URL to related image (optional)
     - AITextSummary: AI-generated text summary (optional)
     - AIImageSummary: AI-generated image summary (optional)
     - AISummary: Overall AI summary (optional)
     - AIAction: Recommended action (BUY/SELL/HOLD) (optional)
     - AIConfidence: Confidence level 0-1 (optional)
     - AIEventTime: Event timestamp (optional)
     - AILevels: Support/Resistance levels (optional)
     
     Returns:
     - int: ID of the created insight
     
     Notes:
     - timeFetched is automatically set to current time
     - timePosted defaults to current time if not provided
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Set timeFetched to current time
    time_fetched = datetime.now().isoformat()
    
    # Use provided timePosted or default to current time
    if timePosted is None:
        timePosted = time_fetched
    
    # Validate type against feed_names
    valid_type = cursor.execute('SELECT name FROM feed_names WHERE name = ?', (type,)).fetchone()
    if not valid_type:
        conn.close()
        raise ValueError(f"Invalid type '{type}'. Must be one of the predefined feed names.")
    
    # Insert the insight
    cursor.execute('''
        INSERT INTO insights (
            timeFetched, timePosted, type, title, content, symbol, exchange, imageURL,
            AITextSummary, AIImageSummary, AISummary, AIAction,
            AIConfidence, AIEventTime, AILevels
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        time_fetched, timePosted, type, title, content, symbol, exchange, imageURL,
        AITextSummary, AIImageSummary, AISummary, AIAction,
        AIConfidence, AIEventTime, AILevels
    ))
    
    insight_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return insight_id

def get_all_insights() -> List[Dict[str, Any]]:
    """
     ┌─────────────────────────────────────┐
     │        GET_ALL_INSIGHTS             │
     └─────────────────────────────────────┘
     Retrieve all insights from the database
     
     Returns all insights with their feed descriptions, ordered by most recently posted first.
     
     Returns:
     - List of insight dictionaries
    """
    conn = get_db_connection()
    insights = conn.execute('''
        SELECT i.*, f.description as feed_description 
        FROM insights i 
        LEFT JOIN feed_names f ON i.type = f.name 
        ORDER BY i.timePosted DESC
    ''').fetchall()
    conn.close()
    
    return [dict(insight) for insight in insights]

def get_insight_by_id(insight_id: int) -> Optional[Dict[str, Any]]:
    """
     ┌─────────────────────────────────────┐
     │        GET_INSIGHT_BY_ID            │
     └─────────────────────────────────────┘
     Retrieve a specific insight by ID
     
     Parameters:
     - insight_id: The ID of the insight to retrieve
     
     Returns:
     - Dictionary with insight data or None if not found
    """
    conn = get_db_connection()
    insight = conn.execute(
        'SELECT * FROM insights WHERE id = ?', (insight_id,)
    ).fetchone()
    conn.close()
    
    return dict(insight) if insight else None

def update_insight(
    insight_id: int,
    **kwargs
) -> bool:
    """
     ┌─────────────────────────────────────┐
     │        UPDATE_INSIGHT               │
     └─────────────────────────────────────┘
     Update an existing insight
     
     Updates specified fields of an insight. Only provided fields are updated.
     
     Parameters:
     - insight_id: The ID of the insight to update
     - **kwargs: Field-value pairs to update
     
     Returns:
     - bool: True if updated successfully, False if not found
     
     Notes:
     - timeFetched cannot be updated
     - type must be valid if provided
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Remove fields that shouldn't be updated
    kwargs.pop('id', None)
    kwargs.pop('timeFetched', None)
    
    # Validate type if provided
    if 'type' in kwargs:
        valid_type = cursor.execute('SELECT name FROM feed_names WHERE name = ?', (kwargs['type'],)).fetchone()
        if not valid_type:
            conn.close()
            raise ValueError(f"Invalid type '{kwargs['type']}'. Must be one of the predefined feed names.")
    
    # Build update query
    if not kwargs:
        conn.close()
        return False
    
    set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
    values = list(kwargs.values())
    values.append(insight_id)
    
    cursor.execute(f'''
        UPDATE insights 
        SET {set_clause}
        WHERE id = ?
    ''', values)
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def update_insight_ai_fields(
    insight_id: int,
    AISummary: Optional[str] = None,
    AIAction: Optional[str] = None,
    AIConfidence: Optional[float] = None,
    AIEventTime: Optional[str] = None,
    AILevels: Optional[str] = None
) -> bool:
    """
     ┌─────────────────────────────────────┐
     │     UPDATE_INSIGHT_AI_FIELDS        │
     └─────────────────────────────────────┘
     Update only AI-related fields of an insight
     
     Convenience function to update AI analysis fields.
     
     Parameters:
     - insight_id: The ID of the insight to update
     - AISummary: AI-generated summary
     - AIAction: Recommended action
     - AIConfidence: Confidence level
     - AIEventTime: Predicted event timing
     - AILevels: Support/Resistance levels
     
     Returns:
     - bool: True if updated successfully
    """
    update_data = {}
    if AISummary is not None:
        update_data['AISummary'] = AISummary
    if AIAction is not None:
        update_data['AIAction'] = AIAction
    if AIConfidence is not None:
        update_data['AIConfidence'] = AIConfidence
    if AIEventTime is not None:
        update_data['AIEventTime'] = AIEventTime
    if AILevels is not None:
        update_data['AILevels'] = AILevels
    
    return update_insight(insight_id, **update_data)

def delete_insight(insight_id: int) -> bool:
    """
     ┌─────────────────────────────────────┐
     │        DELETE_INSIGHT               │
     └─────────────────────────────────────┘
     Delete an insight from the database
     
     Parameters:
     - insight_id: The ID of the insight to delete
     
     Returns:
     - bool: True if deleted successfully, False if not found
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM insights WHERE id = ?', (insight_id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def get_insights_for_ai() -> List[Dict[str, Any]]:
    """
     ┌─────────────────────────────────────┐
     │   GET_INSIGHTS_WITHOUT_AI_DATA      │
     └─────────────────────────────────────┘
     Get insights that have missing AI analysis fields
     
     Returns insights where AISummary is NULL or empty string, ordered by most recently posted first.
     
     Returns:
     - List of insights needing AI analysis
    """
    conn = get_db_connection()
    insights = conn.execute('''
        SELECT * FROM insights 
        WHERE AISummary IS NULL OR AISummary = ''
        ORDER BY timePosted DESC
    ''').fetchall()
    conn.close()
    
    return [dict(insight) for insight in insights]

def get_feed_names() -> List[Dict[str, str]]:
    """
     ┌─────────────────────────────────────┐
     │         GET_FEED_NAMES              │
     └─────────────────────────────────────┘
     Get all available feed names
     
     Returns:
     - List of feed name dictionaries with name and description
    """
    conn = get_db_connection()
    feeds = conn.execute('SELECT name, description FROM feed_names ORDER BY name').fetchall()
    conn.close()
    
    return [dict(feed) for feed in feeds]
