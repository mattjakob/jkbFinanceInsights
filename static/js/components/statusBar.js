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

export class StatusBar {
    constructor() {
        this.statusBarText = document.querySelector('.status-bar-text');
        this.updateInterval = null;
        
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
        this.updateStatus('System ready');
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
        const now = new Date();
        
        const timeString = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        const dateString = now.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric'
        });
        
        this.statusBarText.textContent = `Last Update: ${timeString} | ${dateString}`;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       UPDATE STATUS                 │
     *  └─────────────────────────────────────┘
     *  Updates status message
     * 
     *  Parameters:
     *  - message: Status message to display
     *  - duration: How long to show the message (ms)
     * 
     *  Returns:
     *  - None
     */
    updateStatus(message, duration = 3000) {
        const originalText = this.statusBarText.textContent;
        
        // Show message
        this.statusBarText.textContent = message;
        
        // Restore time display after duration
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
    }
}
