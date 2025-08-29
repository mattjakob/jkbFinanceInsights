"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │      REALTIME DASHBOARD             │
 *  └─────────────────────────────────────┘
 *  Real-time system dashboard with live charts
 * 
 *  Provides a web-based dashboard with live system metrics,
 *  performance charts, and real-time updates using WebSockets.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - HTML dashboard with live charts
 * 
 *  Notes:
 *  - Uses Chart.js for beautiful visualizations
 *  - WebSocket for real-time updates
 *  - Responsive design with Bootstrap
 *  - Includes system health indicators
 */

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import psutil
import sqlite3
from pathlib import Path
import os

class RealtimeDashboard:
    def __init__(self):
        self.metrics_buffer = []
        self.max_buffer_size = 100
        self.update_interval = 2  # seconds
        
    def generate_dashboard_html(self) -> str:
        """Generate the complete dashboard HTML"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JKB Finance - Real-time Dashboard</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <style>
        body {{
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
            color: #ffffff;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            overflow-x: hidden;
        }}
        
        .dashboard-header {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1rem 0;
        }}
        
        .metric-card {{
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }}
        
        .metric-value {{
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }}
        
        .metric-label {{
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.7;
        }}
        
        .health-indicator {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 0.5rem;
        }}
        
        .health-excellent {{ background-color: #28a745; }}
        .health-good {{ background-color: #17a2b8; }}
        .health-fair {{ background-color: #ffc107; }}
        .health-poor {{ background-color: #dc3545; }}
        
        .chart-container {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        
        .status-badge {{
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 0.25rem 0.75rem;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .pulse {{
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
            100% {{ opacity: 1; }}
        }}
        
        .glow {{
            box-shadow: 0 0 20px rgba(255, 255, 255, 0.1);
        }}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div class="container-fluid">
            <div class="row align-items-center">
                <div class="col">
                    <h1 class="mb-0">
                        <i class="bi bi-speedometer2"></i>
                        JKB Finance - Real-time Dashboard
                    </h1>
                </div>
                <div class="col-auto">
                    <div class="d-flex align-items-center gap-3">
                        <div class="status-badge">
                            <i class="bi bi-circle-fill text-success pulse"></i>
                            Live
                        </div>
                        <div class="status-badge">
                            <span id="lastUpdate">--:--:--</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="container-fluid mt-4">
        <!-- System Health Overview -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="metric-card text-center">
                    <div class="metric-value" id="healthScore">--</div>
                    <div class="metric-label">System Health</div>
                    <div class="mt-2">
                        <span class="health-indicator" id="healthIndicator"></span>
                        <span id="healthStatus">--</span>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card text-center">
                    <div class="metric-value" id="cpuUsage">--</div>
                    <div class="metric-label">CPU Usage</div>
                    <div class="mt-2">
                        <div class="progress" style="height: 6px;">
                            <div class="progress-bar" id="cpuProgress" role="progressbar"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card text-center">
                    <div class="metric-value" id="memoryUsage">--</div>
                    <div class="metric-label">Memory Usage</div>
                    <div class="mt-2">
                        <div class="progress" style="height: 6px;">
                            <div class="progress-bar" id="memoryProgress" role="progressbar"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card text-center">
                    <div class="metric-value" id="diskUsage">--</div>
                    <div class="metric-label">Disk Usage</div>
                    <div class="mt-2">
                        <div class="progress" style="height: 6px;">
                            <div class="progress-bar" id="diskProgress" role="progressbar"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="row">
            <div class="col-md-6">
                <div class="chart-container">
                    <h5><i class="bi bi-graph-up"></i> CPU & Memory Trends</h5>
                    <canvas id="performanceChart" height="300"></canvas>
                </div>
            </div>
            <div class="col-md-6">
                <div class="chart-container">
                    <h5><i class="bi bi-hdd-network"></i> Disk & Network I/O</h5>
                    <canvas id="ioChart" height="300"></canvas>
                </div>
            </div>
        </div>

        <!-- Database & Process Info -->
        <div class="row">
            <div class="col-md-6">
                <div class="chart-container">
                    <h5><i class="bi bi-database"></i> Database Status</h5>
                    <div id="databaseInfo">
                        <div class="row">
                            <div class="col-6">
                                <div class="metric-card text-center">
                                    <div class="metric-value" id="dbSize">--</div>
                                    <div class="metric-label">Size (MB)</div>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="metric-card text-center">
                                    <div class="metric-value" id="dbRows">--</div>
                                    <div class="metric-label">Total Rows</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="chart-container">
                    <h5><i class="bi bi-list-ul"></i> Top Processes</h5>
                    <div id="topProcesses" style="max-height: 300px; overflow-y: auto;">
                        <!-- Process list will be populated here -->
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Initialize charts
        const performanceCtx = document.getElementById('performanceChart').getContext('2d');
        const ioCtx = document.getElementById('ioChart').getContext('2d');
        
        const performanceChart = new Chart(performanceCtx, {{
            type: 'line',
            data: {{
                labels: [],
                datasets: [
                    {{
                        label: 'CPU %',
                        data: [],
                        borderColor: '#ff6b6b',
                        backgroundColor: 'rgba(255, 107, 107, 0.1)',
                        tension: 0.4
                    }},
                    {{
                        label: 'Memory %',
                        data: [],
                        borderColor: '#4ecdc4',
                        backgroundColor: 'rgba(78, 205, 196, 0.1)',
                        tension: 0.4
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        labels: {{ color: '#ffffff' }}
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ color: '#ffffff' }},
                        grid: {{ color: 'rgba(255, 255, 255, 0.1)' }}
                    }},
                    y: {{
                        ticks: {{ color: '#ffffff' }},
                        grid: {{ color: 'rgba(255, 255, 255, 0.1)' }}
                    }}
                }}
            }}
        }});
        
        const ioChart = new Chart(ioCtx, {{
            type: 'bar',
            data: {{
                labels: ['Read (MB)', 'Write (MB)', 'Network Sent (MB)', 'Network Recv (MB)'],
                datasets: [{{
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        'rgba(255, 107, 107, 0.8)',
                        'rgba(78, 205, 196, 0.8)',
                        'rgba(255, 193, 7, 0.8)',
                        'rgba(108, 117, 125, 0.8)'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ color: '#ffffff' }},
                        grid: {{ color: 'rgba(255, 255, 255, 0.1)' }}
                    }},
                    y: {{
                        ticks: {{ color: '#ffffff' }},
                        grid: {{ color: 'rgba(255, 255, 255, 0.1)' }}
                    }}
                }}
            }}
        }});
        
        // Update dashboard data
        async function updateDashboard() {{
            try {{
                const response = await fetch('/api/utilities/system-metrics');
                const data = await response.json();
                
                if (data.success) {{
                    const metrics = data.metrics;
                    
                    // Update health score
                    document.getElementById('healthScore').textContent = metrics.health_score || '--';
                    document.getElementById('healthStatus').textContent = metrics.health_status || '--';
                    
                    const healthIndicator = document.getElementById('healthIndicator');
                    healthIndicator.className = 'health-indicator health-' + (metrics.health_color || 'unknown');
                    
                    // Update system metrics
                    document.getElementById('cpuUsage').textContent = metrics.cpu?.usage_percent?.toFixed(1) + '%' || '--';
                    document.getElementById('memoryUsage').textContent = metrics.memory?.percent?.toFixed(1) + '%' || '--';
                    document.getElementById('diskUsage').textContent = metrics.disk?.percent?.toFixed(1) + '%' || '--';
                    
                    // Update progress bars
                    document.getElementById('cpuProgress').style.width = (metrics.cpu?.usage_percent || 0) + '%';
                    document.getElementById('memoryProgress').style.width = (metrics.memory?.percent || 0) + '%';
                    document.getElementById('diskProgress').style.width = (metrics.disk?.percent || 0) + '%';
                    
                    // Update database info
                    document.getElementById('dbSize').textContent = metrics.database?.size_mb || '--';
                    document.getElementById('dbRows').textContent = metrics.database?.total_rows || '--';
                    
                    // Update charts
                    updateCharts(metrics);
                    
                    // Update timestamp
                    document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
                }}
            }} catch (error) {{
                console.error('Failed to update dashboard:', error);
            }}
        }}
        
        function updateCharts(metrics) {{
            const now = new Date().toLocaleTimeString();
            
            // Update performance chart
            if (performanceChart.data.labels.length > 20) {{
                performanceChart.data.labels.shift();
                performanceChart.data.datasets[0].data.shift();
                performanceChart.data.datasets[1].data.shift();
            }}
            
            performanceChart.data.labels.push(now);
            performanceChart.data.datasets[0].data.push(metrics.cpu?.usage_percent || 0);
            performanceChart.data.datasets[1].data.push(metrics.memory?.percent || 0);
            performanceChart.update('none');
            
            // Update I/O chart
            ioChart.data.datasets[0].data = [
                metrics.disk?.read_bytes_mb || 0,
                metrics.disk?.write_bytes_mb || 0,
                metrics.network?.bytes_sent_mb || 0,
                metrics.network?.bytes_recv_mb || 0
            ];
            ioChart.update('none');
        }}
        
        // Update every 2 seconds
        setInterval(updateDashboard, 2000);
        
        // Initial update
        updateDashboard();
    </script>
</body>
</html>
        """
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            # Get system metrics
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            network = psutil.net_io_counters()
            
            # Calculate health score
            cpu_score = max(0, 100 - cpu_percent)
            memory_score = max(0, 100 - memory.percent)
            disk_score = max(0, 100 - (disk.used / disk.total * 100))
            
            overall_score = round((cpu_score * 0.4 + memory_score * 0.4 + disk_score * 0.2), 1)
            
            if overall_score >= 80:
                status = 'Excellent'
                color = 'excellent'
            elif overall_score >= 60:
                status = 'Good'
                color = 'good'
            elif overall_score >= 40:
                status = 'Fair'
                color = 'fair'
            else:
                status = 'Poor'
                color = 'poor'
            
            # Get database info
            db_info = self._get_database_info()
            
            return {
                'success': True,
                'metrics': {
                    'health_score': overall_score,
                    'health_status': status,
                    'health_color': color,
                    'cpu': {
                        'usage_percent': cpu_percent,
                        'count': psutil.cpu_count()
                    },
                    'memory': {
                        'percent': memory.percent,
                        'total_gb': round(memory.total / (1024**3), 2),
                        'available_gb': round(memory.available / (1024**3), 2)
                    },
                    'disk': {
                        'percent': round((disk.used / disk.total) * 100, 2),
                        'total_gb': round(disk.total / (1024**3), 2),
                        'free_gb': round(disk.free / (1024**3), 2),
                        'read_bytes_mb': round(disk_io.read_bytes / (1024**2), 2) if disk_io else 0,
                        'write_bytes_mb': round(disk_io.write_bytes / (1024**2), 2) if disk_io else 0
                    },
                    'network': {
                        'bytes_sent_mb': round(network.bytes_sent / (1024**2), 2),
                        'bytes_recv_mb': round(network.bytes_recv / (1024**2), 2)
                    },
                    'database': db_info
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_database_info(self) -> Dict[str, Any]:
        """Get database information"""
        try:
            db_path = "finance_insights.db"
            if not os.path.exists(db_path):
                return {}
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get table counts
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            total_rows = 0
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    total_rows += count
                except:
                    continue
            
            conn.close()
            
            return {
                'size_mb': round(os.path.getsize(db_path) / (1024 * 1024), 2),
                'total_rows': total_rows,
                'tables': len(tables)
            }
            
        except Exception:
            return {}

# Global instance
dashboard = RealtimeDashboard()

def get_dashboard_html() -> str:
    """Get dashboard HTML"""
    return dashboard.generate_dashboard_html()

def get_dashboard_data() -> Dict[str, Any]:
    """Get dashboard data"""
    return dashboard.get_dashboard_data()
