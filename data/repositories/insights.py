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

from core import InsightModel, FeedType, TaskStatus, TaskName, TaskInfo, get_db_session
from config import SCRAPER_DUPLICATE_WINDOW_HOURS
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
                    AIConfidence, AIEventTime, AILevels, TaskStatus, TaskName
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['timeFetched'], data['timePosted'], data['type'],
                data['title'], data['content'], data['symbol'],
                data['exchange'], data['imageURL'],
                data['AIImageSummary'], data['AISummary'], data['AIAction'],
                data['AIConfidence'], data['AIEventTime'], data['AILevels'],
                data['TaskStatus'], data['TaskName']
            ))
            
            insight_id = cursor.lastrowid
            debug_info(f"Insight {insight_id} created for {insight.symbol} {insight.type}")
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
                # Extract just the symbol part, ignoring exchange suffix (e.g., "AAPL:NASDAQ" -> "AAPL")
                clean_symbol = symbol_filter.split(':')[0] if ':' in symbol_filter else symbol_filter
                query += " AND (symbol = ? OR symbol IS NULL)"
                params.append(clean_symbol)
            
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
         
         Returns insights where TaskStatus is EMPTY or FAILED,
         meaning no task has operated on them yet or they failed and need retry.
         
         Returns:
         - List of insights needing analysis
        """
        with get_db_session() as conn:
            rows = conn.execute("""
                SELECT * FROM insights 
                WHERE TaskStatus IN ('empty', 'failed')
                ORDER BY timePosted DESC
            """).fetchall()
            
            return [InsightModel.from_dict(dict(row)) for row in rows]
    
    def update_ai_status(self, insight_id: int, status: TaskStatus, name: TaskName = None) -> bool:
        """
         ┌─────────────────────────────────────┐
         │       UPDATE_AI_STATUS              │
         └─────────────────────────────────────┘
         Update AI task status and optionally name
         
         Parameters:
         - insight_id: Insight to update
         - status: New task status
         - name: Optional task name (if changing task type)
         
         Returns:
         - True if updated successfully
        """
        updates = {'TaskStatus': status.value}
        if name:
            updates['TaskName'] = name.value
        return self.update(insight_id, updates)
    
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
         
         Simple title-based duplicate detection only.
         
         Parameters:
         - insight: Insight to check
         
         Returns:
         - ID of duplicate if found, None otherwise
        """
        with get_db_session() as conn:
            # Simple query: check for exact title match with same type and symbol
            query = """
                SELECT id
                FROM insights
                WHERE type = ? 
                AND title = ?
                AND symbol = ?
                LIMIT 1
            """
            params = [insight.type.value, insight.title, insight.symbol]
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            return row['id'] if row else None
    
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
            'ai_analysis_status': 'TaskStatus'
        }
        return mapping.get(field_name, field_name)
    
    def reset_failed_ai_analysis(self) -> int:
        """
         ┌─────────────────────────────────────┐
         │    RESET_FAILED_AI_ANALYSIS        │
         └─────────────────────────────────────┘
         Reset all insights with failed AI analysis back to pending
         
         Returns:
         - Number of insights reset
        """
        with get_db_session() as conn:
            reset_count = conn.execute("""
                UPDATE insights
                SET TaskStatus = ?
                WHERE TaskStatus = ?
            """, (
                TaskStatus.EMPTY.value,
                TaskStatus.FAILED.value
            )).rowcount
            
            if reset_count > 0:
                debug_info(f"Reset {reset_count} insights with failed AI analysis back to EMPTY")
            
            return reset_count
    
    def reset_processing_ai_analysis(self) -> int:
        """
         ┌─────────────────────────────────────┐
         │   RESET_PROCESSING_AI_ANALYSIS     │
         └─────────────────────────────────────┘
         Reset all insights with processing AI analysis back to pending
         
         Returns:
         - Number of insights reset
        """
        with get_db_session() as conn:
            reset_count = conn.execute("""
                UPDATE insights
                SET TaskStatus = ?
                WHERE TaskStatus = ?
            """, (
                TaskStatus.EMPTY.value,
                TaskStatus.PROCESSING.value
            )).rowcount
            
            if reset_count > 0:
                debug_info(f"Reset {reset_count} insights with processing AI analysis back to EMPTY")
            
            return reset_count
    
    def reset_stuck_insights(self) -> int:
        """
         ┌─────────────────────────────────────┐
         │       RESET_STUCK_INSIGHTS          │
         └─────────────────────────────────────┘
         Reset insights stuck in PENDING, PROCESSING, or FAILED
         
         Resets AI analysis status to EMPTY for insights
         that are stuck in PENDING, PROCESSING, or FAILED states.
         Also clears any AI analysis results.
         
         Returns:
         - Number of insights reset
        """
        with get_db_session() as conn:
            cursor = conn.cursor()
            
            # Reset insights stuck in PENDING, PROCESSING, or FAILED to EMPTY
            reset_count = cursor.execute("""
                UPDATE insights 
                SET TaskStatus = ?,
                    AISummary = NULL,
                    AIAction = NULL,
                    AIConfidence = NULL,
                    AIEventTime = NULL,
                    AILevels = NULL,
                    AIImageSummary = NULL
                WHERE TaskStatus IN (?, ?, ?)
            """, (
                TaskStatus.EMPTY.value,
                TaskStatus.PENDING.value,
                TaskStatus.PROCESSING.value,
                TaskStatus.FAILED.value
            )).rowcount
            
            if reset_count > 0:
                debug_info(f"Reset {reset_count} stuck insights to EMPTY status")
            
            return reset_count
    
    def reset_insights_by_symbol_and_type(self, symbol: str, feed_type: Optional[FeedType] = None) -> Tuple[int, int]:
        """
         ┌─────────────────────────────────────┐
         │   RESET_INSIGHTS_BY_SYMBOL_TYPE    │
         └─────────────────────────────────────┘
         Reset insights for specific symbol and type
         
         Resets AI analysis status to EMPTY for insights
         matching the given symbol and optionally type.
         
         Parameters:
         - symbol: Symbol to reset
         - feed_type: Optional feed type to filter by
         
         Returns:
         - Tuple of (insights_reset_count, tasks_cancelled_count)
        """
        with get_db_session() as conn:
            # First get the insights to reset
            query = """
                SELECT id, TaskStatus 
                FROM insights 
                WHERE symbol = ?
            """
            params = [symbol]
            
            if feed_type:
                query += " AND type = ?"
                params.append(feed_type.value)
                
            insights = conn.execute(query, params).fetchall()
            
            if not insights:
                debug_info(f"No insights found for symbol {symbol}" + (f" and type {feed_type.value}" if feed_type else ""))
                return 0, 0
            
            insight_ids = [insight['id'] for insight in insights]
            
            # Reset all insights to EMPTY status
            placeholders = ','.join(['?' for _ in insight_ids])
            reset_count = conn.execute(f"""
                UPDATE insights
                SET TaskStatus = ?,
                    AISummary = NULL,
                    AIAction = NULL,
                    AIConfidence = NULL,
                    AIEventTime = NULL,
                    AILevels = NULL,
                    AIImageSummary = NULL
                WHERE id IN ({placeholders})
            """, [TaskStatus.EMPTY.value] + insight_ids).rowcount
            
            # Also cancel any associated tasks in the queue
            tasks_cancelled = 0
            try:
                # Cancel tasks for these insights
                tasks_result = conn.execute(f"""
                    UPDATE simple_tasks
                    SET status = ?, completed_at = ?, error = ?
                    WHERE entity_type = 'insight' 
                    AND entity_id IN ({placeholders})
                    AND status IN (?, ?, ?)
                """, [
                    TaskStatus.CANCELLED.value,
                    datetime.now().isoformat(),
                    f"Reset tasks for symbol {symbol}" + (f" type {feed_type.value}" if feed_type else ""),
                ] + insight_ids + [
                    TaskStatus.PENDING.value,
                    TaskStatus.PROCESSING.value,
                    TaskStatus.FAILED.value
                ])
                tasks_cancelled = tasks_result.rowcount
            except Exception as e:
                debug_error(f"Error cancelling tasks: {e}")
            
            debug_info(f"Reset {reset_count} insights and cancelled {tasks_cancelled} tasks for symbol {symbol}" + 
                      (f" type {feed_type.value}" if feed_type else ""))
            
            return reset_count, tasks_cancelled



