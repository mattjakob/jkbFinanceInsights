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
import { refreshManager } from './core/refreshManager.js';
import { apiService } from './core/apiService.js';
import { urlManager } from './core/urlManager.js';

import { ControlPanel } from './components/controlPanel.js';
import { InsightsTable } from './components/insightsTable.js';
import { StatusBar } from './components/statusBar.js';
import { SymbolSearch } from './components/symbolSearch.js';

class App {
    constructor() {
        this.components = {};
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
            const exchangeInput = document.getElementById('exchangeInput');
            if (symbolInput) {
                this.components.symbolSearch = new SymbolSearch(symbolInput, exchangeInput);
            }
            
            // Register refreshable components
            refreshManager.registerComponent(this.components.insightsTable);
            refreshManager.registerComponent(this.components.statusBar);
            
            // Initialize additional features
            this.initializeResetButtons();
            
            // Load initial data and start auto-refresh
            await refreshManager.refreshData();
            
            // Start auto-refresh if enabled
            if (config.defaults.autoRefresh && localStorage.getItem('autoRefresh') !== 'false') {
                refreshManager.startAutoRefresh();
            }
            
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
            
            // Reset AI analysis using API service
            const result = await apiService.makeRequest(`/api/insights/${insightId}/reset-ai`, {
                method: 'POST'
            });
            
            if (result.success) {
                Debugger.success(`AI analysis reset for insight #${insightId}`);
                
                // Refresh data to show updated state
                await refreshManager.refreshData();
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
        // Clean up refresh manager
        refreshManager.cleanup();
        
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
