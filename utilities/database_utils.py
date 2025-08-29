"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        DATABASE UTILITIES           │
 *  └─────────────────────────────────────┘
 *  Advanced database management utilities
 * 
 *  Provides database maintenance, optimization,
 *  and management functions.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - Database operation results
 * 
 *  Notes:
 *  - Uses SQLite for database operations
 *  - Includes backup, restore, and optimization
 *  - Provides data export/import functionality
 */

import sqlite3
import os
import shutil
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import zipfile
import tempfile

class DatabaseUtils:
    def __init__(self, db_path: str = "finance_insights.db"):
        self.db_path = db_path
        self.backup_dir = "database_backups"
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get comprehensive database information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get database size
            db_size = os.path.getsize(self.db_path)
            
            # Get table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get row counts for each table
            table_counts = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_counts[table] = count
                except:
                    table_counts[table] = 0
            
            # Get database statistics
            cursor.execute("PRAGMA stats")
            stats = cursor.fetchall()
            
            # Get database configuration
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA cache_size")
            cache_size = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'database_path': self.db_path,
                'size_mb': round(db_size / (1024 * 1024), 2),
                'tables': tables,
                'table_counts': table_counts,
                'total_rows': sum(table_counts.values()),
                'page_size': page_size,
                'cache_size': cache_size,
                'journal_mode': journal_mode,
                'last_modified': datetime.fromtimestamp(os.path.getmtime(self.db_path)).isoformat(),
                'backup_count': len(self.get_backup_files())
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def create_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a database backup"""
        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}.db"
            
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Create backup
            shutil.copy2(self.db_path, backup_path)
            
            # Create metadata file
            metadata = {
                'backup_name': backup_name,
                'original_path': self.db_path,
                'backup_path': backup_path,
                'created_at': datetime.now().isoformat(),
                'size_mb': round(os.path.getsize(backup_path) / (1024 * 1024), 2),
                'database_info': self.get_database_info()
            }
            
            metadata_path = backup_path.replace('.db', '_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return {
                'success': True,
                'backup_path': backup_path,
                'metadata_path': metadata_path,
                'size_mb': metadata['size_mb'],
                'message': f'Backup created successfully: {backup_name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Backup failed'
            }
    
    def restore_backup(self, backup_name: str) -> Dict[str, Any]:
        """Restore database from backup"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            if not os.path.exists(backup_path):
                return {
                    'success': False,
                    'error': f'Backup not found: {backup_name}',
                    'message': 'Backup file does not exist'
                }
            
            # Create current database backup before restore
            current_backup = self.create_backup(f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            
            # Restore database
            shutil.copy2(backup_path, self.db_path)
            
            return {
                'success': True,
                'restored_from': backup_path,
                'pre_restore_backup': current_backup['backup_path'],
                'message': f'Database restored from: {backup_name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Restore failed'
            }
    
    def get_backup_files(self) -> List[Dict[str, Any]]:
        """Get list of available backup files"""
        try:
            backups = []
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.db'):
                    file_path = os.path.join(self.backup_dir, filename)
                    metadata_path = file_path.replace('.db', '_metadata.json')
                    
                    backup_info = {
                        'filename': filename,
                        'path': file_path,
                        'size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2),
                        'created_at': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    }
                    
                    # Try to load metadata
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                                backup_info['metadata'] = metadata
                        except:
                            pass
                    
                    backups.append(backup_info)
            
            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            return backups
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def cleanup_old_backups(self, keep_days: int = 30) -> Dict[str, Any]:
        """Clean up old backup files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            deleted_count = 0
            deleted_files = []
            
            for backup in self.get_backup_files():
                backup_date = datetime.fromisoformat(backup['created_at'])
                if backup_date < cutoff_date:
                    try:
                        # Delete backup file
                        os.remove(backup['path'])
                        
                        # Delete metadata file if it exists
                        metadata_path = backup['path'].replace('.db', '_metadata.json')
                        if os.path.exists(metadata_path):
                            os.remove(metadata_path)
                        
                        deleted_count += 1
                        deleted_files.append(backup['filename'])
                    except Exception as e:
                        continue
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'deleted_files': deleted_files,
                'kept_days': keep_days,
                'message': f'Cleaned up {deleted_count} old backups'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Cleanup failed'
            }
    
    def export_data(self, format_type: str = 'json', table: Optional[str] = None) -> Dict[str, Any]:
        """Export database data in specified format"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if table:
                # Export specific table
                cursor.execute(f"SELECT * FROM {table}")
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                
                data = {
                    'table': table,
                    'columns': columns,
                    'rows': [dict(zip(columns, row)) for row in rows],
                    'row_count': len(rows)
                }
            else:
                # Export all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                data = {}
                for table_name in tables:
                    cursor.execute(f"SELECT * FROM {table_name}")
                    columns = [description[0] for description in cursor.description]
                    rows = cursor.fetchall()
                    
                    data[table_name] = {
                        'columns': columns,
                        'rows': [dict(zip(columns, row)) for row in rows],
                        'row_count': len(rows)
                    }
            
            conn.close()
            
            # Format output
            if format_type == 'json':
                output = json.dumps(data, indent=2, default=str)
            elif format_type == 'csv':
                output = self._convert_to_csv(data)
            else:
                output = json.dumps(data, indent=2, default=str)
            
            # Create export file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_filename = f"export_{table or 'all'}_{timestamp}.{format_type}"
            export_path = os.path.join(self.backup_dir, export_filename)
            
            with open(export_path, 'w') as f:
                f.write(output)
            
            return {
                'success': True,
                'export_path': export_path,
                'filename': export_filename,
                'format': format_type,
                'size_mb': round(os.path.getsize(export_path) / (1024 * 1024), 2),
                'message': f'Data exported successfully: {export_filename}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Export failed'
            }
    
    def _convert_to_csv(self, data: Dict[str, Any]) -> str:
        """Convert data to CSV format"""
        if 'table' in data:
            # Single table
            return self._table_to_csv(data)
        else:
            # Multiple tables
            csv_parts = []
            for table_name, table_data in data.items():
                csv_parts.append(f"=== {table_name} ===")
                csv_parts.append(self._table_to_csv(table_data))
                csv_parts.append("")
            return "\n".join(csv_parts)
    
    def _table_to_csv(self, table_data: Dict[str, Any]) -> str:
        """Convert single table to CSV"""
        if not table_data['rows']:
            return ""
        
        output = []
        output.append(",".join(table_data['columns']))
        
        for row in table_data['rows']:
            csv_row = []
            for value in row.values():
                if isinstance(value, str) and ',' in value:
                    csv_row.append(f'"{value}"')
                else:
                    csv_row.append(str(value))
            output.append(",".join(csv_row))
        
        return "\n".join(output)
    
    def optimize_database(self) -> Dict[str, Any]:
        """Optimize database performance"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Run optimization commands
            cursor.execute("VACUUM")
            cursor.execute("ANALYZE")
            cursor.execute("REINDEX")
            
            # Get optimization results
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA optimize")
            optimize_result = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'success': True,
                'integrity_check': integrity,
                'optimize_result': optimize_result,
                'message': 'Database optimized successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Optimization failed'
            }
    
    def reset_failed_ai_analysis(self) -> Dict[str, Any]:
        """Reset failed AI analysis records"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count failed records
            cursor.execute("SELECT COUNT(*) FROM insights WHERE ai_analysis_status = 'failed'")
            failed_count = cursor.fetchone()[0]
            
            # Reset failed records to EMPTY status
            cursor.execute("""
                UPDATE insights 
                SET ai_analysis_status = 'empty', 
                    ai_summary = NULL,
                    ai_action = NULL,
                    ai_confidence = NULL
                WHERE ai_analysis_status = 'failed'
            """)
            
            updated_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'failed_count': failed_count,
                'updated_count': updated_count,
                'message': f'Reset {updated_count} failed AI analysis records to EMPTY status'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Reset failed'
            }
    
    def reset_processing_ai_analysis(self) -> Dict[str, Any]:
        """Reset stuck processing AI analysis records"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Count processing records older than 1 hour
            cutoff_time = datetime.now() - timedelta(hours=1)
            cursor.execute("""
                SELECT COUNT(*) FROM insights 
                WHERE ai_analysis_status = 'processing' 
                AND time_fetched < ?
            """, (cutoff_time.isoformat(),))
            
            processing_count = cursor.fetchone()[0]
            
            # Reset stuck processing records to EMPTY status
            cursor.execute("""
                UPDATE insights 
                SET ai_analysis_status = 'empty'
                WHERE ai_analysis_status = 'processing' 
                AND time_fetched < ?
            """, (cutoff_time.isoformat(),))
            
            updated_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'processing_count': processing_count,
                'updated_count': updated_count,
                'message': f'Reset {updated_count} stuck processing AI analysis records to EMPTY status'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Reset failed'
            }

# Global instance
db_utils = DatabaseUtils()

def get_database_info() -> Dict[str, Any]:
    """Get database information"""
    return db_utils.get_database_info()

def create_backup(backup_name: Optional[str] = None) -> Dict[str, Any]:
    """Create database backup"""
    return db_utils.create_backup(backup_name)

def restore_backup(backup_name: str) -> Dict[str, Any]:
    """Restore database from backup"""
    return db_utils.restore_backup(backup_name)

def get_backup_files() -> List[Dict[str, Any]]:
    """Get backup files list"""
    return db_utils.get_backup_files()

def cleanup_old_backups(keep_days: int = 30) -> Dict[str, Any]:
    """Clean up old backups"""
    return db_utils.cleanup_old_backups(keep_days)

def export_data(format_type: str = 'json', table: Optional[str] = None) -> Dict[str, Any]:
    """Export database data"""
    return db_utils.export_data(format_type, table)

def optimize_database() -> Dict[str, Any]:
    """Optimize database"""
    return db_utils.optimize_database()

def reset_failed_ai_analysis() -> Dict[str, Any]:
    """Reset failed AI analysis"""
    return db_utils.reset_failed_ai_analysis()

def reset_processing_ai_analysis() -> Dict[str, Any]:
    """Reset processing AI analysis"""
    return db_utils.reset_processing_ai_analysis()
