"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         REPORT SERVICE              │
 *  └─────────────────────────────────────┘
 *  Business logic for AI report generation and management
 * 
 *  Handles creation, retrieval, and management of AI analysis
 *  reports that aggregate insights for specific symbols.
 * 
 *  Parameters:
 *  - reports_repo: ReportsRepository instance
 * 
 *  Returns:
 *  - ReportService instance
 * 
 *  Notes:
 *  - Manages comprehensive AI reports
 *  - Coordinates with analysis service for report generation
 *  - Handles report lifecycle and queries
 */
"""

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta
from core.models import ReportModel, TradingAction, TaskStatus, TaskName
from data.repositories.reports import get_reports_repository
from tasks import get_task_queue
from debugger import debug_info, debug_error, debug_success


class ReportService:
    """
     ┌─────────────────────────────────────┐
     │         REPORTSERVICE               │
     └─────────────────────────────────────┘
     Service for managing AI analysis reports
     
     Handles report creation, retrieval, updates, and
     generation of comprehensive analysis reports.
    """
    
    def __init__(self, reports_repo=None):
        self.reports_repo = reports_repo or get_reports_repository()
        self.queue = None  # Will be initialized async
    
    async def create_report_generation_task(self, symbol: str, content: str = None, insights_count: int = 0) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │  CREATE_REPORT_GENERATION_TASK      │
         └─────────────────────────────────────┘
         Create task to generate AI report for symbol
         
         Parameters:
         - symbol: Trading symbol
         - content: Optional aggregated content
         - insights_count: Number of insights included
         
         Returns:
         - Dictionary with task creation results
        """
        try:
            # Initialize queue if needed
            if not self.queue:
                self.queue = await get_task_queue()
                
            task_id = await self.queue.add_task(
                TaskName.REPORT_GENERATION.value,
                {
                    'symbol': symbol,
                    'content': content,
                    'insights_count': insights_count
                },
                max_retries=2,
                entity_type='report',
                entity_id=None
            )
            
            # Task creation logged by queue
            
            return {
                "success": True,
                "message": f"Created report generation task for {symbol}",
                "task_id": task_id
            }
            
        except Exception as e:
            debug_error(f"Failed to create report generation task: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │        CREATE_REPORT                │
         └─────────────────────────────────────┘
         Create a new report directly
         
         Parameters:
         - report_data: Dictionary with report data
         
         Returns:
         - Created report with metadata
        """
        try:
            # Create report model
            report = ReportModel(
                time_fetched=datetime.now(),
                symbol=report_data['symbol'].upper(),
                ai_summary=report_data['ai_summary'],
                ai_action=TradingAction(report_data['ai_action'].upper()),
                ai_confidence=report_data['ai_confidence'],
                ai_event_time=report_data.get('ai_event_time'),
                ai_levels=report_data.get('ai_levels')
            )
            
            # Save to database
            report_id = self.reports_repo.create(report)
            
            # Get created report
            created = self.reports_repo.get_by_id(report_id)
            if not created:
                raise Exception("Failed to retrieve created report")
            
            debug_success(f"Created report {report_id} for {report.symbol}")
            
            return {
                "success": True,
                **created.to_dict()
            }
            
        except Exception as e:
            debug_error(f"Failed to create report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_report(self, report_id: int) -> Optional[Dict[str, Any]]:
        """
         ┌─────────────────────────────────────┐
         │         GET_REPORT                  │
         └─────────────────────────────────────┘
         Get report by ID
         
         Parameters:
         - report_id: Report ID
         
         Returns:
         - Report dictionary or None
        """
        report = self.reports_repo.get_by_id(report_id)
        return report.to_dict() if report else None
    
    def get_reports_for_symbol(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
         ┌─────────────────────────────────────┐
         │     GET_REPORTS_FOR_SYMBOL          │
         └─────────────────────────────────────┘
         Get reports for specific symbol
         
         Parameters:
         - symbol: Trading symbol
         - limit: Maximum reports to return
         
         Returns:
         - List of report dictionaries
        """
        reports = self.reports_repo.get_by_symbol(symbol, limit)
        return [report.to_dict() for report in reports]
    
    def get_latest_report(self, symbol: str = None) -> Optional[Dict[str, Any]]:
        """
         ┌─────────────────────────────────────┐
         │       GET_LATEST_REPORT             │
         └─────────────────────────────────────┘
         Get most recent report
         
         Parameters:
         - symbol: Optional symbol filter
         
         Returns:
         - Latest report dictionary or None
        """
        if symbol:
            reports = self.reports_repo.get_by_symbol(symbol, limit=1)
            report = reports[0] if reports else None
        else:
            report = self.reports_repo.get_latest()
        
        return report.to_dict() if report else None
    
    def get_unique_symbols(self) -> List[str]:
        """
         ┌─────────────────────────────────────┐
         │      GET_UNIQUE_SYMBOLS             │
         └─────────────────────────────────────┘
         Get unique symbols with reports
         
         Returns:
         - List of unique symbols
        """
        return self.reports_repo.get_unique_symbols()
    
    def delete_report(self, report_id: int) -> bool:
        """
         ┌─────────────────────────────────────┐
         │        DELETE_REPORT                │
         └─────────────────────────────────────┘
         Delete report by ID
         
         Parameters:
         - report_id: Report ID
         
         Returns:
         - True if deleted successfully
        """
        return self.reports_repo.delete(report_id)
    
    def cleanup_old_reports(self, days: int = 30) -> int:
        """
         ┌─────────────────────────────────────┐
         │      CLEANUP_OLD_REPORTS            │
         └─────────────────────────────────────┘
         Delete reports older than specified days
         
         Parameters:
         - days: Age threshold in days
         
         Returns:
         - Number of reports deleted
        """
        return self.reports_repo.delete_older_than(days)
    
    def get_high_confidence_reports(self, min_confidence: float = 0.8) -> List[Dict[str, Any]]:
        """
         ┌─────────────────────────────────────┐
         │   GET_HIGH_CONFIDENCE_REPORTS       │
         └─────────────────────────────────────┘
         Get reports with high confidence scores
         
         Parameters:
         - min_confidence: Minimum confidence threshold
         
         Returns:
         - List of high confidence report dictionaries
        """
        reports = self.reports_repo.get_high_confidence_reports(min_confidence)
        return [report.to_dict() for report in reports]
    
    def update_report(self, report_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
         ┌─────────────────────────────────────┐
         │        UPDATE_REPORT                │
         └─────────────────────────────────────┘
         Update existing report
         
         Parameters:
         - report_id: Report ID
         - updates: Dictionary of fields to update
         
         Returns:
         - Updated report dictionary or None
        """
        # Validate updates
        if 'ai_action' in updates:
            updates['ai_action'] = TradingAction(updates['ai_action'].upper()).value
        
        success = self.reports_repo.update(report_id, updates)
        if not success:
            return None
        
        # Return updated report
        report = self.reports_repo.get_by_id(report_id)
        return report.to_dict() if report else None
