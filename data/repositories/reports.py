"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        REPORTS REPOSITORY           │
 *  └─────────────────────────────────────┘
 *  Database repository for AI analysis reports
 * 
 *  Handles all database operations for the reports table,
 *  providing a clean interface for report management.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - ReportsRepository instance
 * 
 *  Notes:
 *  - Uses context managers for safe database access
 *  - Handles type conversions and validation
 */
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import sqlite3

from core.models import ReportModel, TaskStatus, TradingAction
from core.database import get_db_session, get_db_connection
from debugger import debug_info, debug_error, debug_success


class ReportsRepository:
    """
     ┌─────────────────────────────────────┐
     │       REPORTSREPOSITORY             │
     └─────────────────────────────────────┘
     Repository for managing AI analysis reports
     
     Provides CRUD operations and queries for report data.
    """
    
    def __init__(self):
        self.table_name = "reports"
    
    def create(self, report: ReportModel) -> int:
        """
         ┌─────────────────────────────────────┐
         │            CREATE                   │
         └─────────────────────────────────────┘
         Create a new report
         
         Parameters:
         - report: ReportModel instance (id should be None)
         
         Returns:
         - id of created report
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            data = report.to_dict()
            del data['id']  # Remove id for insert
            
            columns = list(data.keys())
            placeholders = ['?' for _ in columns]
            values = [data[col] for col in columns]
            
            query = f"""
                INSERT INTO {self.table_name} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """
            
            cursor.execute(query, values)
            report_id = cursor.lastrowid
            
            debug_success(f"Created report {report_id} for {report.symbol}")
            return report_id
    
    def get_by_id(self, report_id: int) -> Optional[ReportModel]:
        """
         ┌─────────────────────────────────────┐
         │           GET_BY_ID                 │
         └─────────────────────────────────────┘
         Get report by ID
         
         Parameters:
         - report_id: Report ID
         
         Returns:
         - ReportModel or None if not found
        """
        with get_db_session() as conn:
            cursor = conn.cursor()
            
            query = f"SELECT * FROM {self.table_name} WHERE id = ?"
            cursor.execute(query, (report_id,))
            
            row = cursor.fetchone()
            if row:
                return ReportModel.from_dict(dict(row))
            return None
    
    def get_by_symbol(self, symbol: str, limit: Optional[int] = None) -> List[ReportModel]:
        """
         ┌─────────────────────────────────────┐
         │         GET_BY_SYMBOL               │
         └─────────────────────────────────────┘
         Get reports for a specific symbol
         
         Parameters:
         - symbol: Trading symbol
         - limit: Maximum number of reports to return
         
         Returns:
         - List of ReportModel instances ordered by time (newest first)
        """
        with get_db_session() as conn:
            cursor = conn.cursor()
            
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE symbol = ?
                ORDER BY timeFetched DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (symbol,))
            
            reports = []
            for row in cursor.fetchall():
                reports.append(ReportModel.from_dict(dict(row)))
            
            return reports
    
    def get_latest_by_symbol(self, symbol: str) -> Optional[ReportModel]:
        """
         ┌─────────────────────────────────────┐
         │      GET_LATEST_BY_SYMBOL           │
         └─────────────────────────────────────┘
         Get the most recent report for a symbol
         
         Parameters:
         - symbol: Trading symbol
         
         Returns:
         - Latest ReportModel or None
        """
        reports = self.get_by_symbol(symbol, limit=1)
        return reports[0] if reports else None
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[ReportModel]:
        """
         ┌─────────────────────────────────────┐
         │            GET_ALL                  │
         └─────────────────────────────────────┘
         Get all reports
         
         Parameters:
         - limit: Maximum number of reports
         - offset: Number of reports to skip
         
         Returns:
         - List of ReportModel instances
        """
        with get_db_session() as conn:
            cursor = conn.cursor()
            
            query = f"""
                SELECT * FROM {self.table_name}
                ORDER BY timeFetched DESC
                LIMIT ? OFFSET ?
            """
            
            cursor.execute(query, (limit or -1, offset))
            
            reports = []
            for row in cursor.fetchall():
                reports.append(ReportModel.from_dict(dict(row)))
            
            return reports
    
    def get_recent(self, hours: int = 24) -> List[ReportModel]:
        """
         ┌─────────────────────────────────────┐
         │           GET_RECENT                │
         └─────────────────────────────────────┘
         Get reports from the last N hours
         
         Parameters:
         - hours: Number of hours to look back
         
         Returns:
         - List of recent ReportModel instances
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with get_db_session() as conn:
            cursor = conn.cursor()
            
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE timeFetched >= ?
                ORDER BY timeFetched DESC
            """
            
            cursor.execute(query, (cutoff_time.isoformat(),))
            
            reports = []
            for row in cursor.fetchall():
                reports.append(ReportModel.from_dict(dict(row)))
            
            return reports
    
    def update(self, report_id: int, updates: Dict[str, Any]) -> bool:
        """
         ┌─────────────────────────────────────┐
         │            UPDATE                   │
         └─────────────────────────────────────┘
         Update report fields
         
         Parameters:
         - report_id: Report ID
         - updates: Dictionary of fields to update
         
         Returns:
         - True if updated, False if not found
        """
        if not updates:
            return False
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Build update query
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            values.append(report_id)
            
            query = f"""
                UPDATE {self.table_name}
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """
            
            cursor.execute(query, values)
            
            if cursor.rowcount > 0:
                debug_info(f"Updated report {report_id}")
                return True
            return False
    
    def delete(self, report_id: int) -> bool:
        """
         ┌─────────────────────────────────────┐
         │            DELETE                   │
         └─────────────────────────────────────┘
         Delete a report
         
         Parameters:
         - report_id: Report ID
         
         Returns:
         - True if deleted, False if not found
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = f"DELETE FROM {self.table_name} WHERE id = ?"
            cursor.execute(query, (report_id,))
            
            if cursor.rowcount > 0:
                debug_info(f"Deleted report {report_id}")
                return True
            return False
    
    def delete_old_reports(self, days: int = 30) -> int:
        """
         ┌─────────────────────────────────────┐
         │       DELETE_OLD_REPORTS            │
         └─────────────────────────────────────┘
         Delete reports older than specified days
         
         Parameters:
         - days: Age threshold in days
         
         Returns:
         - Number of reports deleted
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = f"""
                DELETE FROM {self.table_name}
                WHERE datetime(timeFetched) < ?
            """
            
            cursor.execute(query, (cutoff_time.isoformat(),))
            deleted_count = cursor.rowcount
            
            if deleted_count > 0:
                debug_info(f"Deleted {deleted_count} old reports")
            
            return deleted_count
    
    def delete_all(self) -> int:
        """
         ┌─────────────────────────────────────┐
         │          DELETE_ALL                 │
         └─────────────────────────────────────┘
         Delete all reports from the database
         
         Returns:
         - Number of reports deleted
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get count before deletion
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            count = cursor.fetchone()[0]
            
            # Delete all reports
            query = f"DELETE FROM {self.table_name}"
            cursor.execute(query)
            
            deleted_count = cursor.rowcount
            
            if deleted_count > 0:
                debug_info(f"Deleted all {deleted_count} reports")
            
            return deleted_count
    
    def get_summary_by_action(self) -> Dict[str, int]:
        """
         ┌─────────────────────────────────────┐
         │      GET_SUMMARY_BY_ACTION          │
         └─────────────────────────────────────┘
         Get count of reports grouped by AI action
         
         Returns:
         - Dictionary mapping AIAction to count
        """
        with get_db_session() as conn:
            cursor = conn.cursor()
            
            query = f"""
                SELECT AIAction, COUNT(*) as count
                FROM {self.table_name}
                GROUP BY AIAction
            """
            
            cursor.execute(query)
            
            summary = {}
            for row in cursor.fetchall():
                summary[row['AIAction']] = row['count']
            
            return summary
    
    def get_high_confidence_reports(self, min_confidence: float = 0.8) -> List[ReportModel]:
        """
         ┌─────────────────────────────────────┐
         │    GET_HIGH_CONFIDENCE_REPORTS      │
         └─────────────────────────────────────┘
         Get reports with high confidence scores
         
         Parameters:
         - min_confidence: Minimum confidence threshold (0.0-1.0)
         
         Returns:
         - List of high-confidence ReportModel instances
        """
        with get_db_session() as conn:
            cursor = conn.cursor()
            
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE AIConfidence >= ?
                ORDER BY AIConfidence DESC, timeFetched DESC
            """
            
            cursor.execute(query, (min_confidence,))
            
            reports = []
            for row in cursor.fetchall():
                reports.append(ReportModel.from_dict(dict(row)))
            
            return reports


# Global instance
_reports_repo: Optional[ReportsRepository] = None


def get_reports_repository() -> ReportsRepository:
    """Get singleton ReportsRepository instance"""
    global _reports_repo
    if _reports_repo is None:
        _reports_repo = ReportsRepository()
    return _reports_repo
