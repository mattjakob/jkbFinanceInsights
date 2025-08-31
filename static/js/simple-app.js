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
            const statusDropdown = document.getElementById('statusDropdown');
            const statusToggle = document.getElementById('statusDropdownToggle');
            
            if (suggestions && !symbolInput?.contains(e.target) && !suggestions.contains(e.target)) {
                this.hideSymbolSuggestions();
            }
            
            // Hide status dropdown when clicking outside
            if (statusDropdown && !statusDropdown.contains(e.target) && !statusToggle?.contains(e.target)) {
                statusDropdown.classList.remove('show');
            }
        });

        // Symbol/Exchange change - navigate to filtered view
        const exchangeInput = document.getElementById('exchangeInput');
        if (symbolInput && exchangeInput) {
            const navigateToSymbol = () => {
                const symbol = symbolInput.value.trim();
                const exchange = exchangeInput.value.trim();
                if (symbol) {
                    // Navigate to web interface with symbol parameter, not API endpoint
                    const url = exchange ? `/?symbol=${exchange}:${symbol}` : `/?symbol=${symbol}`;
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
                    // Use query parameters for filtering instead of API path
                    url = type ? `/?symbol=${exchangeSymbol}&type=${encodeURIComponent(type)}` : `/?symbol=${exchangeSymbol}`;
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

        // Status dropdown toggle
        const statusDropdownToggle = document.getElementById('statusDropdownToggle');
        if (statusDropdownToggle) {
            statusDropdownToggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleStatusDropdown();
            });
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
        }, this.config.UI_REFRESH || 1000));

        // Status updates (debug messages only)
        this.intervals.push(setInterval(() => {
            this.updateDebugStatus();
        }, this.config.frontend_status_refresh_interval || 1000));

        // Table refresh (if auto-refresh is enabled)
        if (this.config.app_auto_refresh) {
            this.intervals.push(setInterval(() => {
                this.refreshTable();
            }, this.config.UI_REFRESH_TABLE || 10000));
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         UPDATE AGES                 │
     *  └─────────────────────────────────────┘
     *  Update relative time displays and horizons
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
        
        // Update horizon elements with data-horizon attribute
        document.querySelectorAll('[data-horizon]').forEach(element => {
            const timestamp = element.dataset.horizon;
            if (timestamp) {
                const horizonDisplay = element.querySelector('.horizon-display');
                if (horizonDisplay) {
                    horizonDisplay.textContent = this.timeHorizon(new Date(timestamp));
                }
            }
        });
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      UPDATE DEBUG STATUS            │
     *  └─────────────────────────────────────┘
     *  Update debug status display in status bar
     */
    async updateDebugStatus() {
        try {
            const response = await fetch('/api/debugger');
            
            // Check if response is ok
            if (!response.ok) {
                console.warn(`Debug status API returned ${response.status}: ${response.statusText}`);
                return; // Don't update anything if API fails
            }
            
            const data = await response.json();
            
            const statusMessageElement = document.getElementById('statusMessage');
            const statusIconElement = document.getElementById('statusIcon');
            
            if (statusMessageElement) {
                // Find the most recent message from either current or history
                let messageToShow = '';
                let statusToShow = 'info';
                
                // First try current message
                if (data.message && data.message.trim()) {
                    messageToShow = data.message;
                    statusToShow = data.status;
                }
                // If no current message, get the latest from history
                else if (data.history && data.history.length > 0) {
                    // Find the most recent non-empty message in history
                    for (let i = data.history.length - 1; i >= 0; i--) {
                        if (data.history[i].message && data.history[i].message.trim()) {
                            messageToShow = data.history[i].message;
                            statusToShow = data.history[i].status;
                            break;
                        }
                    }
                }
                
                // Always update the status message if we found one
                if (messageToShow && messageToShow.trim()) {
                    statusMessageElement.textContent = messageToShow.toUpperCase();
                    
                    // Update icon based on status
                    if (statusIconElement) {
                        const iconClass = this.getStatusIcon(statusToShow);
                        statusIconElement.innerHTML = `<i class="${iconClass}"></i>`;
                    }
                }
                
                // Update dropdown with recent messages
                this.updateStatusDropdown(data.history || []);
            }
        } catch (error) {
            console.warn('Failed to update debug status:', error);
            // Don't clear existing messages on API failure
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    UPDATE STATUS DROPDOWN           │
     *  └─────────────────────────────────────┘
     *  Update the status dropdown with recent messages
     */
    updateStatusDropdown(history) {
        const dropdownContent = document.getElementById('statusDropdownContent');
        const dropdownToggle = document.getElementById('statusDropdownToggle');
        
        if (!dropdownContent) return;
        
        if (!history || history.length === 0) {
            dropdownContent.innerHTML = '<div class="status-dropdown-item">No recent messages</div>';
            if (dropdownToggle) dropdownToggle.style.opacity = '0.3';
            return;
        }
        
        // Show dropdown toggle when we have messages
        if (dropdownToggle) dropdownToggle.style.opacity = '0.7';
        
        // Show last 10 messages, most recent first
        const recentMessages = history.slice(-10).reverse();
        
        dropdownContent.innerHTML = recentMessages.map(msg => `
            <div class="status-dropdown-item">
                <span class="message-status ${msg.status}">${msg.status}</span>
                <span class="message-text">${msg.message}</span>
            </div>
        `).join('');
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    TOGGLE STATUS DROPDOWN           │
     *  └─────────────────────────────────────┘
     *  Toggle the status messages dropdown
     */
    toggleStatusDropdown() {
        const dropdown = document.getElementById('statusDropdown');
        if (dropdown) {
            dropdown.classList.toggle('show');
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      SETUP STATUS DROPDOWN          │
     *  └─────────────────────────────────────┘
     *  Setup status dropdown event handlers
     */
    setupStatusDropdown() {
        const statusDropdownToggle = document.getElementById('statusDropdownToggle');
        if (statusDropdownToggle) {
            // Remove any existing listener
            const newToggle = statusDropdownToggle.cloneNode(true);
            statusDropdownToggle.parentNode.replaceChild(newToggle, statusDropdownToggle);
            
            // Add new listener
            newToggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleStatusDropdown();
            });
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      GET STATUS ICON                │
     *  └─────────────────────────────────────┘
     *  Get appropriate icon for status type
     */
    getStatusIcon(status) {
        switch (status) {
            case 'success':
                return 'bi bi-check-lg';
            case 'error':
                return 'bi bi-x-circle';
            case 'warning':
                return 'bi bi-exclamation-triangle';
            default:
                return 'bi bi-chevron-right';
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      SEND DEBUG MESSAGE             │
     *  └─────────────────────────────────────┘
     *  Send message to centralized debugger
     */
    async sendDebugMessage(message, status = 'info') {
        try {
            // Send to server debugger (for console logging)
            await fetch('/api/debug-message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    status: status
                })
            });
            
            // Update local status display immediately
            this.updateDebugStatus();
        } catch (error) {
            console.warn('Failed to send debug message:', error);
            // Fallback to console log
            console.log(`[${status.toUpperCase()}]`, message);
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      UPDATE TASK COUNTERS           │
     *  └─────────────────────────────────────┘
     *  Update task counter displays
     *  
     *  DEPRECATED: Using server-side rendering for status bar
     */
    async updateTaskCounters() {
        // Task counters are now rendered server-side
        // This method is kept for compatibility but does nothing
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
                
                // Update table content
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
                
                // Update status bar content (server-side rendered)
                const newStatusBar = doc.querySelector('#statusBarContent');
                const currentStatusBar = document.querySelector('#statusBarContent');
                
                if (newStatusBar && currentStatusBar) {
                    // Preserve dropdown state AND status message
                    const dropdownOpen = currentStatusBar.querySelector('#statusDropdown')?.classList.contains('show');
                    const dropdownContent = currentStatusBar.querySelector('#statusDropdownContent')?.innerHTML;
                    const currentMessage = currentStatusBar.querySelector('#statusMessage')?.textContent;
                    const currentIcon = currentStatusBar.querySelector('#statusIcon')?.innerHTML;
                    
                    // Update status bar content
                    currentStatusBar.innerHTML = newStatusBar.innerHTML;
                    
                    // Restore dropdown state
                    if (dropdownOpen) {
                        currentStatusBar.querySelector('#statusDropdown')?.classList.add('show');
                    }
                    if (dropdownContent) {
                        const dropdown = currentStatusBar.querySelector('#statusDropdownContent');
                        if (dropdown) dropdown.innerHTML = dropdownContent;
                    }
                    
                    // Restore status message and icon if they existed
                    if (currentMessage && currentMessage.trim()) {
                        const statusMessageEl = currentStatusBar.querySelector('#statusMessage');
                        if (statusMessageEl) {
                            statusMessageEl.textContent = currentMessage;
                        }
                    }
                    if (currentIcon && currentIcon.trim()) {
                        const statusIconEl = currentStatusBar.querySelector('#statusIcon');
                        if (statusIconEl) {
                            statusIconEl.innerHTML = currentIcon;
                        }
                    }
                    
                    // Re-setup dropdown handler
                    this.setupStatusDropdown();
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
                <div class="symbol-info">
                    <span class="symbol-text">${suggestion.symbol}</span>
                    <span class="company-name">${suggestion.description || ''}</span>
                </div>
                <span class="exchange-tag">${suggestion.exchange}</span>
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
                    // Navigate to web interface with query parameters
                    const url = `/?symbol=${exchange}:${symbol}`;
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
                // Handle task-based response
                if (result.task_id || result.tasks_created) {
                    const taskCount = result.tasks_created || 1;
                    this.sendDebugMessage(`Created ${taskCount} scraping task(s)`, 'success');
                } else {
                    this.sendDebugMessage('Scraping task created successfully', 'success');
                }
                // Refresh table after a delay to allow task processing
                setTimeout(() => this.refreshTable(), this.config.app_reload_delay || this.config.UI_REFRESH);
            } else {
                this.sendDebugMessage(`Scraping failed: ${result.message}`, 'error');
            }
        } catch (error) {
            this.sendDebugMessage(`Scraping failed: ${error.message}`, 'error');
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
            const response = await fetch(`/api/insights/id/${insightId}/reset-ai`, {
                method: 'POST'
            });

            const result = await response.json();
            
            if (result.success) {
                this.sendDebugMessage('AI analysis reset successfully', 'success');
                setTimeout(() => this.refreshTable(), this.config.UI_REFRESH || 1000);
            } else {
                this.sendDebugMessage('Failed to reset AI analysis', 'error');
            }
        } catch (error) {
            this.sendDebugMessage(`Reset failed: ${error.message}`, 'error');
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
            const response = await fetch(`/api/insights/id/${insightId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.sendDebugMessage('Insight deleted successfully', 'success');
                setTimeout(() => this.refreshTable(), this.config.UI_REFRESH || 1000);
            } else {
                this.sendDebugMessage('Failed to delete insight', 'error');
            }
        } catch (error) {
            this.sendDebugMessage(`Delete failed: ${error.message}`, 'error');
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
            this.sendDebugMessage('Please enter a symbol', 'warning');
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
                // Handle task-based response
                if (result.task_id || result.tasks_created) {
                    const taskCount = result.tasks_created || 1;
                    this.sendDebugMessage(`Processing ${taskCount} scraping task(s)`, 'info');
                } else {
                    this.sendDebugMessage('Processing scraping task(s)', 'info');
                }
                setTimeout(() => this.refreshTable(), this.config.app_reload_delay || this.config.UI_REFRESH);
            } else {
                this.sendDebugMessage(`Fetch failed: ${result.message}`, 'error');
            }
        } catch (error) {
            this.sendDebugMessage(`Fetch failed: ${error.message}`, 'error');
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
                this.sendDebugMessage(`AI analysis task queued (${result.tasks_created} tasks for ${result.insights_found} insights)`, 'success');
            } else {
                this.sendDebugMessage(`Analysis failed: ${result.message}`, 'error');
            }
        } catch (error) {
            this.sendDebugMessage(`Analysis failed: ${error.message}`, 'error');
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
            this.sendDebugMessage('Please enter a symbol for report generation', 'warning');
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
                this.sendDebugMessage(`AI report generation task created for ${result.symbol} (${result.insights_count} insights)`, 'success');
                
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
                this.sendDebugMessage(`Report generation failed: ${result.message || result.error || 'Unknown error'}`, 'error');
                if (generateBlock) {
                    generateBlock.classList.add('d-none');
                }
            }
        } catch (error) {
            this.sendDebugMessage(`Generate failed: ${error.message}`, 'error');
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
                this.sendDebugMessage(`Deleted ${result.deleted_count} insights`, 'success');
                setTimeout(() => this.refreshTable(), this.config.UI_REFRESH || 1000);
            } else {
                this.sendDebugMessage(`Delete failed: ${result.message || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            this.sendDebugMessage(`Delete failed: ${error.message}`, 'error');
        }
    }





    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         TIME AGO                    │
     *  └─────────────────────────────────────┘
     *  Calculate relative time string without 'ago'
     */
    timeAgo(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) {
            return `${diffInSeconds}s`;
        } else if (diffInSeconds < 3600) {
            return `${Math.floor(diffInSeconds / 60)}m`;
        } else if (diffInSeconds < 86400) {
            return `${Math.floor(diffInSeconds / 3600)}h`;
        } else {
            return `${Math.floor(diffInSeconds / 86400)}d`;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       TIME HORIZON                  │
     *  └─────────────────────────────────────┘
     *  Calculate time horizon with + for future, - for past
     */
    timeHorizon(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((date - now) / 1000);
        const absDiff = Math.abs(diffInSeconds);
        const prefix = diffInSeconds >= 0 ? '+' : '-';

        if (absDiff < 60) {
            return `${prefix}${absDiff}s`;
        } else if (absDiff < 3600) {
            return `${prefix}${Math.floor(absDiff / 60)}m`;
        } else if (absDiff < 86400) {
            return `${prefix}${Math.floor(absDiff / 3600)}h`;
        } else {
            return `${prefix}${Math.floor(absDiff / 86400)}d`;
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
