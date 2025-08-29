/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │       UNIFIED REFRESH MANAGER       │
 *  └─────────────────────────────────────┘
 *  Manages all UI refresh operations with a single interval
 * 
 *  Consolidates refresh operations for status bar, task counters,
 *  age displays, and other UI elements into a single efficient cycle.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - UnifiedRefreshManager singleton instance
 * 
 *  Notes:
 *  - Reduces timer overhead by using single interval
 *  - All UI updates happen synchronously
 *  - Table refresh remains separate due to resource intensity
 */

import refreshManager from './refreshManager.js';
import { tasksService } from '../services/tasks.js';
import { reportsService } from '../services/reports.js';

class UnifiedRefreshManager {
    constructor() {
        this.components = new Set();
        this.isRunning = false;
        this.interval = window.AppConfig?.frontend_unified_refresh_interval || 1000;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       REGISTER COMPONENT            │
     *  └─────────────────────────────────────┘
     *  Registers a component for unified updates
     * 
     *  Parameters:
     *  - component: Component with update methods
     * 
     *  Returns:
     *  - None
     */
    register(component) {
        this.components.add(component);
        
        // Start if not already running
        if (!this.isRunning && this.components.size > 0) {
            this.start();
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      UNREGISTER COMPONENT           │
     *  └─────────────────────────────────────┘
     *  Removes a component from updates
     * 
     *  Parameters:
     *  - component: Component to remove
     * 
     *  Returns:
     *  - None
     */
    unregister(component) {
        this.components.delete(component);
        
        // Stop if no components left
        if (this.components.size === 0) {
            this.stop();
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │          START UPDATES              │
     *  └─────────────────────────────────────┘
     *  Starts the unified refresh cycle
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    start() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        
        // Register single unified update with refresh manager
        refreshManager.register('unified', async () => {
            await this.performUpdates();
        }, this.interval);
        
        // Perform initial update
        this.performUpdates();
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │          STOP UPDATES               │
     *  └─────────────────────────────────────┘
     *  Stops the unified refresh cycle
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    stop() {
        this.isRunning = false;
        refreshManager.stop('unified');
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │        PERFORM UPDATES              │
     *  └─────────────────────────────────────┘
     *  Executes all registered update operations
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Promise
     */
    async performUpdates() {
        // Fetch task stats once for all components
        await tasksService.fetchTaskStats();
        const taskStats = tasksService.getCurrentStats();
        
        // Update each registered component
        for (const component of this.components) {
            try {
                // Update time display
                if (component.updateTime) {
                    component.updateTime();
                }
                
                // Update task counters
                if (component.statusRunning) {
                    component.statusRunning.textContent = taskStats.processing || 0;
                }
                if (component.statusQueued) {
                    component.statusQueued.textContent = taskStats.pending || 0;
                }
                if (component.statusFailed) {
                    component.statusFailed.textContent = taskStats.failed || 0;
                }
                
                // Update age displays
                if (component.updateAllAges) {
                    component.updateAllAges();
                }
                
                // Fetch debugger status
                if (component.fetchDebuggerStatus) {
                    await component.fetchDebuggerStatus();
                }
            } catch (error) {
                console.error('Error updating component:', error);
            }
        }
        
                // Handle REPORT block visibility
        await this.handleReportVisibility();
    }
    
    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      HANDLE REPORT VISIBILITY        │
     *  └─────────────────────────────────────┘
     *  Checks for new reports and toggles report block visibility
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Promise
     */
    async handleReportVisibility() {
        try {
            // Get current symbol from URL or UI
            const currentSymbol = this.getCurrentSymbol();
            
            if (!currentSymbol) {
                // Hide report block if no symbol
                this.toggleReportBlock(false);
                return;
            }
            
            // Check if reports are available for current symbol
            const hasReports = await reportsService.checkReportsAvailable(currentSymbol);
            
            // Toggle report block visibility
            this.toggleReportBlock(hasReports);
            
        } catch (error) {
            console.error('Error handling report visibility:', error);
        }
    }
    
    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │        GET CURRENT SYMBOL            │
     *  └─────────────────────────────────────┘
     *  Gets the current symbol from URL or UI
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Current symbol string or null
     */
    getCurrentSymbol() {
        // Try to get symbol from URL first
        const urlParams = new URLSearchParams(window.location.search);
        const symbolFromUrl = urlParams.get('symbol');
        
        if (symbolFromUrl) {
            return symbolFromUrl.toUpperCase();
        }
        
        // Try to get symbol from UI inputs
        const symbolInput = document.getElementById('symbolInput');
        if (symbolInput && symbolInput.value.trim()) {
            return symbolInput.value.trim().toUpperCase();
        }
        
        return null;
    }
    
    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       TOGGLE REPORT BLOCK            │
     *  └─────────────────────────────────────┘
     *  Shows or hides the report block
     * 
     *  Parameters:
     *  - show: Boolean to show/hide the block
     * 
     *  Returns:
     *  - None
     */
    toggleReportBlock(show) {
        const reportBlock = document.getElementById('reportBlock');
        if (!reportBlock) return;
        
        if (show) {
            reportBlock.classList.remove('d-none');
            
            // Refresh report content when showing
            if (window.reportBlock && window.reportBlock.refresh) {
                window.reportBlock.refresh();
            }
        } else {
            reportBlock.classList.add('d-none');
        }
    }
    
    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         SET INTERVAL                │
     *  └─────────────────────────────────────┘
     *  Updates the refresh interval
     * 
     *  Parameters:
     *  - interval: New interval in milliseconds
     * 
     *  Returns:
     *  - None
     */
    setInterval(interval) {
        this.interval = interval;
        
        // Restart if running
        if (this.isRunning) {
            this.stop();
            this.start();
        }
    }
}

// Export singleton instance
const unifiedRefreshManager = new UnifiedRefreshManager();
export default unifiedRefreshManager;
