/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        SIMPLE APP                   │
 *  └─────────────────────────────────────┘
 *  Simplified application logic
 * 
 *  Direct API communication without nested managers and
 *  complex refresh systems.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - Simple application functionality
 * 
 *  Notes:
 *  - Direct API calls
 *  - Simple refresh intervals
 *  - Minimal complexity
 */

class SimpleApp {
    constructor() {
        this.config = window.AppConfig || {};
        this.intervals = [];
        this.init();
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         INITIALIZE                  │
     *  └─────────────────────────────────────┘
     *  Initialize the application
     */
    init() {
        this.setupEventListeners();
        this.startRefreshIntervals();
        this.updateAges();
        this.updateDebugStatus();
        this.updateTaskCounters();
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      SETUP EVENT LISTENERS          │
     *  └─────────────────────────────────────┘
     *  Setup all event listeners
     */
    setupEventListeners() {
        // Symbol search
        const symbolInput = document.getElementById('symbolInput');
        if (symbolInput) {
            symbolInput.addEventListener('input', (e) => {
                this.debounce(this.searchSymbols.bind(this), 300)(e.target.value);
            });
        }
        
        // Hide symbol suggestions when clicking outside
        document.addEventListener('click', (e) => {
            const symbolInput = document.getElementById('symbolInput');
            const suggestions = document.getElementById('symbolSuggestions');
            
            if (suggestions && !symbolInput?.contains(e.target) && !suggestions.contains(e.target)) {
                this.hideSymbolSuggestions();
            }
        });

        // Symbol/Exchange change - navigate to filtered view
        const exchangeInput = document.getElementById('exchangeInput');
        if (symbolInput && exchangeInput) {
            const navigateToSymbol = () => {
                const symbol = symbolInput.value.trim();
                const exchange = exchangeInput.value.trim();
                if (symbol) {
                    const url = exchange ? `/api/insights/${exchange}:${symbol}` : `/api/insights/${symbol}`;
                    window.location.href = url;
                }
            };
            
            // Listen for Enter key press to navigate
            symbolInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    navigateToSymbol();
                }
            });
            
            exchangeInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    navigateToSymbol();
                }
            });
        }

        // Type filter change
        const typeFilter = document.getElementById('typeFilter');
        if (typeFilter) {
            typeFilter.addEventListener('change', (e) => {
                const symbol = symbolInput?.value.trim() || '';
                const exchange = exchangeInput?.value.trim() || '';
                const type = e.target.value;
                
                let url = '/';
                if (symbol) {
                    const exchangeSymbol = exchange ? `${exchange}:${symbol}` : symbol;
                    url = type ? `/api/insights/${exchangeSymbol}/${type.replace(/\s+/g, '_')}` : `/api/insights/${exchangeSymbol}`;
                } else if (type) {
                    // If no symbol but type is selected, navigate to type-filtered home view
                    url = `/?type=${encodeURIComponent(type)}`;
                }
                window.location.href = url;
            });
        }

        // Control panel buttons
        const fetchBtn = document.querySelector('.fetch-btn');
        if (fetchBtn) {
            fetchBtn.addEventListener('click', () => this.handleFetch());
        }

        const analyzeBtn = document.querySelector('.update-btn');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => this.handleAnalyze());
        }

        const generateBtn = document.querySelector('.generate-btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.handleGenerate());
        }

        const deleteBtn = document.querySelector('.delete-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => this.handleDeleteByType());
        }

        // Reset buttons
        document.querySelectorAll('[data-action="reset"]').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const insightId = e.target.dataset.insightId;
                if (insightId) {
                    this.resetInsightAI(insightId);
                }
            });
        });

        // Delete buttons
        document.querySelectorAll('[data-action="delete"]').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const insightId = e.target.dataset.insightId;
                if (insightId && confirm('Are you sure you want to delete this insight?')) {
                    this.deleteInsight(insightId);
                }
            });
        });

        // Scraping form
        const scrapingForm = document.getElementById('scrapingForm');
        if (scrapingForm) {
            scrapingForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleScraping(new FormData(scrapingForm));
            });
        }

        // Table row clicks - navigate to detail page
        this.setupRowClickHandlers();
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    SETUP ROW CLICK HANDLERS         │
     *  └─────────────────────────────────────┘
     *  Setup event handlers for table row clicks
     */
    setupRowClickHandlers() {
        // Add click handlers to insight rows
        document.querySelectorAll('.insight-row').forEach(row => {
            row.addEventListener('click', (e) => {
                // Don't navigate if user clicked on an interactive element
                if (e.target.closest('button, a, .btn, .clickable')) {
                    return;
                }
                
                const insightId = row.dataset.insightId;
                if (insightId) {
                    window.location.href = `/insight/${insightId}`;
                }
            });
            
            // Add cursor pointer to indicate clickable rows
            row.style.cursor = 'pointer';
        });
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    START REFRESH INTERVALS          │
     *  └─────────────────────────────────────┘
     *  Start all refresh intervals
     */
    startRefreshIntervals() {
        // Age updates
        this.intervals.push(setInterval(() => {
            this.updateAges();
        }, this.config.frontend_unified_refresh_interval || 1000));

        // Status updates
        this.intervals.push(setInterval(() => {
            this.updateDebugStatus();
            this.updateTaskCounters();
        }, this.config.frontend_status_refresh_interval || 1000));

        // Table refresh (if auto-refresh is enabled)
        if (this.config.app_auto_refresh) {
            this.intervals.push(setInterval(() => {
                this.refreshTable();
            }, this.config.frontend_table_refresh_interval || 10000));
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         UPDATE AGES                 │
     *  └─────────────────────────────────────┘
     *  Update relative time displays
     */
    updateAges() {
        // Update elements with data-time attribute
        document.querySelectorAll('[data-time]').forEach(element => {
            const timestamp = element.dataset.time;
            if (timestamp) {
                element.textContent = this.timeAgo(new Date(timestamp));
            }
        });
        
        // Update elements with data-time-posted attribute (for insights table)
        document.querySelectorAll('[data-time-posted]').forEach(element => {
            const timestamp = element.dataset.timePosted;
            if (timestamp) {
                element.textContent = this.timeAgo(new Date(timestamp));
            }
        });
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      UPDATE DEBUG STATUS            │
     *  └─────────────────────────────────────┘
     *  Update debug status display
     */
    async updateDebugStatus() {
        try {
            const response = await fetch('/api/debug-status');
            const data = await response.json();
            
            const statusElement = document.getElementById('debugStatus');
            if (statusElement && data.message) {
                statusElement.textContent = data.message;
                statusElement.className = `status ${data.status || 'info'}`;
            }
        } catch (error) {
            console.warn('Failed to update debug status:', error);
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      UPDATE TASK COUNTERS           │
     *  └─────────────────────────────────────┘
     *  Update task counter displays
     */
    async updateTaskCounters() {
        try {
            const response = await fetch('/api/tasks/stats');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            // Handle nested stats structure
            const stats = data.stats || data;


            
            // Update running tasks counter (processing)
            const runningElement = document.querySelector('#statusRunning .task-count');
            if (runningElement) {
                runningElement.textContent = stats.processing || 0;

            }
            
            // Update queued tasks counter (pending)
            const queuedElement = document.querySelector('#statusQueued .task-count');
            if (queuedElement) {
                queuedElement.textContent = stats.pending || 0;

            }
            
            // Update failed tasks counter
            const failedElement = document.querySelector('#statusFailed .task-count');
            if (failedElement) {
                failedElement.textContent = stats.failed || 0;

            }
            
            // Update status time
            const timeElement = document.getElementById('statusTime');
            if (timeElement) {
                const now = new Date();
                timeElement.textContent = now.toLocaleTimeString('en-US', { 
                    hour12: false, 
                    hour: '2-digit', 
                    minute: '2-digit', 
                    second: '2-digit' 
                });
            }
            
        } catch (error) {
            console.warn('Failed to update task counters:', error);
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │        REFRESH TABLE                │
     *  └─────────────────────────────────────┘
     *  Refresh the insights table
     */
    async refreshTable() {
        try {
            const url = new URL(window.location);
            const response = await fetch(url.pathname + url.search);
            if (response.ok) {
                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                
                const newTable = doc.querySelector('#insightsTableBody');
                const currentTable = document.querySelector('#insightsTableBody');
                
                if (newTable && currentTable) {
                    // Simply replace the entire table body content
                    currentTable.innerHTML = newTable.innerHTML;
                    
                    // Re-setup row click handlers for new content
                    this.setupRowClickHandlers();
                    
                    // Update ages for new content
                    this.updateAges();
                }
            }
        } catch (error) {
            console.warn('Failed to refresh table:', error);
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       SEARCH SYMBOLS                │
     *  └─────────────────────────────────────┘
     *  Search for symbols
     */
    async searchSymbols(query) {
        if (!query || query.length < 2) {
            this.hideSymbolSuggestions();
            return;
        }

        try {
            const response = await fetch(`/api/scraping/symbols/search?query=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.suggestions && data.suggestions.length > 0) {
                this.showSymbolSuggestions(data.suggestions);
            } else {
                this.hideSymbolSuggestions();
            }
        } catch (error) {
            console.warn('Symbol search failed:', error);
            this.hideSymbolSuggestions();
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    SHOW SYMBOL SUGGESTIONS          │
     *  └─────────────────────────────────────┘
     *  Display symbol suggestions
     */
    showSymbolSuggestions(suggestions) {
        let dropdown = document.getElementById('symbolSuggestions');
        if (!dropdown) {
            dropdown = document.createElement('div');
            dropdown.id = 'symbolSuggestions';
            dropdown.className = 'autocomplete-dropdown';
            document.getElementById('symbolInput').parentNode.appendChild(dropdown);
        }
        
        dropdown.style.display = 'block';

        dropdown.innerHTML = suggestions.map(suggestion => `
            <div class="autocomplete-item" 
                 data-symbol="${suggestion.symbol}" 
                 data-exchange="${suggestion.exchange}">
                <div class="symbol-content">
                    <div class="symbol-line">
                        <span class="symbol-text">${suggestion.symbol}</span>
                        <span class="exchange-tag">${suggestion.exchange}</span>
                    </div>
                    <span class="company-name">${suggestion.description || ''}</span>
                </div>
            </div>
        `).join('');

        // Add click handlers
        dropdown.querySelectorAll('.autocomplete-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const symbolInput = document.getElementById('symbolInput');
                const exchangeInput = document.getElementById('exchangeInput');
                
                // Set values first
                if (symbolInput) {
                    symbolInput.value = item.dataset.symbol;
                    // Manually trigger change event to ensure any listeners are notified
                    symbolInput.dispatchEvent(new Event('input', { bubbles: true }));
                }
                if (exchangeInput) {
                    exchangeInput.value = item.dataset.exchange;
                    // Manually trigger change event to ensure any listeners are notified
                    exchangeInput.dispatchEvent(new Event('input', { bubbles: true }));
                }
                
                this.hideSymbolSuggestions();
                
                // Update TradingView chart if available
                if (window.TradingViewChart && window.TradingViewChart.updateFromInputs) {
                    window.TradingViewChart.updateFromInputs();
                }
                
                // Navigate to the new URL
                const symbol = item.dataset.symbol;
                const exchange = item.dataset.exchange;
                if (symbol && exchange) {
                    const url = `/api/insights/${exchange}:${symbol}`;
                    window.location.href = url;
                }
            });
        });

        dropdown.style.display = 'block';
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    HIDE SYMBOL SUGGESTIONS          │
     *  └─────────────────────────────────────┘
     *  Hide symbol suggestions
     */
    hideSymbolSuggestions() {
        const dropdown = document.getElementById('symbolSuggestions');
        if (dropdown) {
            dropdown.style.display = 'none';
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       HANDLE SCRAPING               │
     *  └─────────────────────────────────────┘
     *  Handle scraping form submission
     */
    async handleScraping(formData) {
        const submitButton = document.querySelector('#scrapingForm button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Fetching...';
        }

        try {
            const response = await fetch('/api/scraping/fetch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol: formData.get('symbol'),
                    exchange: formData.get('exchange'),
                    feed_type: formData.get('feed_type'),
                    max_items: parseInt(formData.get('max_items')) || 50
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showMessage(`Successfully fetched ${result.created_insights} new insights`, 'success');
                // Refresh table after successful scraping
                setTimeout(() => this.refreshTable(), 1000);
            } else {
                this.showMessage(`Scraping failed: ${result.message}`, 'error');
            }
        } catch (error) {
            this.showMessage(`Scraping failed: ${error.message}`, 'error');
        } finally {
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = 'Fetch Insights';
            }
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       RESET INSIGHT AI              │
     *  └─────────────────────────────────────┘
     *  Reset AI analysis for an insight
     */
    async resetInsightAI(insightId) {
        try {
            const response = await fetch(`/api/insights/${insightId}/reset-ai`, {
                method: 'POST'
            });

            const result = await response.json();
            
            if (result.success) {
                this.showMessage('AI analysis reset successfully', 'success');
                setTimeout(() => this.refreshTable(), 1000);
            } else {
                this.showMessage('Failed to reset AI analysis', 'error');
            }
        } catch (error) {
            this.showMessage(`Reset failed: ${error.message}`, 'error');
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       DELETE INSIGHT                │
     *  └─────────────────────────────────────┘
     *  Delete an insight
     */
    async deleteInsight(insightId) {
        try {
            const response = await fetch(`/api/insights/${insightId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showMessage('Insight deleted successfully', 'success');
                setTimeout(() => this.refreshTable(), 1000);
            } else {
                this.showMessage('Failed to delete insight', 'error');
            }
        } catch (error) {
            this.showMessage(`Delete failed: ${error.message}`, 'error');
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         HANDLE FETCH                │
     *  └─────────────────────────────────────┘
     *  Handle FETCH button click
     */
    async handleFetch() {
        const symbol = document.getElementById('symbolInput')?.value.trim();
        const exchange = document.getElementById('exchangeInput')?.value.trim();
        const feedType = document.getElementById('typeFilter')?.value || 'ALL';
        
        // Get the selected items amount from UI
        const itemsSelect = document.querySelector('[title="Number of Items"]');
        const maxItems = parseInt(itemsSelect?.value) || this.config.appMaxItems || 50;
        
        if (!symbol) {
            this.showMessage('Please enter a symbol', 'warning');
            return;
        }

        try {
            const response = await fetch('/api/scraping/fetch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol: symbol,
                    exchange: exchange || 'NASDAQ',
                    feed_type: feedType === '' ? 'ALL' : feedType,
                    max_items: maxItems
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showMessage(`Successfully fetched ${result.created_insights} new insights`, 'success');
                setTimeout(() => this.refreshTable(), 1000);
            } else {
                this.showMessage(`Fetch failed: ${result.message}`, 'error');
            }
        } catch (error) {
            this.showMessage(`Fetch failed: ${error.message}`, 'error');
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │        HANDLE ANALYZE               │
     *  └─────────────────────────────────────┘
     *  Handle ANALYZE button click
     */
    async handleAnalyze() {
        const symbol = document.getElementById('symbolInput')?.value.trim();
        const feedType = document.getElementById('typeFilter')?.value || '';
        
        try {
            const response = await fetch('/api/analysis/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol: symbol || null,
                    type: feedType || null
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showMessage(`AI analysis task queued (${result.tasks_created} tasks for ${result.insights_found} insights)`, 'success');
            } else {
                this.showMessage(`Analysis failed: ${result.message}`, 'error');
            }
        } catch (error) {
            this.showMessage(`Analysis failed: ${error.message}`, 'error');
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       HANDLE GENERATE               │
     *  └─────────────────────────────────────┘
     *  Handle GENERATE button click
     */
    async handleGenerate() {
        const symbol = document.getElementById('symbolInput')?.value.trim();
        const exchange = document.getElementById('exchangeInput')?.value.trim();
        
        if (!symbol) {
            this.showMessage('Please enter a symbol for report generation', 'warning');
            return;
        }

        const generateBlock = document.getElementById('generateBlock');
        const generateContent = document.getElementById('generateContent');
        
        if (generateBlock) {
            generateBlock.classList.remove('d-none');
            generateContent.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border terminal-spinner" role="status">
                        <span class="visually-hidden">Generating...</span>
                    </div>
                    <p class="mt-1 mb-1">Generating AI analysis...</p>
                </div>
            `;
        }

        try {
            const response = await fetch('/api/analysis/generate-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol: symbol,
                    exchange: exchange || 'NASDAQ'
                })
            });

            const result = await response.json();
            
            if (result.success) {
                // Show success message and task info
                this.showMessage(`AI report generation task created for ${result.symbol} (${result.insights_count} insights)`, 'success');
                
                // Try to get the latest report after a short delay
                setTimeout(async () => {
                    try {
                        const reportResponse = await fetch(`/api/reports/symbol/${result.symbol}/latest`);
                        const reportData = await reportResponse.json();
                        
                        if (reportData && generateContent) {
                            generateContent.innerHTML = `
                                <div class="report-content">
                                    <h6>AI Analysis Report for ${result.symbol}</h6>
                                    <div class="mb-2">
                                        <strong>Action:</strong> <span class="badge bg-secondary">${reportData.AIAction}</span>
                                        <strong class="ms-3">Confidence:</strong> ${(reportData.AIConfidence * 100).toFixed(1)}%
                                    </div>
                                    <div class="mb-2">
                                        <strong>Summary:</strong>
                                    </div>
                                    <pre class="bg-dark p-3 rounded">${reportData.AISummary}</pre>
                                    ${reportData.AILevels ? `<div class="mt-2"><strong>Levels:</strong> ${reportData.AILevels}</div>` : ''}
                                    ${reportData.AIEventTime ? `<div class="mt-2"><strong>Event Time:</strong> ${reportData.AIEventTime}</div>` : ''}
                                </div>
                            `;
                        }
                    } catch (error) {
                        console.log('Could not fetch latest report yet, it may still be generating');
                    }
                }, 5000); // Wait 5 seconds for the task to complete
                
                if (generateBlock) {
                    generateBlock.classList.remove('d-none');
                    generateContent.innerHTML = `
                        <div class="text-center">
                            <div class="spinner-border terminal-spinner" role="status">
                                <span class="visually-hidden">Processing...</span>
                            </div>
                            <p class="mt-1 mb-1">Report generation in progress...</p>
                            <small class="text-muted">Report will appear here when ready</small>
                        </div>
                    `;
                }
            } else {
                this.showMessage(`Report generation failed: ${result.message || result.error || 'Unknown error'}`, 'error');
                if (generateBlock) {
                    generateBlock.classList.add('d-none');
                }
            }
        } catch (error) {
            this.showMessage(`Generate failed: ${error.message}`, 'error');
            if (generateBlock) {
                generateBlock.classList.add('d-none');
            }
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │     HANDLE DELETE BY TYPE           │
     *  └─────────────────────────────────────┘
     *  Handle DELETE button click for type deletion
     */
    async handleDeleteByType() {
        const feedType = document.getElementById('typeFilter')?.value || '';
        const typeName = feedType || 'ALL';
        
        if (!confirm(`Are you sure you want to delete all ${typeName} insights?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/insights?type=${encodeURIComponent(feedType)}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            
            if (result.success) {
                this.showMessage(`Deleted ${result.deleted_count} insights`, 'success');
                setTimeout(() => this.refreshTable(), 1000);
            } else {
                this.showMessage(`Delete failed: ${result.message || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            this.showMessage(`Delete failed: ${error.message}`, 'error');
        }
    }



    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │        SHOW MESSAGE                 │
     *  └─────────────────────────────────────┘
     *  Show a temporary message
     */
    showMessage(message, type = 'info') {
        const messageArea = document.getElementById('messageArea');
        const messageText = document.getElementById('messageText');
        
        if (messageArea && messageText) {
            // Map our types to Bootstrap alert classes
            const typeMap = {
                'info': 'alert-info',
                'success': 'alert-success',
                'warning': 'alert-warning',
                'error': 'alert-danger'
            };
            
            // Remove all alert type classes
            messageArea.classList.remove('alert-info', 'alert-success', 'alert-warning', 'alert-danger');
            
            // Add the appropriate class
            messageArea.classList.add(typeMap[type] || 'alert-info');
            
            // Set message text
            messageText.textContent = message;
            
            // Show the message
            messageArea.classList.remove('d-none');
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                messageArea.classList.add('d-none');
            }, 5000);
        } else {
            // Fallback to console log
            console.log(`[${type.toUpperCase()}]`, message);
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         TIME AGO                    │
     *  └─────────────────────────────────────┘
     *  Calculate relative time string
     */
    timeAgo(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) {
            return `${diffInSeconds}s ago`;
        } else if (diffInSeconds < 3600) {
            return `${Math.floor(diffInSeconds / 60)}m ago`;
        } else if (diffInSeconds < 86400) {
            return `${Math.floor(diffInSeconds / 3600)}h ago`;
        } else {
            return `${Math.floor(diffInSeconds / 86400)}d ago`;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         DEBOUNCE                    │
     *  └─────────────────────────────────────┘
     *  Debounce function calls
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         DESTROY                     │
     *  └─────────────────────────────────────┘
     *  Clean up intervals and event listeners
     */
    destroy() {
        this.intervals.forEach(interval => clearInterval(interval));
        this.intervals = [];
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.simpleApp = new SimpleApp();
});

// Make available globally for debugging
window.SimpleApp = SimpleApp;
