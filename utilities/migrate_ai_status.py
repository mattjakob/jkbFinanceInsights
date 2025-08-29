"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │      MIGRATE AI STATUS              │
 *  └─────────────────────────────────────┘
 *  Migration utility for AIAnalysisStatus
 * 
 *  Updates existing insights to use the new EMPTY status
 *  and ensures proper status transitions.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - Migration results
 * 
 *  Notes:
 *  - Run this after updating the AIAnalysisStatus enum
 *  - Updates existing insights to proper status values
 */

import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, List

class AIStatusMigration:
    def __init__(self, db_path: str = "finance_insights.db"):
        self.db_path = db_path
        
    def migrate_ai_status(self) -> Dict[str, Any]:
        """Migrate existing insights to new AIAnalysisStatus values"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current status distribution
            cursor.execute("""
                SELECT AIAnalysisStatus, COUNT(*) as count
                FROM insights
                GROUP BY AIAnalysisStatus
            """)
            current_statuses = dict(cursor.fetchall())
            
            # Migration rules:
            # - NULL or empty string -> 'empty'
            # - 'pending' -> 'empty' (if no AI summary)
            # - 'processing' -> 'empty' (if no AI summary)
            # - 'failed' -> 'empty' (if no AI summary)
            # - 'completed' -> 'completed' (keep as is)
            
            # Update NULL/empty statuses to 'empty'
            cursor.execute("""
                UPDATE insights 
                SET AIAnalysisStatus = 'empty'
                WHERE AIAnalysisStatus IS NULL 
                   OR AIAnalysisStatus = ''
            """)
            null_updated = cursor.rowcount
            
            # Update insights with no AI summary to 'empty'
            cursor.execute("""
                UPDATE insights 
                SET AIAnalysisStatus = 'empty'
                WHERE (AIAnalysisStatus = 'pending' 
                    OR AIAnalysisStatus = 'processing' 
                    OR AIAnalysisStatus = 'failed')
                  AND (AISummary IS NULL OR AISummary = '')
            """)
            no_summary_updated = cursor.rowcount
            
            # Update insights with failed status but no summary to 'empty'
            cursor.execute("""
                UPDATE insights 
                SET AIAnalysisStatus = 'empty'
                WHERE AIAnalysisStatus = 'failed'
                  AND (AISummary IS NULL OR AISummary = '')
            """)
            failed_no_summary_updated = cursor.rowcount
            
            # Get new status distribution
            cursor.execute("""
                SELECT AIAnalysisStatus, COUNT(*) as count
                FROM insights
                GROUP BY AIAnalysisStatus
            """)
            new_statuses = dict(cursor.fetchall())
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'migration_summary': {
                    'null_statuses_updated': null_updated,
                    'no_summary_updated': no_summary_updated,
                    'failed_no_summary_updated': failed_no_summary_updated,
                    'total_updated': null_updated + no_summary_updated + failed_no_summary_updated
                },
                'status_distribution': {
                    'before': current_statuses,
                    'after': new_statuses
                },
                'message': f'Migration completed: {null_updated + no_summary_updated + failed_no_summary_updated} insights updated'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Migration failed'
            }
    
    def validate_migration(self) -> Dict[str, Any]:
        """Validate that migration was successful"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for any invalid statuses
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM insights
                WHERE AIAnalysisStatus NOT IN ('empty', 'pending', 'processing', 'completed', 'failed')
            """)
            invalid_statuses = cursor.fetchone()[0]
            
            # Check for insights with completed status but no AI summary
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM insights
                WHERE AIAnalysisStatus = 'completed'
                  AND (AISummary IS NULL OR AISummary = '')
            """)
            completed_no_summary = cursor.fetchone()[0]
            
            # Check for insights with pending/processing status but no AI summary
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM insights
                WHERE AIAnalysisStatus IN ('pending', 'processing')
                  AND (AISummary IS NULL OR AISummary = '')
            """)
            pending_processing_no_summary = cursor.fetchone()[0]
            
            conn.close()
            
            validation_passed = (
                invalid_statuses == 0 and
                completed_no_summary == 0 and
                pending_processing_no_summary == 0
            )
            
            return {
                'success': True,
                'validation_passed': validation_passed,
                'issues': {
                    'invalid_statuses': invalid_statuses,
                    'completed_no_summary': completed_no_summary,
                    'pending_processing_no_summary': pending_processing_no_summary
                },
                'message': 'Validation passed' if validation_passed else 'Validation failed - issues found'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Validation failed'
            }
    
    def get_migration_report(self) -> Dict[str, Any]:
        """Get comprehensive migration report"""
        migration_result = self.migrate_ai_status()
        if not migration_result['success']:
            return migration_result
        
        validation_result = self.validate_migration()
        
        return {
            'success': True,
            'migration': migration_result,
            'validation': validation_result,
            'timestamp': datetime.now().isoformat(),
            'recommendations': [
                'All insights now use proper AIAnalysisStatus values',
                'EMPTY status indicates insights ready for analysis',
                'PENDING status indicates insights queued for analysis',
                'PROCESSING status indicates insights being analyzed',
                'COMPLETED status indicates successful analysis',
                'FAILED status indicates analysis failed (will be reset to EMPTY)'
            ]
        }

# Global instance
migration = AIStatusMigration()

def migrate_ai_status() -> Dict[str, Any]:
    """Migrate AI analysis statuses"""
    return migration.migrate_ai_status()

def validate_migration() -> Dict[str, Any]:
    """Validate migration results"""
    return migration.validate_migration()

def get_migration_report() -> Dict[str, Any]:
    """Get complete migration report"""
    return migration.get_migration_report()
