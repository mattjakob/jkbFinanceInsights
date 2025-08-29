"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        SYSTEM MONITOR               │
 *  └─────────────────────────────────────┘
 *  Real-time system monitoring utility
 * 
 *  Provides live system metrics, performance data,
 *  and resource utilization monitoring.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - System metrics and performance data
 * 
 *  Notes:
 *  - Uses psutil for system monitoring
 *  - Provides real-time updates
 *  - Includes memory, CPU, disk, and network stats
 */

import psutil
import time
from datetime import datetime
from typing import Dict, Any, List
import json

class SystemMonitor:
    def __init__(self):
        self.metrics_history = []
        self.max_history = 100
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Process metrics
            processes = len(psutil.pids())
            
            # Boot time
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'usage_percent': cpu_percent,
                    'count': cpu_count,
                    'frequency_mhz': cpu_freq.current if cpu_freq else None,
                    'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                },
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'percent': memory.percent,
                    'swap_total_gb': round(swap.total / (1024**3), 2),
                    'swap_used_gb': round(swap.used / (1024**3), 2)
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'used_gb': round(disk.used / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'percent': round((disk.used / disk.total) * 100, 2),
                    'read_bytes_mb': round(disk_io.read_bytes / (1024**2), 2) if disk_io else 0,
                    'write_bytes_mb': round(disk_io.write_bytes / (1024**2), 2) if disk_io else 0
                },
                'network': {
                    'bytes_sent_mb': round(network.bytes_sent / (1024**2), 2),
                    'bytes_recv_mb': round(network.bytes_recv / (1024**2), 2),
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'system': {
                    'processes': processes,
                    'boot_time': boot_time.isoformat(),
                    'uptime_hours': round(uptime.total_seconds() / 3600, 2)
                }
            }
            
            # Store in history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
                
            return metrics
            
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_performance_trends(self) -> Dict[str, Any]:
        """Get performance trends from historical data"""
        if len(self.metrics_history) < 2:
            return {}
            
        try:
            recent = self.metrics_history[-1]
            previous = self.metrics_history[-2]
            
            trends = {
                'cpu_change': recent['cpu']['usage_percent'] - previous['cpu']['usage_percent'],
                'memory_change': recent['memory']['percent'] - previous['memory']['percent'],
                'disk_change': recent['disk']['percent'] - previous['disk']['percent'],
                'process_change': recent['system']['processes'] - previous['system']['processes']
            }
            
            return trends
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_system_health_score(self) -> Dict[str, Any]:
        """Calculate overall system health score"""
        try:
            metrics = self.get_system_metrics()
            
            # Health scoring (0-100, higher is better)
            cpu_score = max(0, 100 - metrics['cpu']['usage_percent'])
            memory_score = max(0, 100 - metrics['memory']['percent'])
            disk_score = max(0, 100 - metrics['disk']['percent'])
            
            # Weighted average
            overall_score = round((cpu_score * 0.4 + memory_score * 0.4 + disk_score * 0.2), 1)
            
            # Health status
            if overall_score >= 80:
                status = 'Excellent'
                color = 'success'
            elif overall_score >= 60:
                status = 'Good'
                color = 'info'
            elif overall_score >= 40:
                status = 'Fair'
                color = 'warning'
            else:
                status = 'Poor'
                color = 'danger'
            
            return {
                'score': overall_score,
                'status': status,
                'color': color,
                'cpu_score': cpu_score,
                'memory_score': memory_score,
                'disk_score': disk_score,
                'timestamp': metrics['timestamp']
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'score': 0,
                'status': 'Unknown'
            }
    
    def get_top_processes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top processes by resource usage"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] > 0 or proc_info['memory_percent'] > 0:
                        processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cpu_percent': round(proc_info['cpu_percent'], 1),
                            'memory_percent': round(proc_info['memory_percent'], 1),
                            'status': proc_info['status']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            return processes[:limit]
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def export_metrics(self, format_type: str = 'json') -> str:
        """Export metrics in specified format"""
        try:
            metrics = self.get_system_metrics()
            
            if format_type == 'json':
                return json.dumps(metrics, indent=2)
            elif format_type == 'csv':
                # Convert to CSV format
                csv_lines = ['Metric,Value,Unit']
                for category, data in metrics.items():
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, (int, float, str)):
                                csv_lines.append(f"{category}.{key},{value},")
                    else:
                        csv_lines.append(f"{category},{data},")
                return '\n'.join(csv_lines)
            else:
                return json.dumps(metrics, indent=2)
                
        except Exception as e:
            return f"Error exporting metrics: {str(e)}"

# Global instance
system_monitor = SystemMonitor()

def get_system_metrics() -> Dict[str, Any]:
    """Get current system metrics"""
    return system_monitor.get_system_metrics()

def get_performance_trends() -> Dict[str, Any]:
    """Get performance trends"""
    return system_monitor.get_performance_trends()

def get_system_health_score() -> Dict[str, Any]:
    """Get system health score"""
    return system_monitor.get_system_health_score()

def get_top_processes(limit: int = 10) -> List[Dict[str, Any]]:
    """Get top processes"""
    return system_monitor.get_top_processes(limit)

def export_metrics(format_type: str = 'json') -> str:
    """Export metrics"""
    return system_monitor.export_metrics(format_type)
