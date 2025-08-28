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

import { tasksService } from '../services/tasks.js';

export class StatusBar {
    constructor() {
        this.statusBarText = document.querySelector('.status-bar-text');
        this.updateInterval = null;
        this.lastDebuggerMessage = null;
        
        if (this.statusBarText) {
            this.initialize();
        }
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
        this.updateDebuggerStatus('info', 'System ready');
        
        // Start task service updates and fetch initial data
        tasksService.startAutoUpdates(5000);
        tasksService.fetchTaskStats(); // Fetch immediately
        
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
        this.updateInterval = setInterval(() => {
            this.updateTime();
        }, 1000);
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
        // If we have a last debugger message, show it instead of just time
        if (this.lastDebuggerMessage) {
            this.displayDebuggerMessage(this.lastDebuggerMessage);
        } else {
            const now = new Date();
            
            const timeString = now.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            });
            
            const dateString = now.toLocaleDateString('en-US', {
                weekday: 'short',
                month: 'short',
                day: 'numeric'
            });
            
            const taskStats = tasksService.getCurrentStats();
            const running = taskStats.processing || 0;
            const queued = taskStats.pending || 0;
            const failed = taskStats.failed || 0;
            
            const formattedTime = `
                <span style="display: inline-block; width: 70px; text-align: left;">${timeString}</span>
                <span style="display: inline-block; width: 50px; text-align: center; color: var(--text-color); font-size: 12px;"><i class="bi bi-lightning-charge-fill" style="color: var(--text-color);"></i> ${running}</span>
                <span style="display: inline-block; width: 50px; text-align: center; color: var(--text-color); font-size: 12px;"><i class="bi bi-list-ol" style="color: var(--text-color);"></i> ${queued}</span>
                <span style="display: inline-block; width: 50px; text-align: center; color: var(--text-color); font-size: 12px;"><i class="bi bi-heartbreak-fill" style="color: var(--text-color);"></i> ${failed}</span>
                <span style="display: inline-block; width: 15px; text-align: center; color: var(--text-color);"><i class="bi bi-clock" style="color: var(--text-color);"></i></span>
                <span style="display: inline-block; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">Last Update: ${dateString}</span>
            `;
            
            this.statusBarText.innerHTML = formattedTime;
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
        const icon = this.getStatusIcon(messageObj.level);
        const taskStats = tasksService.getCurrentStats();
        
        // Format task counts with fallback to 0
        const running = taskStats.processing || 0;
        const queued = taskStats.pending || 0;
        const failed = taskStats.failed || 0;
        
        const formattedMessage = `
            <span style="display: inline-block; width: 70px; text-align: left;">${messageObj.timestamp}</span>
            <span style="display: inline-block; width: 50px; text-align: center; color: var(--text-color); font-size: 12px;"><i class="bi bi-lightning-charge-fill" style="color: var(--text-color);"></i> ${running}</span>
            <span style="display: inline-block; width: 50px; text-align: center; color: var(--text-color); font-size: 12px;"><i class="bi bi-list-ol" style="color: var(--text-color);"></i> ${queued}</span>
            <span style="display: inline-block; width: 50px; text-align: center; color: var(--text-color); font-size: 12px;"><i class="bi bi-heartbreak-fill" style="color: var(--text-color);"></i> ${failed}</span>
            <span style="display: inline-block; width: 15px; text-align: center; color: var(--text-color);">${icon}</span>
            <span style="display: inline-block; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${messageObj.message}</span>
        `;
        
        this.statusBarText.innerHTML = formattedMessage;
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
    getStatusIcon(level) {
        const iconMap = {
            'debug': '<i class="bi bi-bug" style="color: var(--text-color);"></i>',
            'info': '<i class="bi bi-chevron-right" style="color: var(--text-color);"></i>',
            'warn': '<i class="bi bi-exclamation-triangle" style="color: var(--text-color);"></i>',
            'error': '<i class="bi bi-exclamation-diamond-fill" style="color: var(--text-color);"></i>',
            'success': '<i class="bi bi-check" style="color: var(--text-color);"></i>'
        };
        
        return iconMap[level] || '<i class="bi bi-circle" style="color: var(--text-color);"></i>';
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
        tasksService.stopAutoUpdates();
    }
}
