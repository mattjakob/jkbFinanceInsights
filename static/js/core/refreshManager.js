/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │       REFRESH MANAGER               │
 *  └─────────────────────────────────────┘
 *  Centralized refresh management system
 * 
 *  Consolidates all refresh logic into a single manager
 *  for better control and simplicity.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - RefreshManager instance
 * 
 *  Notes:
 *  - Manages all interval-based updates
 *  - Prevents duplicate intervals
 *  - Provides pause/resume capabilities
 */

import { config } from './config.js';
import { insightsService } from '../services/insights.js';
import { tasksService } from '../services/tasks.js';

class RefreshManager {
    constructor() {
        this.intervals = new Map();
        this.callbacks = new Map();
        this.paused = false;
        this.lastRefresh = new Map();
        
        // Get intervals from global config or use defaults
        this.refreshIntervals = {
            age: window.AppConfig?.frontend_age_refresh_interval || config.refreshIntervals.age,
            table: window.AppConfig?.frontend_table_refresh_interval || config.refreshIntervals.table,
            status: window.AppConfig?.frontend_status_refresh_interval || config.refreshIntervals.status,
            tasks: window.AppConfig?.frontend_task_update_interval || 5000,
            debugger: window.AppConfig?.frontend_debugger_fetch_interval || 5000
        };
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         REGISTER REFRESH            │
     *  └─────────────────────────────────────┘
     *  Registers a refresh callback
     * 
     *  Parameters:
     *  - name: Unique identifier for the refresh
     *  - callback: Function to call on refresh
     *  - interval: Optional custom interval (ms)
     * 
     *  Returns:
     *  - None
     */
    register(name, callback, interval = null) {
        // Stop existing interval if present
        this.stop(name);
        
        // Store callback
        this.callbacks.set(name, callback);
        
        // Use provided interval or default
        const refreshInterval = interval || this.refreshIntervals[name] || 10000;
        
        // Create and store interval
        const intervalId = setInterval(async () => {
            if (!this.paused) {
                try {
                    const result = callback();
                    // Handle both promise and non-promise returns
                    if (result && typeof result.then === 'function') {
                        await result;
                    }
                    this.lastRefresh.set(name, Date.now());
                } catch (error) {
                    console.error(`Refresh error for ${name}:`, error);
                }
            }
        }, refreshInterval);
        
        this.intervals.set(name, { id: intervalId, interval: refreshInterval });
        
        // Run immediately
        if (!this.paused) {
            try {
                const result = callback();
                // Handle both promise and non-promise returns
                if (result && typeof result.then === 'function') {
                    result.then(() => {
                        this.lastRefresh.set(name, Date.now());
                    }).catch(error => {
                        console.error(`Initial refresh error for ${name}:`, error);
                    });
                } else {
                    this.lastRefresh.set(name, Date.now());
                }
            } catch (error) {
                console.error(`Initial refresh error for ${name}:`, error);
            }
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │           STOP REFRESH              │
     *  └─────────────────────────────────────┘
     *  Stops a specific refresh
     * 
     *  Parameters:
     *  - name: Identifier of the refresh to stop
     * 
     *  Returns:
     *  - None
     */
    stop(name) {
        const interval = this.intervals.get(name);
        if (interval) {
            clearInterval(interval.id);
            this.intervals.delete(name);
        }
        this.callbacks.delete(name);
        this.lastRefresh.delete(name);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │           STOP ALL                  │
     *  └─────────────────────────────────────┘
     *  Stops all refresh intervals
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    stopAll() {
        this.intervals.forEach((interval, name) => {
            clearInterval(interval.id);
        });
        this.intervals.clear();
        this.callbacks.clear();
        this.lastRefresh.clear();
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │             PAUSE                   │
     *  └─────────────────────────────────────┘
     *  Pauses all refresh intervals
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    pause() {
        this.paused = true;
        Debugger.info('Refresh manager paused');
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │             RESUME                  │
     *  └─────────────────────────────────────┘
     *  Resumes all refresh intervals
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    resume() {
        this.paused = false;
        Debugger.info('Refresh manager resumed');
        
        // Trigger immediate refresh for all callbacks
        this.callbacks.forEach((callback, name) => {
            callback().then(() => {
                this.lastRefresh.set(name, Date.now());
            }).catch(error => {
                console.error(`Resume refresh error for ${name}:`, error);
            });
        });
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │          TRIGGER REFRESH            │
     *  └─────────────────────────────────────┘
     *  Manually triggers a specific refresh
     * 
     *  Parameters:
     *  - name: Identifier of the refresh to trigger
     * 
     *  Returns:
     *  - Promise
     */
    async trigger(name) {
        const callback = this.callbacks.get(name);
        if (callback) {
            await callback();
            this.lastRefresh.set(name, Date.now());
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │          GET STATUS                 │
     *  └─────────────────────────────────────┘
     *  Gets refresh manager status
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Status object
     */
    getStatus() {
        const status = {
            paused: this.paused,
            active: this.intervals.size,
            intervals: {}
        };
        
        this.intervals.forEach((interval, name) => {
            const lastRefresh = this.lastRefresh.get(name);
            status.intervals[name] = {
                interval: interval.interval,
                lastRefresh: lastRefresh ? new Date(lastRefresh).toLocaleTimeString() : 'Never',
                nextRefresh: lastRefresh ? 
                    new Date(lastRefresh + interval.interval).toLocaleTimeString() : 
                    'Pending'
            };
        });
        
        return status;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      UPDATE INTERVAL                │
     *  └─────────────────────────────────────┘
     *  Updates the interval for a refresh
     * 
     *  Parameters:
     *  - name: Identifier of the refresh
     *  - newInterval: New interval in milliseconds
     * 
     *  Returns:
     *  - None
     */
    updateInterval(name, newInterval) {
        const callback = this.callbacks.get(name);
        if (callback) {
            this.register(name, callback, newInterval);
            Debugger.info(`Updated ${name} refresh interval to ${newInterval}ms`);
        }
    }
}

// Create singleton instance
const refreshManager = new RefreshManager();

// Export default instance
export default refreshManager;

// Also export class for testing
export { RefreshManager };