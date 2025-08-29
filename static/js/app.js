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
            console.log('Starting app initialization...');
            Debugger.info('Initializing JKB Finance Terminal...');
            
            // Initialize components
            console.log('Creating ControlPanel...');
            this.components.controlPanel = new ControlPanel();
            console.log('ControlPanel created successfully');
            
            console.log('Creating InsightsTable...');
            this.components.insightsTable = new InsightsTable();
            console.log('InsightsTable created successfully');
            
            console.log('Creating StatusBar...');
            this.components.statusBar = new StatusBar();
            console.log('StatusBar created successfully');
            
            // Initialize symbol search if input exists
            const symbolInput = document.getElementById('symbolInput');
            const exchangeInput = document.getElementById('exchangeInput');
            console.log('Symbol input element:', symbolInput);
            console.log('Exchange input element:', exchangeInput);
            
            if (symbolInput) {
                console.log('Creating SymbolSearch...');
                this.components.symbolSearch = new SymbolSearch(symbolInput, exchangeInput);
                console.log('SymbolSearch created successfully');
            } else {
                console.log('No symbol input found, skipping SymbolSearch');
            }
            
            // Initialize additional features
            console.log('Initializing reset buttons...');
            this.initializeResetButtons();
            
            console.log('Initializing auto refresh...');
            this.initializeAutoRefresh();
            
            // Load initial data
            console.log('Loading initial data...');
            await this.loadInitialData();
            
            console.log('App initialization completed successfully');
            
        } catch (error) {
            console.error('Error during initialization:', error);
            Debugger.error('Failed to initialize application');
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
                    Debugger.warn('Please enter an insight ID');
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
                Debugger.success(`AI analysis reset for insight #${insightId}`);
                
                // Update the row
                const row = button.closest('tr');
                if (row) {
                    const aiCell = row.querySelector('.ai-analysis-cell');
                    if (aiCell) {
                        aiCell.innerHTML = '<span class="text-muted">Pending</span>';
                    }
                }
            } else {
                Debugger.error(`Failed to reset AI analysis: ${result.message}`);
            }
        } catch (error) {
            Debugger.error('Error resetting AI analysis');
            console.error('Reset error:', error);
        } finally {
            button.textContent = originalText;
            button.disabled = false;
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
            // Extract filters from path
            const pathParts = window.location.pathname.split('/').filter(p => p);
            let exchangeSymbol = '';
            let type = '';
            
            // Check if we're on a filtered route
            if (pathParts[0] === 'api' && pathParts[1] === 'insights') {
                exchangeSymbol = pathParts[2] || '';
                type = pathParts[3] ? pathParts[3].replace(/_/g, ' ') : '';
            }
            
            // Parse exchange-symbol format
            let symbol = '';
            let exchange = '';
            if (exchangeSymbol && exchangeSymbol.includes(':')) {
                const parts = exchangeSymbol.split(':', 2);
                exchange = parts[0];
                symbol = parts[1];
            } else if (exchangeSymbol) {
                symbol = exchangeSymbol;
            }
            
            // Fetch insights
            const insights = await insightsService.fetchInsights(symbol, type);
            
            // Update cache
            insightsService.updateCache(insights);
        } catch (error) {
            console.error('Error loading initial data:', error);
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
        // Check for auto-refresh preference from config
        const autoRefreshEnabled = window.AppConfig?.app_auto_refresh !== false && 
                                 localStorage.getItem('autoRefresh') !== 'false';
        
        if (autoRefreshEnabled) {
            Debugger.info('Auto-refresh enabled, starting refresh interval');
            this.startAutoRefresh();
        } else {
            Debugger.info('Auto-refresh disabled by user preference or configuration');
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
        
        // Use the new simplified config
        const refreshInterval = window.AppConfig?.frontend_table_refresh_interval || config.refreshIntervals.table;
        
        this.refreshInterval = setInterval(async () => {
            try {
                // Refresh data
                await this.refreshData();
            } catch (error) {
                console.error('Auto-refresh error:', error);
            }
        }, refreshInterval);
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
            // Extract filters from path
            const pathParts = window.location.pathname.split('/').filter(p => p);
            let exchangeSymbol = '';
            let type = '';
            
            // Check if we're on a filtered route
            if (pathParts[0] === 'api' && pathParts[1] === 'insights') {
                exchangeSymbol = pathParts[2] || '';
                type = pathParts[3] ? pathParts[3].replace(/_/g, ' ') : '';
            }
            
            // Parse exchange-symbol format
            let symbol = '';
            let exchange = '';
            if (exchangeSymbol && exchangeSymbol.includes(':')) {
                const parts = exchangeSymbol.split(':', 2);
                exchange = parts[0];
                symbol = parts[1];
            } else if (exchangeSymbol) {
                symbol = exchangeSymbol;
            }
            
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
