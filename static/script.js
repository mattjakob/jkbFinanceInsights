/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │            JKB FINANCE             │
 *  └─────────────────────────────────────┘
 *  Main JavaScript functionality for JKB Finance Terminal
 * 
 *  Handles control panel interactions, table updates, and dynamic content loading.
 *  Provides real-time updates and interactive features for the financial insights interface.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - None
 * 
 *  Notes:
 *  - Uses Bootstrap 5 components for UI interactions
 *  - Implements loading states and dynamic content updates
 */

// Wait for DOM to be fully loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    // DOM is already loaded
    initializeApp();
}

function initializeApp() {
    try {
        // Initialize control panel functionality
        initializeControlPanel();
        
        // Initialize table interactions
        initializeTableInteractions();
        
        // Initialize age calculations
        initializeAgeCalculations();
        
        // Initialize status bar updates
        initializeStatusUpdates();
        
        // Auto-refresh functionality
        startAutoRefresh();
        
        console.log('JKB Finance Terminal initialized successfully');
    } catch (error) {
        console.error('Error during initialization:', error);
    }
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         INITIALIZE CONTROL          │
 *  └─────────────────────────────────────┘
 *  Sets up control panel event listeners and functionality
 * 
 *  Handles dropdown changes, AI checkbox toggle, and update button clicks.
 *  Manages the state of all control elements and triggers appropriate actions.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - None
 * 
 *  Notes:
 *  - Updates AI status display when controls change
 *  - Triggers data refresh when update button is clicked
 */
function initializeControlPanel() {
    const updateBtn = document.querySelector('.update-btn');
    const fetchBtn = document.querySelector('.fetch-btn');
    const deleteBtn = document.querySelector('.delete-btn');
    const resetBtn = document.getElementById('resetBtn');
    const resetInsightIdInput = document.getElementById('resetInsightId');
    const symbolInput = document.getElementById('symbolInput');
    const typeFilter = document.getElementById('typeFilter');
    const selects = document.querySelectorAll('select');
    
    if (updateBtn) {
        updateBtn.addEventListener('click', function() {
            updateData();
        });
    }
    
    if (fetchBtn) {
        fetchBtn.addEventListener('click', function() {
            fetchData();
        });
    }
    
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            deleteSelectedInsights();
        });
    }
    
    // Initialize type filter
    if (typeFilter) {
        typeFilter.addEventListener('change', function() {
            applyTypeFilter(this.value);
        });
    }
    
    // Initialize symbol validation and chart updates
    if (symbolInput) {
        initializeSymbolValidation(symbolInput);
        
        // Add debounced TradingView chart update on symbol change
        let chartUpdateTimeout;
        symbolInput.addEventListener('input', function() {
            console.log('TradingView: Symbol input changed to:', this.value);
            clearTimeout(chartUpdateTimeout);
            chartUpdateTimeout = setTimeout(() => {
                TradingViewChart.updateFromInputs();
            }, 1000); // 1 second debounce
        });
    }
    
    // Add debounced TradingView chart update on exchange change
    const exchangeInput = document.getElementById('exchangeInput');
    if (exchangeInput) {
        let exchangeUpdateTimeout;
        exchangeInput.addEventListener('input', function() {
            console.log('TradingView: Exchange input changed to:', this.value);
            clearTimeout(exchangeUpdateTimeout);
            exchangeUpdateTimeout = setTimeout(() => {
                TradingViewChart.updateFromInputs();
            }, 1000); // 1 second debounce
        });
    }
    
    if (resetBtn && resetInsightIdInput) {
        resetBtn.addEventListener('click', function() {
            resetInsightAI(parseInt(resetInsightIdInput.value));
        });
    }
    
    // Add change listeners to all selects
    selects.forEach(select => {
        if (select) {
            select.addEventListener('change', function() {
                // Select changed - could add logic here if needed
            });
        }
    });
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         INITIALIZE TABLE            │
 *  └─────────────────────────────────────┘
 *  Sets up table row interactions and functionality
 * 
 *  Handles row clicks, hover effects, and navigation to detail pages.
 *  Provides interactive feedback for user actions on the data table.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - None
 * 
 *  Notes:
 *  - Implements row click navigation to detail pages
 *  - Adds hover effects for better user experience
 *  - Prevents navigation when clicking on interactive elements
 */
function initializeTableInteractions() {
    const tableRows = document.querySelectorAll('.insight-row');
    
    if (tableRows.length === 0) {
        return; // No insights to interact with
    }
    
    tableRows.forEach(row => {
        // Add click handler for navigation to detail page
        row.addEventListener('click', function(e) {
            // Don't navigate if clicking on interactive elements
            if (e.target.closest('.action-badge') || 
                e.target.closest('.loading-spinner') ||
                e.target.closest('.confidence-value') ||
                e.target.closest('.levels-text')) {
                return;
            }
            
            // Get the insight ID from the row data attribute
            const insightId = this.getAttribute('data-insight-id');
            if (insightId) {
                // Navigate to the detail page
                window.location.href = `/insight/${insightId}`;
            }
        });
        
        // Add hover effect
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = 'var(--color-hover)';
            this.style.cursor = 'pointer';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
            this.style.cursor = '';
        });
    });
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         INITIALIZE AGE              │
 *  └─────────────────────────────────────┘
 *  Sets up age calculations for all insight rows
 * 
 *  Calculates and displays the time difference between timePosted and now
 *  in appropriate format (dd, hh:mm, or mm).
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - None
 * 
 *  Notes:
 *  - Updates age display every minute for real-time accuracy
 *  - Handles various time formats gracefully
 */
function initializeAgeCalculations() {
    // Calculate initial ages
    updateAllAges();
    
    // Update ages every minute
    setInterval(updateAllAges, 60000);
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         UPDATE ALL AGES             │
 *  └─────────────────────────────────────┘
 *  Updates the age display for all insight rows
 * 
 *  Iterates through all age elements and calculates their current age
 *  based on the timePosted data attribute.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - None
 * 
 *  Notes:
 *  - Processes all age elements on the page
 *  - Handles missing or invalid time data gracefully
 */
function updateAllAges() {
    const ageElements = document.querySelectorAll('.age-text[data-time-posted]');
    
    if (ageElements.length === 0) {
        console.log('No age elements found');
        return; // No age elements to update
    }
    
    console.log(`Found ${ageElements.length} age elements to update`);
    
    ageElements.forEach((element, index) => {
        const timePosted = element.getAttribute('data-time-posted');
        console.log(`Element ${index}: timePosted = "${timePosted}"`);
        
        if (timePosted) {
            const age = calculateAge(timePosted);
            console.log(`Element ${index}: calculated age = "${age}"`);
            element.textContent = age;
        } else {
            console.log(`Element ${index}: no timePosted attribute`);
        }
    });
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         CALCULATE AGE               │
 *  └─────────────────────────────────────┘
 *  Calculates the time difference between timePosted and now
 * 
 *  Returns the age in appropriate format:
 *  - dd (days) for differences > 24 hours
 *  - hh:mm (hours:minutes) for differences < 24 hours
 *  - mm (minutes) for differences < 1 hour
 * 
 *  Parameters:
 *  - timePosted: string - ISO timestamp string
 * 
 *  Returns:
 *  - string - Formatted age string
 * 
 *  Notes:
 *  - Handles various timestamp formats
 *  - Returns appropriate format based on duration
 *  - Handles edge cases gracefully
 */
function calculateAge(timePosted) {
    console.log(`calculateAge called with: "${timePosted}"`);
    
    if (!timePosted || typeof timePosted !== 'string') {
        console.log(`Invalid timePosted: ${timePosted} (type: ${typeof timePosted})`);
        return '-';
    }
    
    try {
        // Parse the posted time
        let postedDate;
        
        // Handle different timestamp formats
        if (timePosted.includes('T')) {
            // ISO format: 2025-01-27T10:30:00
            postedDate = new Date(timePosted);
            console.log(`Parsed as ISO format: ${postedDate}`);
        } else if (timePosted.includes('-')) {
            // Date format: 2025-01-27 10:30:00
            postedDate = new Date(timePosted.replace(' ', 'T'));
            console.log(`Parsed as date format: ${postedDate}`);
        } else {
            // Try parsing as is
            postedDate = new Date(timePosted);
            console.log(`Parsed as is: ${postedDate}`);
        }
        
        // Check if date is valid
        if (isNaN(postedDate.getTime())) {
            console.log(`Invalid date: ${postedDate}`);
            return '-';
        }
        
        const now = new Date();
        const diffMs = now - postedDate;
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        console.log(`Time difference: ${diffDays}d ${diffHours % 24}h ${diffMinutes % 60}m`);
        
        // Format based on duration
        if (diffDays > 0) {
            return `${diffDays}d`;
        } else if (diffHours > 0) {
            const remainingMinutes = diffMinutes % 60;
            return `${diffHours}h${remainingMinutes.toString().padStart(2, '0')}`;
        } else {
            return `${diffMinutes}m`;
        }
        
    } catch (error) {
        console.error('Error calculating age:', error);
        return '-';
    }
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │           UPDATE DATA               │
 *  └─────────────────────────────────────┘
 *  Triggers data refresh and updates the interface
 * 
 *  Simulates data loading and updates the AI status display.
 *  Handles the update button click functionality.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - None
 * 
 *  Notes:
 *  - Shows loading state during update
 *  - Updates AI engine status with new timestamp
 */
function updateData() {
    const updateBtn = document.querySelector('.update-btn');
    const statusBar = document.querySelector('.status-bar-text');
    
    if (!updateBtn || !statusBar) {
        console.warn('Required elements not found for updateData');
        return;
    }
    
    try {
        // Show loading state
        updateBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>UPDATING...';
        updateBtn.disabled = true;
        
        // Use SSE for real-time updates
        const eventSource = new EventSource('/api/insights/analyze/stream');
        
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.type === 'complete') {
                // Update individual insight rows with new AI data
                updateInsightRows(data.processed, data.success);
                
                // Reset button
                updateBtn.innerHTML = 'UPDATE';
                updateBtn.disabled = false;
                eventSource.close();
            } else if (data.type === 'error') {
                console.error('AI analysis error:', data.message);
                updateBtn.innerHTML = 'UPDATE';
                updateBtn.disabled = false;
                eventSource.close();
            }
        };
        
        eventSource.onerror = function(error) {
            console.error('SSE error:', error);
            updateBtn.innerHTML = 'UPDATE';
            updateBtn.disabled = false;
            eventSource.close();
        };
    } catch (error) {
        console.error('Error in updateData:', error);
        // Reset button on error
        if (updateBtn) {
            updateBtn.innerHTML = 'UPDATE';
            updateBtn.disabled = false;
        }
    }
}

/**
 * Update individual insight rows with new AI analysis data
 */
function updateInsightRows(processed, success) {
    // Fetch updated insights data and update rows
    fetch('/api/insights')
        .then(response => response.json())
        .then(insights => {
            insights.forEach(insight => {
                const row = document.querySelector(`tr[data-insight-id="${insight.id}"]`);
                if (row) {
                    // Update AI summary
                    const summaryCell = row.querySelector('.summary-col');
                    if (summaryCell && insight.AISummary) {
                        summaryCell.innerHTML = insight.AISummary.length > 100 
                            ? insight.AISummary.substring(0, 100) + '...' 
                            : insight.AISummary;
                    }
                    
                    // Update AI action
                    const actionCell = row.querySelector('.action-col');
                    if (actionCell && insight.AIAction) {
                        let actionClass = 'action-neutral';
                        if (insight.AIAction.toUpperCase().includes('SELL')) actionClass = 'action-sell';
                        else if (insight.AIAction.toUpperCase().includes('BUY')) actionClass = 'action-buy';
                        else if (insight.AIAction.toUpperCase().includes('HOLD')) actionClass = 'action-hold';
                        
                        actionCell.innerHTML = `<span class="action-badge ${actionClass}">${insight.AIAction.substring(0, 4).toUpperCase()}</span>`;
                    }
                    
                    // Update AI confidence
                    const confidenceCell = row.querySelector('.confidence-col');
                    if (confidenceCell && insight.AIConfidence) {
                        confidenceCell.innerHTML = `<span class="confidence-value">${Math.round(insight.AIConfidence * 100)}%</span>`;
                    }
                    
                    // Update AI event time
                    const timeCell = row.querySelector('.time-col');
                    if (timeCell && insight.AIEventTime) {
                        timeCell.innerHTML = insight.AIEventTime.includes(':') 
                            ? insight.AIEventTime.slice(-5) 
                            : insight.AIEventTime.substring(0, 5);
                    }
                    
                    // Update AI levels
                    const levelsCell = row.querySelector('.levels-col');
                    if (levelsCell && insight.AILevels) {
                        levelsCell.innerHTML = `<span class="levels-text">${insight.AILevels.length > 30 
                            ? insight.AILevels.substring(0, 30) + '...' 
                            : insight.AILevels}</span>`;
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error updating insight rows:', error);
        });
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │           FETCH DATA                │
 *  └─────────────────────────────────────┘
 *  Triggers data fetching from external sources
 * 
 *  Initiates the feed scraper to fetch new insights from configured
 *  data sources based on current symbol/exchange/type settings.
 * 
 *  Parameters:
 *  - None (uses current form values)
 * 
 *  Returns:
 *  - None (updates interface and shows results)
 * 
 *  Notes:
 *  - Shows loading state during fetch operation
 *  - Uses feedScraper system for data retrieval
 */
function fetchData() {
    const fetchBtn = document.querySelector('.fetch-btn');
    const symbolInput = document.getElementById('symbolInput');
    const exchangeInput = document.getElementById('exchangeInput');
    const typeFilter = document.getElementById('typeFilter');
    const itemsSelect = document.querySelector('select[title="Number of Items"]');
    
    if (!fetchBtn) {
        console.warn('Fetch button not found');
        return;
    }
    
    // Get current form values
    const symbol = symbolInput ? symbolInput.value.trim().toUpperCase() : 'BTCUSD';
    const exchange = exchangeInput ? exchangeInput.value.trim().toUpperCase() : 'BINANCE';
    const feedType = typeFilter ? typeFilter.value : '';
    const maxItems = itemsSelect ? parseInt(itemsSelect.value) || 10 : 10;
    
    try {
        // Show loading state
        fetchBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>FETCHING...';
        fetchBtn.disabled = true;
        
        // Call the fetch API endpoint
        const requestBody = {
            symbol,
            exchange,
            feedType,
            maxItems: parseInt(maxItems)
        };
        
        fetch('/api/insights/fetch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Fetch operation completed:', data);
            
            if (data.success) {
                // Show success message with details
                const message = `${data.created_insights} insights created, ${data.failed_items} failed`;
                console.log(`✓ Fetch successful: ${message}`);
                
                // Reload page if insights were created
                if (data.created_insights > 0) {
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                }
        } else {
                console.error('Fetch failed:', data.message);
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
        })
        .finally(() => {
            // Reset button
            fetchBtn.innerHTML = 'FETCH';
            fetchBtn.disabled = false;
        });
        
    } catch (error) {
        console.error('Error in fetchData:', error);
        // Reset button on error
        if (fetchBtn) {
            fetchBtn.innerHTML = 'FETCH';
            fetchBtn.disabled = false;
        }
    }
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │     DELETE SELECTED INSIGHTS        │
 *  └─────────────────────────────────────┘
 *  Delete all insights of the selected type
 * 
 *  Gets the current type filter value and deletes all insights
 *  matching that type using the delete_select_insights API.
 * 
 *  Parameters:
 *  - None (uses current TYPE dropdown value)
 * 
 *  Returns:
 *  - None (shows confirmation and reloads page)
 * 
 *  Notes:
 *  - Shows confirmation dialog before deletion
 *  - Uses type from TYPE dropdown as filter
 *  - Reloads page after successful deletion
 */
function deleteSelectedInsights() {
    const deleteBtn = document.querySelector('.delete-btn');
    const typeFilter = document.getElementById('typeFilter');
    
    if (!deleteBtn) {
        console.warn('Delete button not found');
        return;
    }
    
    // Get the selected type from the dropdown
    const selectedType = typeFilter ? typeFilter.value : '';
    
    // Determine what will be deleted
    let deleteMessage;
    if (!selectedType || selectedType === '') {
        deleteMessage = 'This will delete ALL insights in the database. This action cannot be undone.';
    } else {
        deleteMessage = `This will delete all insights of type "${selectedType}". This action cannot be undone.`;
    }
    
    // Show confirmation dialog
    if (!confirm(`⚠️ DELETE CONFIRMATION\n\n${deleteMessage}\n\nAre you sure you want to proceed?`)) {
        return;
    }
    
    try {
        // Show loading state
        deleteBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>DELETING...';
        deleteBtn.disabled = true;
        
        // Call the delete API endpoint
        const params = new URLSearchParams({
            type: selectedType
        });
        
        fetch(`/api/insights?${params}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            console.log('Delete operation completed:', data);
            
            if (data.success) {
                // Show success message with details
                const message = `${data.deleted_count} insights deleted, ${data.failed_count} failed`;
                console.log(`✓ Delete successful: ${message}`);
                
                // Reload page to show updated insights list
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                console.error('Delete failed:', data.message);
                alert(`Delete failed: ${data.message}`);
            }
        })
        .catch(error => {
            console.error('Delete error:', error);
            alert('Network error during deletion. Please try again.');
        })
        .finally(() => {
            // Reset button
            deleteBtn.innerHTML = 'DELETE';
            deleteBtn.disabled = false;
        });
        
    } catch (error) {
        console.error('Error in deleteSelectedInsights:', error);
        // Reset button on error
        if (deleteBtn) {
            deleteBtn.innerHTML = 'DELETE';
            deleteBtn.disabled = false;
        }
    }
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        APPLY TYPE FILTER            │
 *  └─────────────────────────────────────┘
 *  Apply type filter to insights display
 * 
 *  Reloads the page with the selected type filter applied to show
 *  only insights matching the selected feed type.
 * 
 *  Parameters:
 *  - filterValue: The type filter value (empty string for "ALL")
 * 
 *  Returns:
 *  - None (reloads page)
 * 
 *  Notes:
 *  - Uses URL parameters to maintain filter state
 */
function applyTypeFilter(filterValue) {
    const url = new URL(window.location);
    
    if (filterValue && filterValue.trim() !== '') {
        // Set the type_filter parameter
        url.searchParams.set('type_filter', filterValue);
    } else {
        // Remove the type_filter parameter for "ALL"
        url.searchParams.delete('type_filter');
    }
    
    // Reload the page with the new filter
    window.location.href = url.toString();
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │      FETCH DEBUG STATUS             │
 *  └─────────────────────────────────────┘
 *  Fetch current debug status from server
 * 
 *  Retrieves the current debug message and status from the debugger
 *  API and updates the status bar with the latest information.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - None (updates status bar)
 * 
 *  Notes:
 *  - Called periodically to keep status bar updated
 */
async function fetchDebugStatus() {
    try {
        const response = await fetch('/api/debug-status');
        if (response.ok) {
            const status = await response.json();
            updateStatusBar(status.full_message);
        }
    } catch (error) {
        console.error('Error fetching debug status:', error);
        updateStatusBar('[SYSTEM] Connection error');
    }
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │       UPDATE STATUS BAR             │
 *  └─────────────────────────────────────┘
 *  Update the status bar with a message
 * 
 *  Updates the status bar text content with the provided message.
 * 
 *  Parameters:
 *  - message: The message to display in the status bar
 * 
 *  Returns:
 *  - None
 */
function updateStatusBar(message) {
    const statusBarText = document.getElementById('statusBarText');
    if (statusBarText) {
        statusBarText.textContent = message;
    }
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │    INITIALIZE STATUS UPDATES        │
 *  └─────────────────────────────────────┘
 *  Initialize periodic status bar updates
 * 
 *  Sets up periodic fetching of debug status to keep the status bar
 *  updated with the latest system messages.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - None
 */
function initializeStatusUpdates() {
    // Fetch initial status
    fetchDebugStatus();
    
    // Set up periodic updates every 2 seconds
    setInterval(fetchDebugStatus, 2000);
}

/**
* 
*  ┌─────────────────────────────────────┐
*  │       INITIALIZE SYMBOL VALIDATION  │
*  └─────────────────────────────────────┘
*  Sets up autocomplete and validation for symbol input field.
* 
*  Provides real-time autocomplete suggestions using TradingView API
*  and validates symbols with visual feedback using Bootstrap classes.
* 
*  Parameters:
*  - symbolInput: The symbol input element
* 
*  Returns:
*  - Nothing
* 
*  Notes:
*  - Uses TradingView API for real symbol validation
*  - Converts input to uppercase automatically
*  - Shows autocomplete suggestions with keyboard navigation
*/
function initializeSymbolValidation(symbolInput) {
    const autocompleteDropdown = document.getElementById('symbolAutocomplete');
    const exchangeInput = document.getElementById('exchangeInput');
    let currentSuggestions = [];
    let selectedIndex = -1;
    let searchTimeout = null;
    let userModifiedExchange = false;
    
    // Auto-uppercase input and trigger search
    symbolInput.addEventListener('input', function() {
        this.value = this.value.toUpperCase();
        
        // Clear previous timeout
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        
        // Clear exchange when searching for new symbol
        if (this.value.trim().length > 0) {
            clearExchangeInput();
            setValidationIcon('default');
            userModifiedExchange = false; // Reset when user changes symbol
        }
        
        // Debounce search requests
        searchTimeout = setTimeout(() => {
            searchSymbols(this.value.trim());
        }, 300);
    });
    
    // Handle keyboard navigation
    symbolInput.addEventListener('keydown', function(e) {
        if (!autocompleteDropdown.classList.contains('show')) {
            return;
        }
        
        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                selectedIndex = Math.min(selectedIndex + 1, currentSuggestions.length - 1);
                updateHighlight();
                break;
            case 'ArrowUp':
                e.preventDefault();
                selectedIndex = Math.max(selectedIndex - 1, -1);
                updateHighlight();
                break;
            case 'Enter':
                e.preventDefault();
                if (selectedIndex >= 0 && selectedIndex < currentSuggestions.length) {
                    selectSuggestion(currentSuggestions[selectedIndex]);
                }
                break;
            case 'Escape':
                hideAutocomplete();
                break;
        }
    });
    
    // Hide autocomplete when clicking outside
    document.addEventListener('click', function(e) {
        if (!symbolInput.contains(e.target) && !autocompleteDropdown.contains(e.target)) {
            hideAutocomplete();
        }
    });
    
    // Validate on blur only if symbol has reasonable length
    symbolInput.addEventListener('blur', function() {
        // Delay to allow for suggestion selection
        setTimeout(() => {
            if (!autocompleteDropdown.classList.contains('show')) {
                const symbolValue = this.value.trim();
                if (symbolValue.length >= 2) {  // Only validate if symbol has at least 2 characters
                    validateSymbolWithAPI(symbolValue);
                } else if (symbolValue.length === 0) {
                    // Clear everything if symbol is empty
                    clearExchangeInput();
                    setValidationIcon('default');
                }
                // For 1 character, do nothing (don't clear exchange or set invalid)
            }
        }, 200);
    });
    
    // Auto-uppercase exchange input and track user modifications
    if (exchangeInput) {
        exchangeInput.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
            userModifiedExchange = true; // Track that user manually modified exchange
        });
    }
    
    // Initial validation
    if (symbolInput.value.trim()) {
        validateSymbolWithAPI(symbolInput.value.trim());
    } else {
        setValidationIcon('default');
    }
    
    // Search for symbol suggestions
    async function searchSymbols(query) {
        if (!query || query.length < 1) {
            hideAutocomplete();
            return;
        }
        
        try {
            showLoading();
            
            const response = await fetch(`/api/symbols/search?q=${encodeURIComponent(query)}&limit=8`);
            const data = await response.json();
            
            if (data.symbols && data.symbols.length > 0) {
                showSuggestions(data.symbols);
            } else {
                showNoResults();
            }
        } catch (error) {
            console.error('Error searching symbols:', error);
            hideAutocomplete();
        }
    }
    
    // Show loading state
    function showLoading() {
        autocompleteDropdown.innerHTML = '<div class="autocomplete-loading">SEARCHING...</div>';
        autocompleteDropdown.classList.add('show');
        selectedIndex = -1;
    }
    
    // Show suggestions
    function showSuggestions(symbols) {
        currentSuggestions = symbols;
        selectedIndex = -1;
        
        const html = symbols.map((symbol, index) => `
            <div class="autocomplete-item" data-index="${index}">
                <span class="symbol">${symbol.symbol}</span>
                <span class="exchange">${symbol.exchange}</span>
                <div class="description">${symbol.description}</div>
            </div>
        `).join('');
        
        autocompleteDropdown.innerHTML = html;
        autocompleteDropdown.classList.add('show');
        
        // Add click handlers
        autocompleteDropdown.querySelectorAll('.autocomplete-item').forEach((item, index) => {
            item.addEventListener('click', () => {
                selectSuggestion(symbols[index]);
            });
        });
    }
    
    // Show no results
    function showNoResults() {
        autocompleteDropdown.innerHTML = '<div class="autocomplete-no-results">NO SYMBOLS FOUND</div>';
        autocompleteDropdown.classList.add('show');
        selectedIndex = -1;
    }
    
    // Hide autocomplete
    function hideAutocomplete() {
        autocompleteDropdown.classList.remove('show');
        selectedIndex = -1;
    }
    
    // Update highlight
    function updateHighlight() {
        const items = autocompleteDropdown.querySelectorAll('.autocomplete-item');
        items.forEach((item, index) => {
            item.classList.toggle('highlighted', index === selectedIndex);
        });
    }
    
    // Select a suggestion
    function selectSuggestion(symbol) {
        symbolInput.value = symbol.symbol;
        hideAutocomplete();
        
        // Immediately populate exchange with the suggestion's exchange
        populateExchangeFromSuggestion(symbol);
        setValidationIcon('valid');
        
        symbolInput.focus();
    }
    
    // Populate exchange from autocomplete suggestion
    function populateExchangeFromSuggestion(symbolData) {
        const exchangeInput = document.getElementById('exchangeInput');
        
        if (symbolData.exchange) {
            exchangeInput.value = symbolData.exchange;
            userModifiedExchange = false; // Reset flag when populated from suggestion
        }
    }
    
    // Validate symbol with API
    async function validateSymbolWithAPI(symbol) {
        const iconElement = document.getElementById('symbolIcon');
        
        if (!symbol) {
            setValidationIcon('invalid');
            return false;
        }
        
        try {
            setValidationIcon('loading');
            
            const response = await fetch(`/api/symbols/validate?symbol=${encodeURIComponent(symbol)}`);
            
            const data = await response.json();
            
            if (data.valid) {
                setValidationIcon('valid');
                populateExchangeOptions(data);
                return true;
            } else {
                setValidationIcon('invalid');
                clearExchangeInput();
                return false;
            }
        } catch (error) {
            console.error('Error validating symbol:', error);
            setValidationIcon('invalid');
            return false;
        }
    }
    
    // Set validation icon state
    function setValidationIcon(state) {
        const iconElement = document.getElementById('symbolIcon');
        
        // Remove all possible classes
        iconElement.className = iconElement.className.replace(/bi-[a-zA-Z-]+/g, '');
        
        switch(state) {
            case 'loading':
                iconElement.classList.add('bi', 'bi-arrow-clockwise');
                break;
            case 'valid':
                iconElement.classList.add('bi', 'bi-check');
                break;
            case 'invalid':
                iconElement.classList.add('bi', 'bi-x');
                break;
            default:
                iconElement.classList.add('bi', 'bi-search');
                break;
        }
    }
    
    // Populate exchange input (only if empty or user hasn't manually set it)
    function populateExchangeOptions(validationData) {
        const exchangeInput = document.getElementById('exchangeInput');
        
        // Only populate if exchange field is empty and user hasn't manually modified it
        if (validationData.exchange && !exchangeInput.value.trim() && !userModifiedExchange) {
            exchangeInput.value = validationData.exchange;
        }
    }
    
    // Clear exchange input
    function clearExchangeInput() {
        const exchangeInput = document.getElementById('exchangeInput');
        exchangeInput.value = '';
        userModifiedExchange = false; // Reset flag when clearing
    }
}

/**
 * 
 * ┌─────────────────────────────────────┐
 * │        REFRESH TABLE DATA           │
 * └─────────────────────────────────────┘
 * Refreshes the table with new data
 * 
 * Simulates data refresh and updates loading states for incomplete entries.
 * 
 * Parameters:
 * - None
 * 
 * Returns:
 * - None
 * 
 * Notes:
 * - Updates loading spinners for incomplete data
 * - Simulates real-time data updates
 */
function refreshTableData() {
    // This function is now deprecated since we reload the page after updates
    // The UPDATE button calls the API which adds/updates data server-side
    // and then reloads the page to show the actual data from the database
    console.log('refreshTableData called - page will reload after API update');
}

/**
 * 
 * ┌─────────────────────────────────────┐
 * │         START AUTO REFRESH          │
 * └─────────────────────────────────────┘
 * Starts automatic data refresh at regular intervals
 * 
 * Implements periodic updates to simulate real-time financial data feed.
 * 
 * Parameters:
 * - None
 * 
 * Returns:
 * - None
 * 
 * Notes:
 * - Updates every 60 seconds by default
 * - Can be adjusted based on interval selection
 */
function startAutoRefresh() {
    // Auto-refresh every 60 seconds (adjustable based on interval selection)
    setInterval(() => {
        // Only auto-refresh if AI is enabled
        const aiCheckbox = document.getElementById('aiCheck');
        if (aiCheckbox && aiCheckbox.checked) {
            // Simulate subtle updates
            updateAIStatus();
        }
    }, 60000);
}

/**
 * 
 * ┌─────────────────────────────────────┐
 * │         DELETE INSIGHT              │
 * └─────────────────────────────────────┘
 * Deletes a financial insight entry
 * 
 * Handles the deletion of table rows and updates the interface accordingly.
 *  Makes an API call to delete the insight from the database and redirects
 *  to the main page upon successful deletion.
 * 
 * Parameters:
 * - insightId: The ID of the insight to delete
 * - redirectToHome: Whether to redirect to home page after deletion
 * 
 * Returns:
 * - None
 * 
 * Notes:
 * - Makes DELETE request to /insight/{id} endpoint
 * - Redirects to home page on successful deletion
 * - No confirmation dialog is shown
 */
async function deleteInsight(insightId, redirectToHome = false) {
    try {
        const response = await fetch(`/insight/${insightId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (response.ok) {
            if (redirectToHome) {
                // Redirect to home page after successful deletion
                window.location.href = '/';
            } else {
                // Remove the row from the table if on the main page
                const row = document.querySelector(`[data-insight-id="${insightId}"]`);
                if (row) {
                    row.remove();
                }
            }
        } else {
            console.error('Failed to delete insight:', response.status);
        }
    } catch (error) {
        console.error('Error deleting insight:', error);
    }
}

/**
 * 
 * ┌─────────────────────────────────────┐
 * │         RESET INSIGHT AI            │
 * └─────────────────────────────────────┘
 * Resets AI analysis fields for a specific insight
 * 
 * Makes an API call to reset all AI-related fields (AISummary, AIAction, 
 * AIConfidence, AIEventTime, AILevels) to null/empty for the specified insight ID.
 * 
 * Parameters:
 * - insightId: The ID of the insight to reset AI fields for
 * 
 * Returns:
 * - None
 * 
 * Notes:
 * - Makes POST request to /api/insights/{id}/reset-ai endpoint
 * - Shows success/error feedback to user
 * - Reloads page to reflect changes
 */
async function resetInsightAI(insightId) {
    if (!insightId || isNaN(insightId) || insightId < 1) {
        alert('Please enter a valid insight ID (must be a positive number)');
        return;
    }
    
    try {
        // Show loading state
        const resetBtn = document.getElementById('resetBtn');
        const originalText = resetBtn.innerHTML;
        resetBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Resetting...';
        resetBtn.disabled = true;
        
        const response = await fetch(`/api/insights/${insightId}/reset-ai`, {
            method: 'POST'
        });

        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                alert(`Successfully reset AI fields for insight #${insightId}`);
                // Reload the page to show updated data
                window.location.reload();
            } else {
                alert(`Failed to reset AI fields: ${result.message || 'Unknown error'}`);
            }
        } else {
            const errorData = await response.json().catch(() => ({}));
            alert(`Error resetting AI fields: ${errorData.message || `HTTP ${response.status}`}`);
        }
    } catch (error) {
        console.error('Error resetting insight AI:', error);
        alert('Network error while resetting AI fields. Please try again.');
    } finally {
        // Restore button state
        const resetBtn = document.getElementById('resetBtn');
        resetBtn.innerHTML = originalText;
        resetBtn.disabled = false;
    }
}

// TradingView chart functions moved to separate file: /static/tradingview-chart.js


