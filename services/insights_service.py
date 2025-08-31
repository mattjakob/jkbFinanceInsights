"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │   INSIGHT MANAGEMENT SERVICE        │
 *  └─────────────────────────────────────┘
 *  Business logic for insight data management
 * 
 *  Handles CRUD operations, deduplication, and database
 *  management for insights. This is the core service for
 *  managing insight data lifecycle.
 * 
 *  Parameters:
 *  - insights_repo: InsightsRepository instance
 * 
 *  Returns:
 *  - InsightManagementService instance
 * 
 *  Notes:
 *  - Manages insight lifecycle (create, read, update, delete)
 *  - Handles deduplication and validation
 *  - Does NOT handle scraping or AI analysis
 */
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from core import InsightModel, FeedType, TaskStatus, TaskName
from data import InsightsRepository
from debugger import debug_info, debug_success, debug_error


class InsightManagementService:
    """
     ┌─────────────────────────────────────┐
     │   INSIGHTMANAGEMENTSERVICE          │
     └─────────────────────────────────────┘
     Service for managing insight data lifecycle
     
     Handles CRUD operations, validation, and database
     coordination for insights. Focuses purely on data
     management, not scraping or analysis.
    """
    
    def __init__(self, insights_repo: Optional[InsightsRepository] = None):
        self.insights_repo = insights_repo or InsightsRepository()
    
    def get_insights(self, 
                    type_filter: Optional[str] = None,
                    symbol_filter: Optional[str] = None,
                    limit: Optional[int] = None,
                    offset: int = 0) -> List[Dict[str, Any]]:
        """
         ┌─────────────────────────────────────┐
         │         GET_INSIGHTS                │
         └─────────────────────────────────────┘
         Get insights with filters and pagination
         
         Parameters:
         - type_filter: Filter by feed type
         - symbol_filter: Filter by symbol
         - limit: Maximum results
         - offset: Skip first N results
         
         Returns:
         - List of insight dictionaries
        """
        insights = self.insights_repo.find_all(
            type_filter=type_filter,
            symbol_filter=symbol_filter,
            limit=limit,
            offset=offset
        )
        return [insight.to_dict() for insight in insights]
    
    def get_insight_by_id(self, insight_id: int) -> Optional[Dict[str, Any]]:
        """
         ┌─────────────────────────────────────┐
         │      GET_INSIGHT_BY_ID              │
         └─────────────────────────────────────┘
         Get specific insight by ID
         
         Parameters:
         - insight_id: ID of insight to retrieve
         
         Returns:
         - Insight dictionary or None
        """
        insight = self.insights_repo.get_by_id(insight_id)
        return insight.to_dict() if insight else None
    
    def create_insight(self, insight_data: Dict[str, Any]) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │       CREATE_INSIGHT                │
         └─────────────────────────────────────┘
         Create new insight with validation
         
         Parameters:
         - insight_data: Insight data dictionary
         
         Returns:
         - Created insight with metadata
        """
        # Validate required fields
        required_fields = ['type', 'title', 'content', 'symbol', 'exchange']
        for field in required_fields:
            if field not in insight_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Create InsightModel
        insight = InsightModel(
            type=FeedType(insight_data['type']),
            title=insight_data['title'],
            content=insight_data['content'],
            symbol=insight_data['symbol'],
            exchange=insight_data['exchange'],
            time_fetched=datetime.now(),
            time_posted=datetime.fromisoformat(
                insight_data.get('timePosted', datetime.now().isoformat())
            ),
            image_url=insight_data.get('imageURL')
        )
        
        # Store in database
        insight_id, is_new = self.insights_repo.create(insight)
        
        # Get created insight
        created = self.insights_repo.get_by_id(insight_id)
        
        return {
            **created.to_dict(),
            'is_new': is_new
        }
    
    def update_insight(self, insight_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
         ┌─────────────────────────────────────┐
         │       UPDATE_INSIGHT                │
         └─────────────────────────────────────┘
         Update existing insight
         
         Parameters:
         - insight_id: ID of insight to update
         - updates: Dictionary of fields to update
         
         Returns:
         - Updated insight dictionary or None
        """
        # Check if insight exists
        if not self.insights_repo.get_by_id(insight_id):
            return None
        
        # Update insight
        success = self.insights_repo.update(insight_id, updates)
        if not success:
            return None
        
        # Return updated insight
        updated = self.insights_repo.get_by_id(insight_id)
        return updated.to_dict() if updated else None
    
    def delete_insight(self, insight_id: int) -> bool:
        """
         ┌─────────────────────────────────────┐
         │       DELETE_INSIGHT                │
         └─────────────────────────────────────┘
         Delete insight by ID
         
         Parameters:
         - insight_id: ID of insight to delete
         
         Returns:
         - True if deleted, False if not found
        """
        return self.insights_repo.delete(insight_id)
    
    def delete_insights_by_type(self, feed_type: str) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │    DELETE_INSIGHTS_BY_TYPE          │
         └─────────────────────────────────────┘
         Delete all insights of specific type
         
         Parameters:
         - feed_type: Feed type to delete (or "ALL" for all types)
         
         Returns:
         - Dictionary with deletion results
        """
        if feed_type == "" or feed_type.upper() == "ALL":
            return self._delete_all_insights()
        else:
            # Delete specific type
            ft = FeedType(feed_type)
            count, ids = self.insights_repo.delete_by_type(ft)
            
            debug_success(f"Deleted {count} insights of type {feed_type}")
            
            return {
                "success": True,
                "message": f"Deleted {count} insights of type {feed_type}",
                "deleted_count": count,
                "failed_count": 0,
                "deleted_ids": ids
            }
    
    def reset_insight_ai(self, insight_id: int) -> bool:
        """
         ┌─────────────────────────────────────┐
         │       RESET_INSIGHT_AI              │
         └─────────────────────────────────────┘
         Reset AI analysis fields for insight
         
         Parameters:
         - insight_id: ID of insight to reset
         
         Returns:
         - True if reset successfully
        """
        # Check if insight exists
        if not self.insights_repo.get_by_id(insight_id):
            return False
        
        # Reset AI fields
        updates = {
            'ai_summary': None,
            'ai_action': None,
            'ai_confidence': None,
            'ai_event_time': None,
            'ai_levels': None,
            'ai_image_summary': None,
            'TaskStatus': TaskStatus.PENDING.value,
            'TaskName': TaskName.AI_ANALYSIS.value
        }
        
        return self.insights_repo.update(insight_id, updates)
    
    def _delete_all_insights(self) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │      _DELETE_ALL_INSIGHTS           │
         └─────────────────────────────────────┘
         Delete all insights across all feed types
         
         Returns:
         - Dictionary with deletion results
        """
        all_deleted = 0
        all_ids = []
        
        for ft in FeedType:
            count, ids = self.insights_repo.delete_by_type(ft)
            all_deleted += count
            all_ids.extend(ids)
        
        debug_success(f"Deleted {all_deleted} insights (all types)")
        
        return {
            "success": True,
            "message": f"Deleted {all_deleted} insights (all types)",
            "deleted_count": all_deleted,
            "failed_count": 0,
            "deleted_ids": all_ids
        }

