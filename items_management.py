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
from debugger import debug_error, debug_info, debug_warning
import hashlib

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
     Includes duplicate checking to prevent redundant entries.
     
     Parameters:
     - type: Feed type (must match feed_names table)
     - title: Insight title
     - content: Main content
     - timePosted: When content was originally posted (optional)
     - symbol: Stock symbol/ticker (optional)
     - exchange: Stock exchange (optional)
     - imageURL: URL to related image (optional)

     - AIImageSummary: AI-generated image summary (optional)
     - AISummary: Overall AI summary (optional)
     - AIAction: Recommended action (BUY/SELL/HOLD) (optional)
     - AIConfidence: Confidence level 0-1 (optional)
     - AIEventTime: Event timestamp (optional)
     - AILevels: Support/Resistance levels (optional)
     
     Returns:
     - int: ID of the created insight (or existing duplicate)
     
     Notes:
     - timeFetched is automatically set to current time
     - timePosted defaults to current time if not provided
     - Checks for duplicates within 48 hour window
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Set timeFetched to current time
    timeFetched = datetime.now().isoformat()
    
    # Use provided timePosted or default to current time
    if timePosted is None:
        timePosted = timeFetched
    
    # Validate type against feed_names
    valid_type = cursor.execute('SELECT name FROM feed_names WHERE name = ?', (type,)).fetchone()
    if not valid_type:
        conn.close()
        raise ValueError(f"Invalid type '{type}'. Must be one of the predefined feed names.")
    
    # Check for duplicates within 48 hour window
    hours_window = 48
    content_hash = hashlib.md5(content.encode()).hexdigest()
    
    # Build query to check for duplicates
    query = '''
        SELECT id, title, content, timePosted
        FROM insights
        WHERE type = ?
        AND (
            title = ? OR LOWER(title) = LOWER(?)
        )
    '''
    
    params = [type, title, title]
    
    # Add symbol check if provided
    if symbol:
        query += ' AND symbol = ?'
        params.append(symbol)
    
    # Add time window check
    query += '''
        AND datetime(timePosted) > datetime(?, '-' || ? || ' hours')
    '''
    params.extend([timePosted, hours_window])
    
    cursor.execute(query, params)
    potential_duplicates = cursor.fetchall()
    
    # Check each potential duplicate
    for row in potential_duplicates:
        # Check if content is similar
        existing_content_hash = hashlib.md5(row['content'].encode()).hexdigest()
        
        # If exact content match, it's a duplicate
        if existing_content_hash == content_hash:
            debug_warning(f"Found exact duplicate: ID {row['id']} - {row['title']}")
            conn.close()
            return row['id']
        
        # If title is exact match and content is > 80% similar in length
        if row['title'] == title:
            content_len_ratio = len(content) / len(row['content'])
            if 0.8 <= content_len_ratio <= 1.2:
                debug_warning(f"Found likely duplicate (similar title/content): ID {row['id']}")
                conn.close()
                return row['id']
    
    # No duplicate found, insert the insight
    cursor.execute('''
        INSERT INTO insights (
            timeFetched, timePosted, type, title, content, symbol, exchange, imageURL,
            AIImageSummary, AISummary, AIAction,
            AIConfidence, AIEventTime, AILevels
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        timeFetched, timePosted, type, title, content, symbol, exchange, imageURL,
        AIImageSummary, AISummary, AIAction,
        AIConfidence, AIEventTime, AILevels
    ))
    
    insight_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    debug_info(f"Added new insight with ID: {insight_id}")
    return insight_id

def get_all_insights(type_filter: str = None, symbol_filter: str = None) -> List[Dict[str, Any]]:
    """
     ┌─────────────────────────────────────┐
     │        GET_ALL_INSIGHTS             │
     └─────────────────────────────────────┘
     Retrieve all insights from the database with optional filtering
     
     Returns all insights with their feed descriptions, ordered by most recently posted first.
     Supports filtering by type and symbol when filters are provided.
     
     Parameters:
     - type_filter: Optional feed type to filter by (e.g., "TD NEWS"). If None or empty, returns all insights.
     - symbol_filter: Optional symbol to filter by (e.g., "BTCUSD"). If None or empty, no symbol filtering.
     
     Returns:
     - List of insight dictionaries with AIAnalysisStatus included
    """
    conn = get_db_connection()
    
    # Build WHERE clause based on filters
    where_conditions = []
    params = []
    
    if type_filter and type_filter.strip():
        where_conditions.append("i.type = ?")
        params.append(type_filter)
    
    if symbol_filter and symbol_filter.strip():
        where_conditions.append("(i.symbol = ? OR i.symbol IS NULL)")
        params.append(symbol_filter)
    
    # Build complete query
    base_query = '''
        SELECT i.*, f.description as feed_description 
        FROM insights i 
        LEFT JOIN feed_names f ON i.type = f.name
    '''
    
    if where_conditions:
        base_query += " WHERE " + " AND ".join(where_conditions)
    
    base_query += " ORDER BY i.timePosted DESC"
    
    insights = conn.execute(base_query, params).fetchall()
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

def reset_insight_ai_fields(insight_id: int) -> bool:
    """
     ┌─────────────────────────────────────┐
     │     RESET_INSIGHT_AI_FIELDS         │
     └─────────────────────────────────────┘
     Reset all AI-related fields of an insight to null/empty
     
     Resets AISummary, AIAction, AIConfidence, AIEventTime, and AILevels
     to NULL or empty string values for the specified insight.
     
     Parameters:
     - insight_id: The ID of the insight to reset AI fields for
     
     Returns:
     - bool: True if reset successfully, False if not found
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE insights 
        SET AISummary = NULL,
            AIAction = NULL,
            AIConfidence = NULL,
            AIEventTime = NULL,
            AILevels = NULL
        WHERE id = ?
    ''', (insight_id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

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

def update_ai_analysis_status(insight_id: int, status: str) -> bool:
    """
     ┌─────────────────────────────────────┐
     │      UPDATE_AI_ANALYSIS_STATUS      │
     └─────────────────────────────────────┘
     Update the AI analysis status for an insight
     
     Parameters:
     - insight_id: The ID of the insight to update
     - status: The new status ('pending', 'processing', 'completed', 'failed')
     
     Returns:
     - bool: True if updated successfully, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'UPDATE insights SET AIAnalysisStatus = ? WHERE id = ?',
        (status, insight_id)
    )
    
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

def delete_select_insights(type: str) -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │    DELETE_SELECT_INSIGHTS           │
     └─────────────────────────────────────┘
     Delete all insights of a specific type
     
     Finds all insights with the specified type and deletes each one
     using the delete_insight function.
     
     Parameters:
     - type: Feed type to filter and delete (e.g., "TD NEWS")
     
     Returns:
     - Dictionary with deletion results and statistics
     
     Notes:
     - Calls delete_insight for each matching insight
     - Returns detailed statistics of the operation
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Find all insights with the specified type
        insights = cursor.execute(
            'SELECT id, title FROM insights WHERE type = ? ORDER BY id',
            (type,)
        ).fetchall()
        
        if not insights:
            conn.close()
            return {
                "success": True,
                "message": f"No insights found with type '{type}'",
                "total_found": 0,
                "deleted_count": 0,
                "failed_count": 0,
                "deleted_ids": [],
                "failed_ids": []
            }
        
        total_found = len(insights)
        deleted_ids = []
        failed_ids = []
        
        # Delete each insight using the existing delete_insight function
        for insight in insights:
            insight_id = insight[0]
            try:
                # Use the existing delete_insight function
                if delete_insight(insight_id):
                    deleted_ids.append(insight_id)
                else:
                    failed_ids.append(insight_id)
            except Exception as e:
                debug_error(f"Error deleting insight {insight_id}: {e}")
                failed_ids.append(insight_id)
        
        conn.close()
        
        deleted_count = len(deleted_ids)
        failed_count = len(failed_ids)
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count}/{total_found} insights of type '{type}'",
            "total_found": total_found,
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "deleted_ids": deleted_ids,
            "failed_ids": failed_ids
        }
        
    except Exception as e:
        conn.close()
        return {
            "success": False,
            "message": f"Error deleting insights: {str(e)}",
            "total_found": 0,
            "deleted_count": 0,
            "failed_count": 0,
            "deleted_ids": [],
            "failed_ids": []
        }
