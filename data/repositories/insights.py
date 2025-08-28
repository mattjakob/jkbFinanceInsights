"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │       INSIGHTS REPOSITORY           │
 *  └─────────────────────────────────────┘
 *  Data access layer for insights
 * 
 *  Implements the repository pattern for insights,
 *  providing clean data access without exposing SQL.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - Repository instance for insights operations
 * 
 *  Notes:
 *  - All SQL is contained within this module
 *  - Returns domain models, not raw database rows
 */
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import hashlib

from core import InsightModel, FeedType, AIAnalysisStatus, get_db_session
from debugger import debug_info, debug_warning, debug_error


class InsightsRepository:
    """
     ┌─────────────────────────────────────┐
     │      INSIGHTSREPOSITORY             │
     └─────────────────────────────────────┘
     Repository for insights data access
     
     Provides CRUD operations and queries for insights,
     encapsulating all database interactions.
    """
    
    def create(self, insight: InsightModel) -> Tuple[int, bool]:
        """
         ┌─────────────────────────────────────┐
         │            CREATE                   │
         └─────────────────────────────────────┘
         Create a new insight
         
         Checks for duplicates before inserting.
         
         Parameters:
         - insight: InsightModel to create
         
         Returns:
         - Tuple of (insight_id, is_new)
         
         Notes:
         - Returns existing ID if duplicate found
         - Duplicate check uses 48-hour window
        """
        # Check for duplicates first
        duplicate_id = self._check_duplicate(insight)
        if duplicate_id:
            debug_warning(f"Found duplicate insight: ID {duplicate_id}")
            return (duplicate_id, False)
        
        # Insert new insight
        with get_db_session() as conn:
            cursor = conn.cursor()
            
            data = insight.to_dict()
            cursor.execute("""
                INSERT INTO insights (
                    timeFetched, timePosted, type, title, content,
                    symbol, exchange, imageURL,
                    AIImageSummary, AISummary, AIAction,
                    AIConfidence, AIEventTime, AILevels, AIAnalysisStatus
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['timeFetched'], data['timePosted'], data['type'],
                data['title'], data['content'], data['symbol'],
                data['exchange'], data['imageURL'],
                data['AIImageSummary'], data['AISummary'], data['AIAction'],
                data['AIConfidence'], data['AIEventTime'], data['AILevels'],
                data['AIAnalysisStatus']
            ))
            
            insight_id = cursor.lastrowid
            debug_info(f"Created new insight with ID: {insight_id}")
            return (insight_id, True)
    
    def get_by_id(self, insight_id: int) -> Optional[InsightModel]:
        """
         ┌─────────────────────────────────────┐
         │           GET_BY_ID                 │
         └─────────────────────────────────────┘
         Get insight by ID
         
         Parameters:
         - insight_id: ID of insight to retrieve
         
         Returns:
         - InsightModel or None if not found
        """
        with get_db_session() as conn:
            row = conn.execute(
                "SELECT * FROM insights WHERE id = ?",
                (insight_id,)
            ).fetchone()
            
            if row:
                return InsightModel.from_dict(dict(row))
            return None
    
    def update(self, insight_id: int, updates: Dict[str, Any]) -> bool:
        """
         ┌─────────────────────────────────────┐
         │            UPDATE                   │
         └─────────────────────────────────────┘
         Update an insight
         
         Parameters:
         - insight_id: ID of insight to update
         - updates: Dictionary of fields to update
         
         Returns:
         - True if updated, False if not found
        """
        # Remove fields that shouldn't be updated
        updates.pop('id', None)
        updates.pop('timeFetched', None)
        
        if not updates:
            return False
        
        # Build SET clause
        set_clauses = []
        values = []
        for key, value in updates.items():
            # Convert Python field names to database column names
            db_column = self._to_db_column(key)
            set_clauses.append(f"{db_column} = ?")
            values.append(value)
        
        values.append(insight_id)
        
        with get_db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE insights SET {', '.join(set_clauses)} WHERE id = ?",
                values
            )
            return cursor.rowcount > 0
    
    def delete(self, insight_id: int) -> bool:
        """
         ┌─────────────────────────────────────┐
         │            DELETE                   │
         └─────────────────────────────────────┘
         Delete an insight
         
         Parameters:
         - insight_id: ID of insight to delete
         
         Returns:
         - True if deleted, False if not found
        """
        with get_db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM insights WHERE id = ?", (insight_id,))
            return cursor.rowcount > 0
    
    def find_all(self, 
                 type_filter: Optional[str] = None,
                 symbol_filter: Optional[str] = None,
                 limit: Optional[int] = None,
                 offset: int = 0) -> List[InsightModel]:
        """
         ┌─────────────────────────────────────┐
         │          FIND_ALL                   │
         └─────────────────────────────────────┘
         Find insights with optional filters
         
         Parameters:
         - type_filter: Filter by feed type
         - symbol_filter: Filter by symbol
         - limit: Maximum results
         - offset: Skip first N results
         
         Returns:
         - List of InsightModel instances
        """
        with get_db_session() as conn:
            query = "SELECT * FROM insights WHERE 1=1"
            params = []
            
            if type_filter:
                query += " AND type = ?"
                params.append(type_filter)
            
            if symbol_filter:
                query += " AND (symbol = ? OR symbol IS NULL)"
                params.append(symbol_filter)
            
            query += " ORDER BY timePosted DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            if offset:
                query += " OFFSET ?"
                params.append(offset)
            
            rows = conn.execute(query, params).fetchall()
            return [InsightModel.from_dict(dict(row)) for row in rows]
    
    def find_for_ai_analysis(self) -> List[InsightModel]:
        """
         ┌─────────────────────────────────────┐
         │     FIND_FOR_AI_ANALYSIS            │
         └─────────────────────────────────────┘
         Find insights needing AI analysis
         
         Returns insights where analysis is pending or
         where AISummary is empty.
         
         Returns:
         - List of insights needing analysis
        """
        with get_db_session() as conn:
            rows = conn.execute("""
                SELECT * FROM insights 
                WHERE (
                    AIAnalysisStatus = 'pending' 
                    OR (
                        (AISummary IS NULL OR AISummary = '')
                        AND (AIAnalysisStatus IS NULL OR AIAnalysisStatus != 'failed')
                    )
                )
                ORDER BY timePosted DESC
            """).fetchall()
            
            return [InsightModel.from_dict(dict(row)) for row in rows]
    
    def update_ai_status(self, insight_id: int, status: AIAnalysisStatus) -> bool:
        """
         ┌─────────────────────────────────────┐
         │       UPDATE_AI_STATUS              │
         └─────────────────────────────────────┘
         Update AI analysis status
         
         Parameters:
         - insight_id: Insight to update
         - status: New analysis status
         
         Returns:
         - True if updated successfully
        """
        return self.update(insight_id, {'AIAnalysisStatus': status.value})
    
    def delete_by_type(self, feed_type: FeedType) -> Tuple[int, List[int]]:
        """
         ┌─────────────────────────────────────┐
         │        DELETE_BY_TYPE               │
         └─────────────────────────────────────┘
         Delete all insights of a specific type
         
         Parameters:
         - feed_type: Type of insights to delete
         
         Returns:
         - Tuple of (count_deleted, list_of_ids)
        """
        with get_db_session() as conn:
            # First get the IDs
            cursor = conn.cursor()
            ids = cursor.execute(
                "SELECT id FROM insights WHERE type = ?",
                (feed_type.value,)
            ).fetchall()
            
            id_list = [row[0] for row in ids]
            
            if id_list:
                # Delete them
                cursor.execute(
                    "DELETE FROM insights WHERE type = ?",
                    (feed_type.value,)
                )
                
            return (len(id_list), id_list)
    
    def _check_duplicate(self, insight: InsightModel) -> Optional[int]:
        """
         ┌─────────────────────────────────────┐
         │       _CHECK_DUPLICATE              │
         └─────────────────────────────────────┘
         Check for duplicate insights
         
         Uses title and content hash within 48-hour window.
         
         Parameters:
         - insight: Insight to check
         
         Returns:
         - ID of duplicate if found, None otherwise
        """
        hours_window = 48
        content_hash = hashlib.md5(insight.content.encode()).hexdigest()
        
        with get_db_session() as conn:
            # Build query
            query = """
                SELECT id, title, content
                FROM insights
                WHERE type = ?
                AND (title = ? OR LOWER(title) = LOWER(?))
            """
            params = [insight.type.value, insight.title, insight.title]
            
            if insight.symbol:
                query += " AND symbol = ?"
                params.append(insight.symbol)
            
            query += """
                AND datetime(timePosted) > datetime(?, '-' || ? || ' hours')
            """
            params.extend([insight.time_posted.isoformat(), hours_window])
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            for row in cursor.fetchall():
                # Check content hash
                existing_hash = hashlib.md5(row['content'].encode()).hexdigest()
                if existing_hash == content_hash:
                    return row['id']
                
                # Check similar content length
                if row['title'] == insight.title:
                    content_ratio = len(insight.content) / len(row['content'])
                    if 0.8 <= content_ratio <= 1.2:
                        return row['id']
            
            return None
    
    def _to_db_column(self, field_name: str) -> str:
        """Convert Python field name to database column name"""
        mapping = {
            'time_fetched': 'timeFetched',
            'time_posted': 'timePosted',
            'image_url': 'imageURL',
            'ai_image_summary': 'AIImageSummary',
            'ai_summary': 'AISummary',
            'ai_action': 'AIAction',
            'ai_confidence': 'AIConfidence',
            'ai_event_time': 'AIEventTime',
            'ai_levels': 'AILevels',
            'ai_analysis_status': 'AIAnalysisStatus'
        }
        return mapping.get(field_name, field_name)



