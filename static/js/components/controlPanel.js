/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         CONTROL PANEL               │
 *  └─────────────────────────────────────┘
 *  Control panel component for user interactions
 * 
 *  Manages all control panel buttons, inputs, and filters
 *  including fetch, update, delete, and filter operations.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - ControlPanel class
 * 
 *  Notes:
 *  - Handles all user input events
 *  - Updates UI state based on operations
 */

import { config } from '../core/config.js';

import { insightsService } from '../services/insights.js';
import { scrapingService } from '../services/scraping.js';
import { analysisService } from '../services/analysis.js';

export class ControlPanel {
    constructor() {
        this.elements = {
            updateBtn: document.querySelector('.update-btn'),
            fetchBtn: document.querySelector('.fetch-btn'),
            deleteBtn: document.querySelector('.delete-btn'),
            generateBtn: document.querySelector('.generate-btn'),
            symbolInput: document.getElementById('symbolInput'),
            exchangeInput: document.getElementById('exchangeInput'),
            typeFilter: document.getElementById('typeFilter'),
            itemsSelect: document.querySelector('select[title="Number of Items"]')
        };
        
        this.initializeEventListeners();
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    INITIALIZE EVENT LISTENERS       │
     *  └─────────────────────────────────────┘
     *  Sets up all event listeners for control panel
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    initializeEventListeners() {
        // Update button
        if (this.elements.updateBtn) {
            this.elements.updateBtn.addEventListener('click', () => this.handleUpdate());
        }
        
        // Fetch button
        if (this.elements.fetchBtn) {
            this.elements.fetchBtn.addEventListener('click', () => this.handleFetch());
        }
        
        // Delete button
        if (this.elements.deleteBtn) {
            this.elements.deleteBtn.addEventListener('click', () => this.handleDelete());
        }
        
        // Generate button
        if (this.elements.generateBtn) {
            this.elements.generateBtn.addEventListener('click', () => this.handleGenerate());
        }
        
        // Type filter
        if (this.elements.typeFilter) {
            this.elements.typeFilter.addEventListener('change', (e) => this.handleTypeFilterChange(e));
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         HANDLE UPDATE               │
     *  └─────────────────────────────────────┘
     *  Handles AI analysis update
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Promise
     */
    async handleUpdate() {
        const btn = this.elements.updateBtn;
        if (!btn || btn.disabled) return;
        
        try {
            // Get current symbol from UI
            const symbol = this.elements.symbolInput?.value.trim().toUpperCase() || '';
            
            if (!symbol) {
                Debugger.error('Symbol is required for analysis. Please enter a symbol first.');
                return;
            }
            
            // Show loading state
            this.setButtonLoading(btn, 'UPDATING...');
            
            // Trigger analysis for current symbol
            const result = await analysisService.triggerAnalysis(symbol);
            
            if (result.success) {
                if (result.symbol) {
                    Debugger.success(
                        `AI analysis started for ${result.symbol}: ${result.insights_found} insights found, ${result.tasks_created} tasks created`
                    );
                } else {
                    Debugger.success(
                        `AI analysis started: ${result.insights_found} insights found, ${result.tasks_created} tasks created`
                    );
                }
                
                // Reload page after delay
                setTimeout(() => window.location.reload(), config.defaults.reloadDelay * 2);
            } else {
                Debugger.error(`AI analysis failed: ${result.message}`);
            }
        } catch (error) {
            Debugger.error('Network error during AI analysis');
            console.error('Update error:', error);
        } finally {
            this.resetButton(btn, 'UPDATE');
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         HANDLE FETCH                │
     *  └─────────────────────────────────────┘
     *  Handles fetching new insights
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Promise
     */
    async handleFetch() {
        const btn = this.elements.fetchBtn;
        if (!btn || btn.disabled) return;
        
        try {
            // Get form values
            const symbol = this.elements.symbolInput?.value.trim().toUpperCase() || '';
            const exchange = this.elements.exchangeInput?.value.trim().toUpperCase() || '';
            const feedType = this.elements.typeFilter?.value || '';
            const maxItems = parseInt(this.elements.itemsSelect?.value) || config.defaults.maxItems;
            
            // Validate required fields
            if (!symbol) {
                Debugger.error('Symbol is required');
                return;
            }
            if (!exchange) {
                Debugger.error('Exchange is required');
                return;
            }
            
            // Show loading state
            this.setButtonLoading(btn, 'FETCHING...');
            
            // Fetch insights
            const result = await scrapingService.fetchInsights({
                symbol,
                exchange,
                feedType,
                maxItems
            });
            
            if (result.success) {
                Debugger.success(
                    `Fetch successful: ${result.created_insights} insights created, ${result.failed_items} failed`
                );
                
                // Reload if insights were created
                if (result.created_insights > 0) {
                    setTimeout(() => window.location.reload(), config.defaults.reloadDelay);
                }
            } else {
                Debugger.error(`Fetch failed: ${result.message}`);
            }
        } catch (error) {
            Debugger.error('Network error during fetch');
            console.error('Fetch error:', error);
        } finally {
            this.resetButton(btn, 'FETCH');
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         HANDLE DELETE               │
     *  └─────────────────────────────────────┘
     *  Handles deleting insights
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Promise
     */
    async handleDelete() {
        const btn = this.elements.deleteBtn;
        if (!btn || btn.disabled) return;
        
        const selectedType = this.elements.typeFilter?.value || 'all';
        const typeText = selectedType === '' ? 'ALL' : selectedType;
        
        if (!confirm(`Are you sure you want to delete ${typeText} insights? This cannot be undone.`)) {
            return;
        }
        
        try {
            // Show loading state
            this.setButtonLoading(btn, 'DELETING...');
            
            // Delete insights
            const result = await insightsService.deleteInsights(selectedType);
            
            if (result.success) {
                Debugger.success(
                    `Delete successful: ${result.deleted_count} insights deleted, ${result.failed_count} failed`
                );
                
                // Reload page
                setTimeout(() => window.location.reload(), config.defaults.reloadDelay);
            } else {
                Debugger.error(`Delete failed: ${result.message}`);
            }
        } catch (error) {
            Debugger.error('Network error during deletion');
            console.error('Delete error:', error);
        } finally {
            this.resetButton(btn, 'DELETE');
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         HANDLE GENERATE             │
     *  └─────────────────────────────────────┘
     *  Handles generating AI megasummary
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Promise
     */
    async handleGenerate() {
        const btn = this.elements.generateBtn;
        if (!btn || btn.disabled) return;
        
        Debugger.info('AI Megasummary generation not yet implemented');
        // TODO: Implement megasummary generation when API is ready
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    HANDLE TYPE FILTER CHANGE        │
     *  └─────────────────────────────────────┘
     *  Handles type filter changes
     * 
     *  Parameters:
     *  - event: Change event
     * 
     *  Returns:
     *  - None
     */
    handleTypeFilterChange(event) {
        const filterValue = event.target.value;
        const symbolInput = document.getElementById('symbolInput');
        const exchangeInput = document.getElementById('exchangeInput');
        const symbol = symbolInput?.value.trim().toUpperCase() || '';
        const exchange = exchangeInput?.value.trim().toUpperCase() || '';
        
        // Build new URL path using EXCHANGE:SYMBOL format
        let newPath = '/';
        if (symbol && exchange) {
            const exchangeSymbol = `${exchange}:${symbol}`;
            newPath = `/api/insights/${exchangeSymbol}`;
            if (filterValue) {
                // Replace spaces with underscores for URL
                const urlSafeType = filterValue.replace(/\s+/g, '_');
                newPath = `/api/insights/${exchangeSymbol}/${urlSafeType}`;
            }
        } else if (symbol) {
            // Fallback to just symbol if no exchange
            newPath = `/api/insights/${symbol}`;
            if (filterValue) {
                // Replace spaces with underscores for URL
                const urlSafeType = filterValue.replace(/\s+/g, '_');
                newPath = `/api/insights/${symbol}/${urlSafeType}`;
            }
        } else if (filterValue) {
            // If no symbol but type is selected, stay on current page
            return;
        }
        
        window.location.href = newPath;
    }



    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      SET BUTTON LOADING             │
     *  └─────────────────────────────────────┘
     *  Sets button to loading state
     * 
     *  Parameters:
     *  - button: Button element
     *  - text: Loading text
     * 
     *  Returns:
     *  - None
     */
    setButtonLoading(button, text) {
        button.innerHTML = `<span class="${config.icons.loading} me-2"></span>${text}`;
        button.disabled = true;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         RESET BUTTON                │
     *  └─────────────────────────────────────┘
     *  Resets button to normal state
     * 
     *  Parameters:
     *  - button: Button element
     *  - text: Button text
     * 
     *  Returns:
     *  - None
     */
    resetButton(button, text) {
        button.innerHTML = text;
        button.disabled = false;
    }
}
