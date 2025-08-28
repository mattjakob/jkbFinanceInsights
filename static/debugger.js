/**
 * 
 * ┌─────────────────────────────────────┐
 * │         FRONTEND DEBUGGER           │
 * └─────────────────────────────────────┘
 * Frontend debugging system for JKB Finance Terminal
 * 
 * Provides centralized debugging functionality to replace console.log
 * statements with a unified system that can be controlled globally.
 * 
 * Parameters:
 * - None
 * 
 * Returns:
 * - None
 * 
 * Notes:
 * - Replaces all console.log, console.error, console.warn statements
 * - Can be globally enabled/disabled
 * - Integrates with server-side debugger system
 */

class FrontendDebugger {
    constructor() {
        this.enabled = true;
        this.logLevel = 'info'; // 'debug', 'info', 'warn', 'error'
        this.maxLogs = 100;
        this.logs = [];
        this.initialize();
    }

    /**
     * Initialize the debugger
     */
    initialize() {
        // Check if debugger should be enabled based on environment
        if (typeof window !== 'undefined') {
            // In production, disable debug logging by default
            this.enabled = window.location.hostname === 'localhost' || 
                           window.location.hostname === '127.0.0.1';
            
            // Allow manual override via URL parameter
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.has('debug')) {
                this.enabled = urlParams.get('debug') === 'true';
            }
        }
    }

    /**
     * Log a debug message
     */
    debug(message, ...args) {
        if (this.enabled && this.shouldLog('debug')) {
            this.log('debug', message, args);
        }
    }

    /**
     * Log an info message
     */
    info(message, ...args) {
        if (this.enabled && this.shouldLog('info')) {
            this.log('info', message, args);
        }
    }

    /**
     * Log a warning message
     */
    warn(message, ...args) {
        if (this.enabled && this.shouldLog('warn')) {
            this.log('warn', message, args);
        }
    }

    /**
     * Log an error message
     */
    error(message, ...args) {
        if (this.enabled && this.shouldLog('error')) {
            this.log('error', message, args);
        }
    }

    /**
     * Log a success message
     */
    success(message, ...args) {
        if (this.enabled && this.shouldLog('info')) {
            this.log('success', message, args);
        }
    }

    /**
     * Check if message should be logged based on log level
     */
    shouldLog(level) {
        const levels = { 'debug': 0, 'info': 1, 'warn': 2, 'error': 3 };
        return levels[level] >= levels[this.logLevel];
    }

    /**
     * Internal logging method
     */
    log(level, message, args) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            level,
            message,
            args: args.length > 0 ? args : undefined
        };

        // Add to logs array
        this.logs.push(logEntry);
        if (this.logs.length > this.maxLogs) {
            this.logs.shift();
        }

        // Output to console with appropriate method
        const consoleMethod = level === 'error' ? 'error' : 
                             level === 'warn' ? 'warn' : 
                             level === 'success' ? 'log' : 'log';
        
        const prefix = `[${level.toUpperCase()}]`;
        if (args && args.length > 0) {
            console[consoleMethod](prefix, message, ...args);
        } else {
            console[consoleMethod](prefix, message);
        }

        // Send to server debugger if available
        this.sendToServer(level, message, args);
    }

    /**
     * Send debug message to server
     */
    async sendToServer(level, message, args) {
        try {
            // Only send important messages to server
            if (level === 'error' || level === 'warn') {
                const response = await fetch('/api/debug-status', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        level,
                        message: args && args.length > 0 ? `${message} ${args.join(' ')}` : message,
                        timestamp: new Date().toISOString()
                    })
                });
            }
        } catch (error) {
            // Silently fail - don't create debug loops
        }
    }

    /**
     * Enable/disable debugger
     */
    setEnabled(enabled) {
        this.enabled = enabled;
        this.info(`Debugger ${enabled ? 'enabled' : 'disabled'}`);
    }

    /**
     * Set log level
     */
    setLogLevel(level) {
        this.logLevel = level;
        this.info(`Log level set to: ${level}`);
    }

    /**
     * Get all logs
     */
    getLogs() {
        return [...this.logs];
    }

    /**
     * Clear logs
     */
    clearLogs() {
        this.logs = [];
        this.info('Logs cleared');
    }

    /**
     * Export logs
     */
    exportLogs() {
        return JSON.stringify(this.logs, null, 2);
    }
}

// Create global debugger instance
window.Debugger = new FrontendDebugger();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FrontendDebugger;
}
