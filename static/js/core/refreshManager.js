/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        REFRESH MANAGER              │
 *  └─────────────────────────────────────┘
 *  Centralized refresh management system
 * 
 *  Consolidates all refresh, update, and reload logic into
 *  a single, robust manager for better maintainability.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - RefreshManager singleton instance
 * 
 *  Notes:
 *  - Handles all data refresh operations
 *  - Provides unified error handling
 *  - Manages auto-refresh intervals
 */

import { config } from './config.js';
import { apiService } from './apiService.js';
import { urlManager } from './urlManager.js';

class RefreshManager {
    constructor() {
        this.refreshInterval = null;
        this.isRefreshing = false;
        this.components = new Set();
        this.lastRefresh = null;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      REGISTER COMPONENT             │
     *  └─────────────────────────────────────┘
     *  Register a component for refresh updates
     * 
     *  Parameters:
     *  - component: Component with refresh() method
     * 
     *  Returns:
     *  - None
     */
    registerComponent(component) {
        if (component && typeof component.refresh === 'function') {
            this.components.add(component);
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │     UNREGISTER COMPONENT            │
     *  └─────────────────────────────────────┘
     *  Remove a component from refresh updates
     * 
     *  Parameters:
     *  - component: Component to remove
     * 
     *  Returns:
     *  - None
     */
    unregisterComponent(component) {
        this.components.delete(component);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         REFRESH DATA                │
     *  └─────────────────────────────────────┘
     *  Refresh all registered components
     * 
     *  Parameters:
     *  - options: Refresh options
     * 
     *  Returns:
     *  - Promise<boolean> success status
     */
    async refreshData(options = {}) {
        // Prevent concurrent refreshes
        if (this.isRefreshing) {
            console.info('Refresh already in progress, skipping');
            return false;
        }

        this.isRefreshing = true;

        try {
            // Get current filters
            const filters = urlManager.parseCurrentFilters();
            
            // Fetch fresh data
            const insights = await apiService.fetchInsights(filters);
            
            if (!insights || !Array.isArray(insights)) {
                console.warn('Invalid data received, skipping refresh');
                return false;
            }

            // Update all registered components
            const updatePromises = Array.from(this.components).map(component => {
                return component.refresh(insights).catch(error => {
                    console.error(`Error refreshing component:`, error);
                });
            });

            await Promise.allSettled(updatePromises);
            
            this.lastRefresh = Date.now();
            
            if (window.Debugger?.info) {
                window.Debugger.info(`Refreshed ${this.components.size} components`);
            }
            
            return true;
        } catch (error) {
            console.error('Refresh error:', error);
            
            if (window.Debugger?.error) {
                window.Debugger.error('Failed to refresh data');
            }
            
            return false;
        } finally {
            this.isRefreshing = false;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       START AUTO REFRESH            │
     *  └─────────────────────────────────────┘
     *  Start automatic refresh interval
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    startAutoRefresh() {
        // Check if auto-refresh is enabled
        if (!config.defaults.autoRefresh) {
            console.info('Auto-refresh is disabled');
            return;
        }

        // Clear existing interval
        this.stopAutoRefresh();

        // Get refresh interval
        const interval = config.refreshIntervals.table;

        // Start refresh interval
        this.refreshInterval = setInterval(() => {
            this.refreshData({ auto: true });
        }, interval);

        console.info(`Auto-refresh started (${interval / 1000}s interval)`);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       STOP AUTO REFRESH             │
     *  └─────────────────────────────────────┘
     *  Stop automatic refresh interval
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
            console.info('Auto-refresh stopped');
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      TRIGGER MANUAL REFRESH         │
     *  └─────────────────────────────────────┘
     *  Trigger a manual refresh
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Promise<boolean> success status
     */
    async triggerManualRefresh() {
        console.info('Manual refresh triggered');
        return this.refreshData({ manual: true });
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │        GET REFRESH STATUS           │
     *  └─────────────────────────────────────┘
     *  Get current refresh status
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Object with status information
     */
    getStatus() {
        return {
            isRefreshing: this.isRefreshing,
            autoRefreshEnabled: !!this.refreshInterval,
            componentCount: this.components.size,
            lastRefresh: this.lastRefresh,
            timeSinceLastRefresh: this.lastRefresh ? Date.now() - this.lastRefresh : null
        };
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │            CLEANUP                  │
     *  └─────────────────────────────────────┘
     *  Cleanup resources
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    cleanup() {
        this.stopAutoRefresh();
        this.components.clear();
        this.isRefreshing = false;
        this.lastRefresh = null;
    }
}

// Export singleton instance
export const refreshManager = new RefreshManager();
