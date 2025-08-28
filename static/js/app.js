/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        JKB FINANCE APP              │
 *  └─────────────────────────────────────┘
 *  Main application entry point
 * 
 *  Initializes all components and manages the application
 *  lifecycle for the JKB Finance Terminal.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - App class
 * 
 *  Notes:
 *  - Coordinates all components
 *  - Manages application state
 */

import { config } from './core/config.js';
import { showNotification } from './core/utils.js';
import { ControlPanel } from './components/controlPanel.js';
import { InsightsTable } from './components/insightsTable.js';
import { StatusBar } from './components/statusBar.js';
import { SymbolSearch } from './components/symbolSearch.js';
import { insightsService } from './services/insights.js';

class App {
    constructor() {
        this.components = {};
        this.refreshInterval = null;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         INITIALIZE                  │
     *  └─────────────────────────────────────┘
     *  Initializes the application
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    async initialize() {
        try {
            Debugger.info('Initializing JKB Finance Terminal...');
            
            // Initialize components
            this.components.controlPanel = new ControlPanel();
            this.components.insightsTable = new InsightsTable();
            this.components.statusBar = new StatusBar();
            
            // Initialize symbol search if input exists
            const symbolInput = document.getElementById('symbolInput');
            if (symbolInput) {
                this.components.symbolSearch = new SymbolSearch(symbolInput);
            }
            
            // Initialize additional features
            this.initializeResetButtons();
            this.initializeAutoRefresh();
            
            // Load initial data
            await this.loadInitialData();
            
            Debugger.success('JKB Finance Terminal initialized successfully');
        } catch (error) {
            console.error('Error during initialization:', error);
            showNotification('Failed to initialize application', 'error');
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      LOAD INITIAL DATA              │
     *  └─────────────────────────────────────┘
     *  Loads initial data from API
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Promise
     */
    async loadInitialData() {
        try {
            // Get URL parameters for filters
            const urlParams = new URLSearchParams(window.location.search);
            const symbol = urlParams.get('symbol') || '';
            const type = urlParams.get('type') || '';
            
            // Fetch insights
            const insights = await insightsService.fetchInsights(symbol, type);
            Debugger.info(`Loaded ${insights.length} insights`);
            
            // Update cache
            insightsService.updateCache(insights);
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }



    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    INITIALIZE RESET BUTTONS         │
     *  └─────────────────────────────────────┘
     *  Initializes AI reset button handlers
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    initializeResetButtons() {
        // Handle individual reset buttons
        document.addEventListener('click', async (e) => {
            if (e.target.classList.contains('reset-ai-btn')) {
                const insightId = e.target.getAttribute('data-id');
                await this.handleResetAI(insightId, e.target);
            }
        });
        
        // Handle bulk reset
        const bulkResetBtn = document.getElementById('resetBtn');
        const resetInput = document.getElementById('resetInsightId');
        
        if (bulkResetBtn && resetInput) {
            bulkResetBtn.addEventListener('click', async () => {
                const insightId = resetInput.value.trim();
                if (!insightId) {
                    showNotification('Please enter an insight ID', 'warning');
                    return;
                }
                
                await this.handleResetAI(insightId, bulkResetBtn);
                resetInput.value = '';
            });
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       HANDLE RESET AI               │
     *  └─────────────────────────────────────┘
     *  Handles AI analysis reset
     * 
     *  Parameters:
     *  - insightId: Insight ID
     *  - button: Button element
     * 
     *  Returns:
     *  - Promise
     */
    async handleResetAI(insightId, button) {
        const originalText = button.textContent;
        
        try {
            // Show loading state
            button.textContent = 'Resetting...';
            button.disabled = true;
            
            // Reset AI analysis
            const result = await insightsService.resetAIAnalysis(insightId);
            
            if (result.success) {
                showNotification(`AI analysis reset for insight #${insightId}`, 'success');
                
                // Update the row
                const row = button.closest('tr');
                if (row) {
                    const aiCell = row.querySelector('.ai-analysis-cell');
                    if (aiCell) {
                        aiCell.innerHTML = '<span class="text-muted">Pending</span>';
                    }
                }
            } else {
                showNotification(`Failed to reset AI analysis: ${result.message}`, 'error');
            }
        } catch (error) {
            showNotification('Error resetting AI analysis', 'error');
            console.error('Reset error:', error);
        } finally {
            button.textContent = originalText;
            button.disabled = false;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    INITIALIZE AUTO REFRESH          │
     *  └─────────────────────────────────────┘
     *  Sets up automatic page refresh
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    initializeAutoRefresh() {
        // Check for auto-refresh preference
        const autoRefreshEnabled = localStorage.getItem('autoRefresh') !== 'false';
        
        if (autoRefreshEnabled) {
            Debugger.info('Auto-refresh enabled, starting refresh interval');
            this.startAutoRefresh();
        } else {
            Debugger.info('Auto-refresh disabled by user preference');
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       START AUTO REFRESH            │
     *  └─────────────────────────────────────┘
     *  Starts automatic refresh interval
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.refreshInterval = setInterval(async () => {
            try {
                // Refresh data
                await this.refreshData();
            } catch (error) {
                console.error('Auto-refresh error:', error);
            }
        }, config.refreshIntervals.autoRefresh);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         REFRESH DATA                │
     *  └─────────────────────────────────────┘
     *  Refreshes application data
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Promise
     */
    async refreshData() {
        try {
            // Get current filters
            const urlParams = new URLSearchParams(window.location.search);
            const symbol = urlParams.get('symbol') || '';
            const type = urlParams.get('type') || '';
            
            // Fetch fresh insights
            const insights = await insightsService.fetchInsights(symbol, type);
            
            // Validate data before updating table
            if (insights && Array.isArray(insights)) {
                // Update table
                if (this.components.insightsTable) {
                    await this.components.insightsTable.updateTableRows(insights);
                }
                
                // Update cache
                insightsService.updateCache(insights);
                
                Debugger.info(`Data refreshed successfully: ${insights.length} insights`);
            } else {
                console.warn('Auto-refresh received invalid data, skipping table update');
            }
        } catch (error) {
            console.error('Error refreshing data:', error);
            // Don't update table on error to preserve existing data
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         STOP AUTO REFRESH           │
     *  └─────────────────────────────────────┘
     *  Stops automatic refresh
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
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │           CLEANUP                   │
     *  └─────────────────────────────────────┘
     *  Cleans up resources
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    cleanup() {
        this.stopAutoRefresh();
        
        // Clean up components
        if (this.components.insightsTable) {
            this.components.insightsTable.stopUpdates();
        }
        
        if (this.components.statusBar) {
            this.components.statusBar.destroy();
        }
    }
}

// Create and export app instance
const app = new App();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => app.initialize());
} else {
    app.initialize();
}

// Clean up on page unload
window.addEventListener('beforeunload', () => app.cleanup());

export default app;
