"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         REPORTS API ROUTES          │
 *  └─────────────────────────────────────┘
 *  API endpoints for managing AI analysis reports
 * 
 *  Provides RESTful endpoints for creating, reading, updating,
 *  and deleting AI analysis reports.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - FastAPI router instance
 * 
 *  Notes:
 *  - Follows REST conventions
 *  - Returns JSON responses
 *  - Handles errors gracefully
 */
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from core.models import ReportModel, AIAction, AIAnalysisStatus
from data.repositories.reports import get_reports_repository
from debugger import debug_info, debug_error, debug_success


# Pydantic models for request/response
class ReportCreate(BaseModel):
    """Request model for creating a report"""
    symbol: str
    ai_summary: str = Field(alias="AISummary")
    ai_action: str = Field(alias="AIAction")
    ai_confidence: float = Field(alias="AIConfidence")
    ai_event_time: Optional[str] = Field(None, alias="AIEventTime")
    ai_levels: Optional[str] = Field(None, alias="AILevels")
    ai_analysis_status: Optional[str] = Field("completed", alias="AIAnalysisStatus")
    
    class Config:
        populate_by_name = True


class ReportUpdate(BaseModel):
    """Request model for updating a report"""
    ai_summary: Optional[str] = Field(None, alias="AISummary")
    ai_action: Optional[str] = Field(None, alias="AIAction")
    ai_confidence: Optional[float] = Field(None, alias="AIConfidence")
    ai_event_time: Optional[str] = Field(None, alias="AIEventTime")
    ai_levels: Optional[str] = Field(None, alias="AILevels")
    ai_analysis_status: Optional[str] = Field(None, alias="AIAnalysisStatus")
    
    class Config:
        populate_by_name = True


class ReportResponse(BaseModel):
    """Response model for report data"""
    id: int
    timeFetched: str
    symbol: str
    AISummary: str
    AIAction: str
    AIConfidence: float
    AIEventTime: Optional[str]
    AILevels: Optional[str]
    AIAnalysisStatus: str


# Create router
router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/", response_model=ReportResponse)
async def create_report(report_data: ReportCreate):
    """
     ┌─────────────────────────────────────┐
     │         CREATE_REPORT               │
     └─────────────────────────────────────┘
     Create a new AI analysis report
     
     Creates a report with the provided analysis data.
    """
    try:
        # Create report model
        report = ReportModel(
            time_fetched=datetime.now(),
            symbol=report_data.symbol.upper(),
            ai_summary=report_data.ai_summary,
            ai_action=AIAction(report_data.ai_action.upper()),
            ai_confidence=report_data.ai_confidence,
            ai_event_time=report_data.ai_event_time,
            ai_levels=report_data.ai_levels,
            ai_analysis_status=AIAnalysisStatus(report_data.ai_analysis_status)
        )
        
        # Save to database
        repo = get_reports_repository()
        report_id = repo.create(report)
        
        # Get created report
        created_report = repo.get_by_id(report_id)
        if not created_report:
            raise HTTPException(status_code=500, detail="Failed to retrieve created report")
        
        debug_success(f"Created report {report_id} for {report.symbol}")
        return ReportResponse(**created_report.to_dict())
        
    except ValueError as e:
        debug_error(f"Invalid report data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        debug_error(f"Error creating report: {e}")
        raise HTTPException(status_code=500, detail="Failed to create report")


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int):
    """
     ┌─────────────────────────────────────┐
     │           GET_REPORT                │
     └─────────────────────────────────────┘
     Get a specific report by ID
    """
    repo = get_reports_repository()
    report = repo.get_by_id(report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return ReportResponse(**report.to_dict())


@router.get("/", response_model=List[ReportResponse])
async def get_reports(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    limit: Optional[int] = Query(100, description="Maximum number of reports"),
    offset: int = Query(0, description="Number of reports to skip")
):
    """
     ┌─────────────────────────────────────┐
     │          GET_REPORTS                │
     └─────────────────────────────────────┘
     Get reports with optional filtering
     
     Query parameters:
     - symbol: Filter by trading symbol
     - limit: Maximum number of results
     - offset: Pagination offset
    """
    repo = get_reports_repository()
    
    if symbol:
        reports = repo.get_by_symbol(symbol.upper(), limit=limit)
    else:
        reports = repo.get_all(limit=limit, offset=offset)
    
    return [ReportResponse(**report.to_dict()) for report in reports]


@router.get("/symbol/{symbol}", response_model=List[ReportResponse])
async def get_reports_by_symbol(
    symbol: str,
    limit: Optional[int] = Query(10, description="Maximum number of reports")
):
    """
     ┌─────────────────────────────────────┐
     │      GET_REPORTS_BY_SYMBOL          │
     └─────────────────────────────────────┘
     Get all reports for a specific symbol
    """
    repo = get_reports_repository()
    reports = repo.get_by_symbol(symbol.upper(), limit=limit)
    
    if not reports:
        return []  # Return empty list instead of 404
    
    return [ReportResponse(**report.to_dict()) for report in reports]


@router.get("/symbol/{symbol}/latest", response_model=Optional[ReportResponse])
async def get_latest_report_by_symbol(symbol: str):
    """
     ┌─────────────────────────────────────┐
     │    GET_LATEST_REPORT_BY_SYMBOL      │
     └─────────────────────────────────────┘
     Get the most recent report for a symbol
    """
    repo = get_reports_repository()
    report = repo.get_latest_by_symbol(symbol.upper())
    
    if not report:
        return None  # Return null instead of 404
    
    return ReportResponse(**report.to_dict())


@router.put("/{report_id}", response_model=ReportResponse)
async def update_report(report_id: int, update_data: ReportUpdate):
    """
     ┌─────────────────────────────────────┐
     │         UPDATE_REPORT               │
     └─────────────────────────────────────┘
     Update an existing report
    """
    repo = get_reports_repository()
    
    # Check if report exists
    report = repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Build update dict
    updates = {}
    if update_data.ai_summary is not None:
        updates["AISummary"] = update_data.ai_summary
    if update_data.ai_action is not None:
        updates["AIAction"] = update_data.ai_action.upper()
    if update_data.ai_confidence is not None:
        updates["AIConfidence"] = update_data.ai_confidence
    if update_data.ai_event_time is not None:
        updates["AIEventTime"] = update_data.ai_event_time
    if update_data.ai_levels is not None:
        updates["AILevels"] = update_data.ai_levels
    if update_data.ai_analysis_status is not None:
        updates["AIAnalysisStatus"] = update_data.ai_analysis_status
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Update report
    success = repo.update(report_id, updates)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update report")
    
    # Get updated report
    updated_report = repo.get_by_id(report_id)
    debug_info(f"Updated report {report_id}")
    
    return ReportResponse(**updated_report.to_dict())


@router.delete("/{report_id}")
async def delete_report(report_id: int):
    """
     ┌─────────────────────────────────────┐
     │         DELETE_REPORT               │
     └─────────────────────────────────────┘
     Delete a report
    """
    repo = get_reports_repository()
    
    # Check if report exists
    report = repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Delete report
    success = repo.delete(report_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete report")
    
    debug_info(f"Deleted report {report_id}")
    return {"message": "Report deleted successfully", "id": report_id}


@router.get("/high-confidence/{min_confidence}", response_model=List[ReportResponse])
async def get_high_confidence_reports(
    min_confidence: float = 0.8,
    limit: Optional[int] = Query(50, description="Maximum number of reports")
):
    """
     ┌─────────────────────────────────────┐
     │   GET_HIGH_CONFIDENCE_REPORTS       │
     └─────────────────────────────────────┘
     Get reports with high confidence scores
    """
    repo = get_reports_repository()
    reports = repo.get_high_confidence_reports(min_confidence)
    
    # Apply limit
    if limit:
        reports = reports[:limit]
    
    return [ReportResponse(**report.to_dict()) for report in reports]


@router.get("/summary/by-action", response_model=Dict[str, int])
async def get_reports_summary_by_action():
    """
     ┌─────────────────────────────────────┐
     │    GET_REPORTS_SUMMARY_BY_ACTION    │
     └─────────────────────────────────────┘
     Get count of reports grouped by action
    """
    repo = get_reports_repository()
    summary = repo.get_summary_by_action()
    return summary


@router.delete("/cleanup/{days}")
async def cleanup_old_reports(days: int = 30):
    """
     ┌─────────────────────────────────────┐
     │       CLEANUP_OLD_REPORTS           │
     └─────────────────────────────────────┘
     Delete reports older than specified days
    """
    if days < 1:
        raise HTTPException(status_code=400, detail="Days must be greater than 0")
    
    repo = get_reports_repository()
    deleted_count = repo.delete_old_reports(days)
    
    debug_info(f"Cleaned up {deleted_count} reports older than {days} days")
    return {
        "message": f"Deleted {deleted_count} old reports",
        "days": days,
        "count": deleted_count
    }
