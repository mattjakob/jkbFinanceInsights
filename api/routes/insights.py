"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        INSIGHTS ROUTES              │
 *  └─────────────────────────────────────┘
 *  API routes for insights operations
 * 
 *  Provides RESTful endpoints for CRUD operations on insights
 *  using the refactored repository pattern.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - FastAPI router with insights endpoints
 * 
 *  Notes:
 *  - Uses dependency injection for repository
 *  - Returns standardized responses
 */
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime

from core import InsightModel, FeedType
from data import InsightsRepository
from debugger import debug_info, debug_error, debug_success

# Create router
router = APIRouter(prefix="/api/insights", tags=["insights"])

# Repository instance
insights_repo = InsightsRepository()


@router.get("", response_model=List[Dict[str, Any]])
async def get_insights(
    type: Optional[str] = Query(None, description="Filter by feed type"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    limit: Optional[int] = Query(100, description="Maximum results"),
    offset: int = Query(0, description="Skip first N results")
):
    """
     ┌─────────────────────────────────────┐
     │         GET_INSIGHTS                │
     └─────────────────────────────────────┘
     Get insights with optional filters
     
     Returns a list of insights filtered by type and/or symbol.
    """
    try:
        insights = insights_repo.find_all(
            type_filter=type,
            symbol_filter=symbol,
            limit=limit,
            offset=offset
        )
        
        # Convert to dict for response
        return [insight.to_dict() for insight in insights]
        
    except Exception as e:
        debug_error(f"Error getting insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{insight_id}", response_model=Dict[str, Any])
async def get_insight(insight_id: int):
    """
     ┌─────────────────────────────────────┐
     │          GET_INSIGHT                │
     └─────────────────────────────────────┘
     Get a specific insight by ID
    """
    insight = insights_repo.get_by_id(insight_id)
    
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    return insight.to_dict()


@router.post("", response_model=Dict[str, Any])
async def create_insight(insight_data: Dict[str, Any]):
    """
     ┌─────────────────────────────────────┐
     │        CREATE_INSIGHT               │
     └─────────────────────────────────────┘
     Create a new insight
     
     Creates an insight from raw data. Primarily used
     for testing - production insights come from scrapers.
    """
    try:
        # Create InsightModel from data
        insight = InsightModel(
            type=FeedType(insight_data['type']),
            title=insight_data['title'],
            content=insight_data['content'],
            symbol=insight_data['symbol'],
            exchange=insight_data['exchange'],
            time_fetched=datetime.now(),
            time_posted=datetime.fromisoformat(insight_data.get('timePosted', datetime.now().isoformat())),
            image_url=insight_data.get('imageURL')
        )
        
        # Store in database
        insight_id, is_new = insights_repo.create(insight)
        
        # Get created insight
        created = insights_repo.get_by_id(insight_id)
        
        return {
            **created.to_dict(),
            'is_new': is_new
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        debug_error(f"Error creating insight: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{insight_id}", response_model=Dict[str, Any])
async def update_insight(insight_id: int, updates: Dict[str, Any]):
    """
     ┌─────────────────────────────────────┐
     │        UPDATE_INSIGHT               │
     └─────────────────────────────────────┘
     Update an existing insight
    """
    # Check if insight exists
    insight = insights_repo.get_by_id(insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    # Update insight
    success = insights_repo.update(insight_id, updates)
    
    if not success:
        raise HTTPException(status_code=500, detail="Update failed")
    
    # Return updated insight
    updated = insights_repo.get_by_id(insight_id)
    return updated.to_dict()


@router.delete("/{insight_id}")
async def delete_insight(insight_id: int):
    """
     ┌─────────────────────────────────────┐
     │        DELETE_INSIGHT               │
     └─────────────────────────────────────┘
     Delete an insight
    """
    success = insights_repo.delete(insight_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    return {"message": "Insight deleted successfully"}


@router.delete("")
async def delete_insights_by_type(type: str):
    """
     ┌─────────────────────────────────────┐
     │     DELETE_INSIGHTS_BY_TYPE         │
     └─────────────────────────────────────┘
     Delete all insights of a specific type
    """
    try:
        # Handle empty string as "delete all"
        if type == "" or type.upper() == "ALL":
            # Delete all insights
            all_deleted = 0
            all_ids = []
            
            for feed_type in FeedType:
                count, ids = insights_repo.delete_by_type(feed_type)
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
        else:
            # Delete specific type
            feed_type = FeedType(type)
            count, ids = insights_repo.delete_by_type(feed_type)
            
            debug_success(f"Deleted {count} insights of type {type}")
            
            return {
                "success": True,
                "message": f"Deleted {count} insights of type {type}",
                "deleted_count": count,
                "failed_count": 0,
                "deleted_ids": ids
            }
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid feed type: {type}")
    except Exception as e:
        debug_error(f"Error deleting insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{insight_id}/reset-ai")
async def reset_insight_ai(insight_id: int):
    """
     ┌─────────────────────────────────────┐
     │       RESET_INSIGHT_AI              │
     └─────────────────────────────────────┘
     Reset AI analysis fields for an insight
    """
    # Check if insight exists
    insight = insights_repo.get_by_id(insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    # Reset AI fields
    updates = {
        'ai_summary': None,
        'ai_action': None,
        'ai_confidence': None,
        'ai_event_time': None,
        'ai_levels': None,
        'ai_image_summary': None,
        'ai_analysis_status': 'pending'
    }
    
    success = insights_repo.update(insight_id, updates)
    
    if success:
        return {
            "success": True,
            "message": f"Reset AI fields for insight #{insight_id}"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to reset AI fields")



