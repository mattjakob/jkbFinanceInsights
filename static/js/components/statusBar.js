/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │          STATUS BAR                 │
 *  └─────────────────────────────────────┘
 *  Status bar component for system updates
 * 
 *  Manages the status bar display showing last update time,
 *  system status, and other real-time information.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - StatusBar class
 * 
 *  Notes:
 *  - Updates time every second
 *  - Shows system status and messages
 */

import { apiService } from '../core/apiService.js';
import { config } from '../core/config.js';

export class StatusBar {
    constructor() {
        this.statusTime = document.getElementById('statusTime');
        this.statusRunning = document.querySelector('#statusRunning .task-count');
        this.statusQueued = document.querySelector('#statusQueued .task-count');
        this.statusFailed = document.querySelector('#statusFailed .task-count');
        this.statusIcon = document.querySelector('#statusIcon i');
        this.statusMessage = document.getElementById('statusMessage');
        this.updateInterval = null;
        this.debuggerFetchInterval = null;
        this.lastDebuggerMessage = null;
        
        if (this.statusTime && this.statusMessage) {
            this.initialize();
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │            REFRESH                  │
     *  └─────────────────────────────────────┘
     *  Refresh status bar (for RefreshManager)
     * 
     *  Parameters:
     *  - data: Refresh data (optional)
     * 
     *  Returns:
     *  - Promise
     */
    async refresh(data) {
        // Update task status
        await this.updateTaskStatus();
        return Promise.resolve();
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         INITIALIZE                  │
     *  └─────────────────────────────────────┘
     *  Initializes the status bar
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    initialize() {
        this.startTimeUpdates();
        this.startDebuggerUpdates();
        this.startTaskUpdates();
        
        // Make this instance globally available for debugger integration
        window.statusBar = this;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      START TIME UPDATES             │
     *  └─────────────────────────────────────┘
     *  Starts automatic time updates
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    startTimeUpdates() {
        // Initial update
        this.updateTime();
        
        // Update every second
        const updateInterval = config.refreshIntervals.status;
        this.updateInterval = setInterval(() => {
            this.updateTime();
        }, updateInterval);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       START TASK UPDATES            │
     *  └─────────────────────────────────────┘
     *  Starts automatic task status updates
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    startTaskUpdates() {
        // Initial update
        this.updateTaskStatus();
        
        // Update periodically
        const interval = config.refreshIntervals.status * 2; // Less frequent than time
        this.taskUpdateInterval = setInterval(() => {
            this.updateTaskStatus();
        }, interval);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       UPDATE TASK STATUS            │
     *  └─────────────────────────────────────┘
     *  Updates task status counts
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Promise
     */
    async updateTaskStatus() {
        try {
            const stats = await apiService.getTaskStatus();
            
            if (stats && stats.stats) {
                // Update counts
                if (this.statusRunning) {
                    this.statusRunning.textContent = stats.stats.running || 0;
                }
                if (this.statusQueued) {
                    this.statusQueued.textContent = stats.stats.pending || 0;
                }
                if (this.statusFailed) {
                    this.statusFailed.textContent = stats.stats.failed || 0;
                }
                
                // Update icon based on status
                this.updateStatusIcon(stats.stats);
            }
        } catch (error) {
            console.error('Error updating task status:', error);
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       UPDATE STATUS ICON            │
     *  └─────────────────────────────────────┘
     *  Updates status icon based on task stats
     * 
     *  Parameters:
     *  - stats: Task statistics
     * 
     *  Returns:
     *  - None
     */
    updateStatusIcon(stats) {
        if (!this.statusIcon) return;
        
        // Remove all status classes
        this.statusIcon.className = 'bi';
        
        if (stats.running > 0) {
            // Active processing
            this.statusIcon.classList.add('bi-lightning-charge-fill', 'text-warning');
        } else if (stats.pending > 0) {
            // Tasks waiting
            this.statusIcon.classList.add('bi-hourglass-split', 'text-info');
        } else if (stats.failed > 0) {
            // Has failures
            this.statusIcon.classList.add('bi-exclamation-triangle-fill', 'text-danger');
        } else {
            // All clear
            this.statusIcon.classList.add('bi-check-circle-fill', 'text-success');
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         UPDATE TIME                 │
     *  └─────────────────────────────────────┘
     *  Updates the time display
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    updateTime() {
        // Update timestamp
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        this.statusTime.textContent = timeString;
        
        // Update task counts
        const taskStats = tasksService.getCurrentStats();
        this.statusRunning.textContent = taskStats.processing || 0;
        this.statusQueued.textContent = taskStats.pending || 0;
        this.statusFailed.textContent = taskStats.failed || 0;
        
        // Update message/icon based on debugger status
        if (this.lastDebuggerMessage) {
            this.displayDebuggerMessage(this.lastDebuggerMessage);
        } else {
            // Show default status
            this.statusIcon.className = 'bi bi-clock';
            const dateString = now.toLocaleDateString('en-US', {
                weekday: 'short',
                month: 'short',
                day: 'numeric'
            });
            this.statusMessage.textContent = `Last Update: ${dateString}`;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      START DEBUGGER UPDATES         │
     *  └─────────────────────────────────────┘
     *  Starts automatic debugger status updates
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    startDebuggerUpdates() {
        // Initial fetch
        this.fetchDebuggerStatus();
        
        // Update every 2 seconds
        const debuggerInterval = window.AppConfig?.frontend_debugger_fetch_interval || 5000;
        this.debuggerFetchInterval = setInterval(() => {
            this.fetchDebuggerStatus();
        }, debuggerInterval);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      FETCH DEBUGGER STATUS          │
     *  └─────────────────────────────────────┘
     *  Fetches current debugger status from API
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    async fetchDebuggerStatus() {
        try {
            const response = await fetch('/api/debug-status');
            if (response.ok) {
                const debugStatus = await response.json();
                
                // Only update if we have a valid message and it's different from current
                if (debugStatus.message && debugStatus.message.trim()) {
                    const newMessage = {
                        level: debugStatus.status || 'info',
                        message: debugStatus.message,
                        timestamp: this.formatTimestamp(debugStatus.timestamp)
                    };
                    
                    // Update if message is different or if we don't have a current message
                    if (!this.lastDebuggerMessage || 
                        this.lastDebuggerMessage.message !== newMessage.message ||
                        this.lastDebuggerMessage.timestamp !== newMessage.timestamp) {
                        this.lastDebuggerMessage = newMessage;
                    }
                }
            }
        } catch (error) {
            // Silently fail - don't spam console with fetch errors
            // The status bar will continue showing time if debugger fetch fails
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      FORMAT TIMESTAMP               │
     *  └─────────────────────────────────────┘
     *  Formats timestamp from API response
     * 
     *  Parameters:
     *  - timestamp: Timestamp from API (could be string or Date)
     * 
     *  Returns:
     *  - Formatted time string
     */
    formatTimestamp(timestamp) {
        if (!timestamp) return new Date().toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        
        try {
            const date = new Date(timestamp);
            return date.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            });
        } catch (e) {
            return new Date().toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            });
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    UPDATE DEBUGGER STATUS           │
     *  └─────────────────────────────────────┘
     *  Updates status with debugger message format
     * 
     *  Parameters:
     *  - level: Debug level (debug, info, warn, error, success)
     *  - message: Message to display
     * 
     *  Returns:
     *  - None
     */
    updateDebuggerStatus(level, message) {
        const timestamp = new Date();
        const timeString = timestamp.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        
        this.lastDebuggerMessage = {
            level,
            message,
            timestamp: timeString
        };
        
        this.displayDebuggerMessage(this.lastDebuggerMessage);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    DISPLAY DEBUGGER MESSAGE         │
     *  └─────────────────────────────────────┘
     *  Displays debugger message with proper format
     * 
     *  Parameters:
     *  - messageObj: Object with level, message, timestamp
     * 
     *  Returns:
     *  - None
     */
    displayDebuggerMessage(messageObj) {
        // Update timestamp
        this.statusTime.textContent = messageObj.timestamp;
        
        // Update task counts (already updated in updateTime)
        const taskStats = tasksService.getCurrentStats();
        this.statusRunning.textContent = taskStats.processing || 0;
        this.statusQueued.textContent = taskStats.pending || 0;
        this.statusFailed.textContent = taskStats.failed || 0;
        
        // Update status icon
        const iconClass = this.getStatusIconClass(messageObj.level);
        this.statusIcon.className = iconClass;
        
        // Update message
        this.statusMessage.textContent = messageObj.message;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │        GET STATUS ICON              │
     *  └─────────────────────────────────────┘
     *  Gets Bootstrap icon for status level
     * 
     *  Parameters:
     *  - level: Debug level
     * 
     *  Returns:
     *  - HTML string with Bootstrap icon
     */
    getStatusIconClass(level) {
        const iconMap = {
            'debug': 'bi bi-bug',
            'info': 'bi bi-chevron-right',
            'warn': 'bi bi-exclamation-triangle',
            'error': 'bi bi-exclamation-diamond-fill',
            'success': 'bi bi-check'
        };
        
        return iconMap[level] || 'bi bi-circle';
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       UPDATE STATUS                 │
     *  └─────────────────────────────────────┘
     *  Updates status message (legacy method)
     * 
     *  Parameters:
     *  - message: Status message to display
     *  - duration: How long to show the message (ms)
     * 
     *  Returns:
     *  - None
     */
    updateStatus(message, duration = 3000) {
        // Convert to debugger format
        this.updateDebuggerStatus('info', message);
        
        // Restore time display after duration if needed
        if (duration > 0) {
            setTimeout(() => {
                this.updateTime();
            }, duration);
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      SHOW ACTIVITY                  │
     *  └─────────────────────────────────────┘
     *  Shows activity indicator
     * 
     *  Parameters:
     *  - activity: Activity description
     * 
     *  Returns:
     *  - None
     */
    showActivity(activity) {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        this.statusBarText.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${activity} - ${timeString}`;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      CLEAR ACTIVITY                 │
     *  └─────────────────────────────────────┘
     *  Clears activity indicator
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    clearActivity() {
        this.updateTime();
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         STOP UPDATES                │
     *  └─────────────────────────────────────┘
     *  Stops automatic updates
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    stopUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        if (this.debuggerFetchInterval) {
            clearInterval(this.debuggerFetchInterval);
            this.debuggerFetchInterval = null;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │           DESTROY                   │
     *  └─────────────────────────────────────┘
     *  Cleans up the component
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    destroy() {
        this.stopUpdates();
        if (this.taskUpdateInterval) {
            clearInterval(this.taskUpdateInterval);
        }
    }
}
