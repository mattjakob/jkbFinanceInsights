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

from services import InsightsService
from debugger import debug_info, debug_error, debug_success

# Create router
router = APIRouter(prefix="/api/insights", tags=["insights"])

# Service instance
insights_service = InsightsService()


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
        return insights_service.get_insights(
            type_filter=type,
            symbol_filter=symbol,
            limit=limit,
            offset=offset
        )
        
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
    insight_data = insights_service.get_insight_by_id(insight_id)
    
    if not insight_data:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    return insight_data


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
        return insights_service.create_insight(insight_data)
        
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
    updated = insights_service.update_insight(insight_id, updates)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    return updated


@router.delete("/{insight_id}")
async def delete_insight(insight_id: int):
    """
     ┌─────────────────────────────────────┐
     │        DELETE_INSIGHT               │
     └─────────────────────────────────────┘
     Delete an insight
    """
    success = insights_service.delete_insight(insight_id)
    
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
        return insights_service.delete_insights_by_type(type)
        
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
    success = insights_service.reset_insight_ai(insight_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    return {
        "success": True,
        "message": f"Reset AI fields for insight #{insight_id}"
    }






