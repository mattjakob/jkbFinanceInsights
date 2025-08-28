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
    
    const generateBtn = document.querySelector('.generate-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', function() {
            generateAIMegasummary();
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
    
    // Calculate initial horizons and levels
    updateAllHorizons();
    updateAllLevels();
    
    // Apply initial confidence styling
    updateConfidenceStyling();
    
    // Update ages every minute
    setInterval(updateAllAges, 60000);
    
    // Update horizons and levels every minute (in case data changes)
    setInterval(updateAllHorizons, 60000);
    setInterval(updateAllLevels, 60000);
    
    // Update confidence styling every minute
    setInterval(updateConfidenceStyling, 60000);
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
            
            // Add CSS class for future timestamps
            if (age.startsWith('+')) {
                element.classList.add('age-future');
            } else {
                element.classList.remove('age-future');
            }
        } else {
            console.log(`Element ${index}: no timePosted attribute`);
        }
    });
}

/**
* 
*  ┌─────────────────────────────────────┐
*  │      UPDATE ALL HORIZONS            │
*  └─────────────────────────────────────┘
*  Updates the horizon display for all insight rows
* 
*  Iterates through all horizon elements and formats their event time
*  based on the data-event-time attribute.
* 
*  Parameters:
*  - None
* 
*  Returns:
*  - None
* 
*  Notes:
*  - Processes all horizon elements on the page
*  - Handles missing or invalid time data gracefully
*/
function updateAllHorizons() {
    const horizonElements = document.querySelectorAll('.time-text[data-event-time]');
    
    horizonElements.forEach((element) => {
        const eventTime = element.getAttribute('data-event-time');
        
        if (eventTime) {
            const formattedTime = formatEventTime(eventTime);
            element.textContent = formattedTime;
        } else {
            element.textContent = '-';
        }
    });
}

/**
* 
*  ┌─────────────────────────────────────┐
*  │       UPDATE ALL LEVELS             │
*  └─────────────────────────────────────┘
*  Updates the levels display for all insight rows
* 
*  Iterates through all levels elements and formats their levels data
*  based on the data-levels attribute.
* 
*  Parameters:
*  - None
* 
*  Returns:
*  - None
* 
*  Notes:
*  - Processes all levels elements on the page
*  - Handles missing or invalid levels data gracefully
*/
function updateAllLevels() {
    const levelsElements = document.querySelectorAll('.levels-text[data-levels]');
    
    levelsElements.forEach((element) => {
        const levels = element.getAttribute('data-levels');
        
        if (levels) {
            const formattedLevels = formatLevels(levels);
            element.textContent = formattedLevels;
        } else {
            element.textContent = '-';
        }
    });
}

/**
* 
*  ┌─────────────────────────────────────┐
*  │      UPDATE CONFIDENCE STYLING      │
*  └─────────────────────────────────────┘
*  Applies low confidence styling to rows with confidence <50%
* 
*  Iterates through all insight rows and applies the low-confidence
*  CSS class based on the confidence value in the confidence column.
* 
*  Parameters:
*  - None
* 
*  Returns:
*  - None
* 
*  Notes:
*  - Applies 50% opacity to rows with confidence <50%
*  - Removes styling from rows with confidence >=50%
*  - Works with both initial page load and dynamic updates
*/
function updateConfidenceStyling() {
    const insightRows = document.querySelectorAll('.insight-row');
    
    insightRows.forEach((row) => {
        const confidenceCell = row.querySelector('.confidence-col .confidence-value');
        if (confidenceCell) {
            const confidenceText = confidenceCell.textContent;
            const confidencePercent = parseInt(confidenceText);
            
            if (!isNaN(confidencePercent) && confidencePercent < 50) {
                row.classList.add('low-confidence');
            } else {
                row.classList.remove('low-confidence');
            }
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
/**
* 
*  ┌─────────────────────────────────────┐
*  │        FORMAT EVENT TIME            │
*  └─────────────────────────────────────┘
*  Formats AIEventTime for display in HORIZON column
* 
*  Takes a timestamp and returns a user-friendly format like "Jan 27" or time portion.
* 
*  Parameters:
*  - eventTime: string - ISO timestamp string or date string
* 
*  Returns:
*  - string - Formatted time string for display
* 
*  Notes:
*  - Returns short date format for dates
*  - Returns time portion for same-day events
*  - Handles various timestamp formats gracefully
*/
function formatEventTime(eventTime) {
    if (!eventTime || typeof eventTime !== 'string') {
        return '-';
    }
    
    try {
        const date = new Date(eventTime);
        if (isNaN(date.getTime())) {
            // If can't parse as date, return time portion if it looks like time
            return eventTime.includes(':') ? eventTime.slice(-5) : eventTime.substring(0, 5);
        }
        
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const eventDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
        
        // If it's today, show time portion
        if (eventDate.getTime() === today.getTime()) {
            return date.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit',
                hour12: false 
            });
        }
        
        // Otherwise show date
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric' 
        });
    } catch {
        // Fallback to original behavior
        return eventTime.includes(':') ? eventTime.slice(-5) : eventTime.substring(0, 5);
    }
}

/**
* 
*  ┌─────────────────────────────────────┐
*  │        FORMAT LEVELS                │
*  └─────────────────────────────────────┘
*  Formats AILevels for display in LEVELS column
* 
*  Takes raw levels string and returns only Entry and Take Profit levels
*  with currency formatting for numerical values.
* 
*  Parameters:
*  - levels: string - Raw levels string from database
* 
*  Returns:
*  - string - Formatted levels string showing only E: and TP: values with currency formatting
* 
*  Notes:
*  - Filters to show only Entry (E:) and Take Profit (TP:) levels
*  - Ignores SL, S, R, and other level types
*  - Formats all numbers as currency (e.g., $130,000)
*  - Maintains the original level type labels
*/
function formatLevels(levels) {
    if (!levels || typeof levels !== 'string') {
        return '-';
    }
    
    // Split levels by | and filter for only E: and TP: entries
    const levelParts = levels.split('|').map(part => part.trim());
    const filteredLevels = levelParts.filter(part => {
        const levelType = part.split(':')[0].trim();
        return levelType === 'E' || levelType === 'TP';
    });
    
    // Format each level with currency formatting
    const formattedLevels = filteredLevels.map(part => {
        const [levelType, levelValue] = part.split(':').map(s => s.trim());
        
        if (levelValue) {
            // Extract numeric value and format as currency
            const numericValue = parseFloat(levelValue.replace(/[^\d.-]/g, ''));
            if (!isNaN(numericValue)) {
                const formattedValue = new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD',
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0
                }).format(numericValue);
                
                return `${levelType}: ${formattedValue}`;
            }
        }
        
        return part; // Return original if no valid number found
    });
    
    // Return formatted levels joined with | separator
    return formattedLevels.length > 0 ? formattedLevels.join(' | ') : '-';
}

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
        
        // Always use UTC for comparison to avoid timezone issues
        const now = new Date();
        const nowUTC = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(),
                               now.getUTCHours(), now.getUTCMinutes(), now.getUTCSeconds());
        const postedUTC = postedDate.getTime();
        const diffMs = nowUTC - postedUTC;
        
        console.log(`Now UTC: ${new Date(nowUTC).toISOString()}, Posted UTC: ${postedDate.toISOString()}, Diff: ${diffMs}ms`);
        
        // Check if the date is in the future
        if (diffMs < 0) {
            // For items in the future, show how far in the future
            const futureDiffMs = Math.abs(diffMs);
            const futureDiffMinutes = Math.floor(futureDiffMs / (1000 * 60));
            const futureDiffHours = Math.floor(futureDiffMs / (1000 * 60 * 60));
            
            console.log(`Date is in the future: ${postedDate}`);
            
            if (futureDiffHours > 0) {
                return `+${futureDiffHours}h`;
            } else {
                return `+${futureDiffMinutes}m`;
            }
        }
        
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        console.log(`Time difference: ${diffDays}d ${diffHours % 24}h ${diffMinutes % 60}m`);
        
        // Format based on duration
        if (diffDays > 365) {
            // For very old items, show the actual date
            const month = postedDate.toLocaleDateString('en-US', { month: 'short' });
            const day = postedDate.getDate();
            const year = postedDate.getFullYear();
            return `${month} ${day}, ${year}`;
        } else if (diffDays > 30) {
            // Show in weeks for items older than a month
            const weeks = Math.floor(diffDays / 7);
            return `${weeks}w`;
        } else if (diffDays > 0) {
            return `${diffDays}d`;
        } else if (diffHours > 0) {
            const remainingMinutes = diffMinutes % 60;
            return `${diffHours}h${remainingMinutes.toString().padStart(2, '0')}`;
        } else if (diffMinutes > 0) {
            return `${diffMinutes}m`;
        } else {
            return 'now';
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
                        
                        // Apply low confidence styling to the row
                        if (insight.AIConfidence < 0.5) {
                            row.classList.add('low-confidence');
                        } else {
                            row.classList.remove('low-confidence');
                        }
                    }
                    
                    // Update AI event time using data attribute approach
                    const timeCell = row.querySelector('.time-col .time-text');
                    if (timeCell) {
                        timeCell.setAttribute('data-event-time', insight.AIEventTime || '');
                        const formattedTime = formatEventTime(insight.AIEventTime || '');
                        timeCell.innerHTML = insight.AIEventTime 
                            ? `<span class="time-value">${formattedTime}</span>`
                            : '<span class="text-muted">-</span>';
                    }
                    
                    // Update AI levels using data attribute approach
                    const levelsCell = row.querySelector('.levels-col .levels-text');
                    if (levelsCell) {
                        levelsCell.setAttribute('data-levels', insight.AILevels || '');
                        const formattedLevels = formatLevels(insight.AILevels || '');
                        levelsCell.innerHTML = insight.AILevels 
                            ? formattedLevels
                            : '<span class="text-muted">-</span>';
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
            const formattedTime = formatTimestamp(status.timestamp);
            updateStatusBar(formattedTime + ' ' + status.full_message);
        }
    } catch (error) {
        console.error('Error fetching debug status:', error);
        updateStatusBar('! Connection error');
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
 * Fetches the latest insights data from the API and updates the table
 * to show current AI analysis status without full page reload.
 * 
 * Parameters:
 * - None
 * 
 * Returns:
 * - None
 * 
 * Notes:
 * - Updates AI status indicators in real-time
 * - Preserves user interactions and scroll position
 */
async function refreshTableData() {
    try {
        // Get current filter parameters
        const symbolFilter = document.getElementById('symbolFilter')?.value || '';
        const typeFilter = document.getElementById('typeFilter')?.value || '';
        
        // Fetch latest insights data
        const response = await fetch(`/api/insights?symbol=${encodeURIComponent(symbolFilter)}&type=${encodeURIComponent(typeFilter)}`);
        
        if (!response.ok) {
            console.error('Failed to fetch insights data:', response.status);
            return;
        }
        
        const insights = await response.json();
        
        console.log(`Refreshing table with ${insights.length} insights`);
        
        // Update table rows with new data
        updateTableRows(insights);
        
        console.log('Table data refreshed successfully');
    } catch (error) {
        console.error('Error refreshing table data:', error);
    }
}

/**
 * 
 * ┌─────────────────────────────────────┐
 * │          UPDATE TABLE ROWS          │
 * └─────────────────────────────────────┘
 * Updates existing table rows with fresh data
 * 
 * Updates the content of table rows to reflect the latest AI analysis
 * status and other field changes without disrupting the page layout.
 * 
 * Parameters:
 * - insights: Array of insight objects with updated data
 * 
 * Returns:
 * - None
 * 
 * Notes:
 * - Preserves existing table structure and row heights
 * - Only updates changed content
 * - Prevents table jumping during updates
 */
function updateTableRows(insights) {
    const tableBody = document.querySelector('tbody');
    if (!tableBody) return;
    
    // Create a map of insights by ID for quick lookup
    const insightMap = new Map();
    insights.forEach(insight => {
        insightMap.set(insight.id, insight);
    });
    
    const rows = tableBody.querySelectorAll('tr[data-insight-id]');
    
    rows.forEach(row => {
        const insightId = parseInt(row.getAttribute('data-insight-id'));
        const insight = insightMap.get(insightId);
        
        if (!insight) return; // Skip if no matching insight found
        
        const cells = row.querySelectorAll('td');
        
        if (cells.length < 9) return; // Ensure we have enough cells (0-8 = 9 columns)
        
        // Column indices based on HTML table structure:
        // 0: TYPE, 1: SYMBOL, 2: AGE, 3: TITLE, 4: AI SUMMARY, 5: ACTION, 6: RELEVANCE, 7: HORIZON, 8: LEVELS
        
        // Update AI Summary column (index 4)
        updateAICellStable(cells[4], insight.AISummary, insight.AIAnalysisStatus, (summary) => {
            return summary.length > 100 ? summary.substring(0, 100) + '...' : summary;
        });
        
        // Update Action column (index 5)
        updateAICellStable(cells[5], insight.AIAction, insight.AIAnalysisStatus, (action) => {
            const actionUpper = action.toUpperCase();
            let iconClass = '';
            let badgeClass = '';
            
            if (actionUpper.includes('SELL')) {
                iconClass = 'bi-graph-down-arrow';
                badgeClass = 'action-sell';
            } else if (actionUpper.includes('BUY')) {
                iconClass = 'bi-graph-up-arrow';
                badgeClass = 'action-buy';
            } else if (actionUpper.includes('HOLD')) {
                iconClass = 'bi-hourglass-split';
                badgeClass = 'action-hold';
            } else {
                badgeClass = 'action-neutral';
            }
            
            return `<span class="action-badge ${badgeClass}">${actionUpper}${iconClass ? ` <i class="bi ${iconClass}"></i>` : ''}</span>`;
        });
        
        // Update Relevance column (index 6)
        updateAICellStable(cells[6], insight.AIConfidence, insight.AIAnalysisStatus, (confidence) => {
            // Apply low confidence styling to the row
            const row = cells[6].closest('.insight-row');
            if (row && insight.AIConfidence !== null && insight.AIConfidence !== undefined) {
                if (insight.AIConfidence < 0.5) {
                    row.classList.add('low-confidence');
                } else {
                    row.classList.remove('low-confidence');
                }
            }
            
            return `<span class="confidence-value">${Math.round(confidence * 100)}%</span>`;
        });
        
        // Update Horizon column (index 7 - AIEventTime) using data attribute approach
        const horizonCell = cells[7].querySelector('.time-text');
        if (horizonCell) {
            horizonCell.setAttribute('data-event-time', insight.AIEventTime || '');
        }
        updateAICellStable(cells[7], insight.AIEventTime, insight.AIAnalysisStatus, (eventTime) => {
            const formattedTime = formatEventTime(eventTime);
            return formattedTime;
        });
        
        // Update Levels column (index 8) using data attribute approach
        const levelsCell = cells[8].querySelector('.levels-text');
        if (levelsCell) {
            levelsCell.setAttribute('data-levels', insight.AILevels || '');
        }
        updateAICellStable(cells[8], insight.AILevels, insight.AIAnalysisStatus, (levels) => {
            const formattedLevels = formatLevels(levels);
            return formattedLevels;
        });
    });
    
}

/**
 * 
 * ┌─────────────────────────────────────┐
 * │           UPDATE AI CELL            │
 * └─────────────────────────────────────┘
 * Updates a single table cell based on AI analysis status
 * 
 * Updates cell content to show loading spinner, data, or empty state
 * based on the current AI analysis status.
 * 
 * Parameters:
 * - cell: The table cell DOM element to update
 * - data: The data value for this cell
 * - status: The AI analysis status ('pending', 'processing', 'completed', 'failed')
 * - formatter: Function to format the data for display
 * 
 * Returns:
 * - None
 * 
 * Notes:
 * - Shows spinner only during 'processing' status
 * - Shows data when available
 * - Shows nothing when data is empty/null/none
 */
function updateAICell(cell, data, status, formatter) {
    if (data != null && data !== '') {
        // Show data if available
        cell.innerHTML = formatter(data);
    } else if (status === 'processing') {
        // Show spinner only during processing
        cell.innerHTML = '<div class="loading-spinner"></div>';
    } else {
        // Show nothing for empty/null data
        cell.innerHTML = '';
    }
}

/**
 * 
 * ┌─────────────────────────────────────┐
 * │        UPDATE AI CELL STABLE        │
 * └─────────────────────────────────────┘
 * Updates a single table cell without changing row height
 * 
 * Updates cell content while preserving the original cell dimensions
 * to prevent table row height changes during updates.
 * 
 * Parameters:
 * - cell: The table cell DOM element to update
 * - data: The data value for this cell
 * - status: The AI analysis status ('pending', 'processing', 'completed', 'failed')
 * - formatter: Function to format the data for display
 * 
 * Returns:
 * - None
 * 
 * Notes:
 * - Preserves cell height to prevent table jumping
 * - Uses textContent for better height stability
 * - Maintains consistent visual appearance
 */
function updateAICellStable(cell, data, status, formatter) {
    if (data != null && data !== '') {
        // Show data if available
        const formattedContent = formatter(data);
        
        if (formattedContent.includes('<')) {
            cell.innerHTML = formattedContent;
        } else {
            cell.textContent = formattedContent;
        }
    } else if (status === 'processing') {
        // Show spinner only during processing
        cell.innerHTML = '<div class="loading-spinner"></div>';
    } else {
        // Show nothing for empty/null data
        cell.textContent = '';
    }
}

/**
 * 
 * ┌─────────────────────────────────────┐
 * │         FORMAT TIMESTAMP            │
 * └─────────────────────────────────────┘
 * Formats a timestamp string to hh:mm AM/PM format
 * 
 * Converts ISO timestamp strings to readable time format
 * for display in the status bar.
 * 
 * Parameters:
 * - timestamp: ISO timestamp string (e.g., "2025-08-27T23:09:51.495623")
 * 
 * Returns:
 * - Formatted time string in "hh:mm AM/PM" format
 * 
 * Notes:
 * - Handles various timestamp formats gracefully
 * - Returns "Invalid time" for malformed timestamps
 */
function formatTimestamp(timestamp) {
    try {
        if (!timestamp) return '';
        
        const date = new Date(timestamp);
        
        // Check if date is valid
        if (isNaN(date.getTime())) {
            return '';
        }
        
        // Format to hh:mm AM/PM
        const hours = date.getHours();
        const minutes = date.getMinutes();
        const ampm = hours >= 12 ? 'PM' : 'AM';
        const displayHours = hours % 12 || 12;
        const displayMinutes = minutes.toString().padStart(2, '0');
        
        return `${displayHours}:${displayMinutes} ${ampm}`;
    } catch (error) {
        console.error('Error formatting timestamp:', error);
        return '';
    }
}

/**
 * 
 * ┌─────────────────────────────────────┐
 * │         START AUTO REFRESH          │
 * └─────────────────────────────────────┘
 * Starts automatic data refresh at regular intervals
 * 
 * Implements periodic updates to show real-time AI analysis status changes.
 * 
 * Parameters:
 * - None
 * 
 * Returns:
 * - None
 * 
 * Notes:
 * - Updates every 5 seconds for real-time AI status tracking
 * - Only refreshes table data, not the entire page
 */
function startAutoRefresh() {
    // Auto-refresh every 5 seconds to show real-time AI status updates
    setInterval(() => {
        // Only refresh if we're on the main page with the table
        const tableBody = document.querySelector('tbody');
        if (tableBody && tableBody.children.length > 0) {
            refreshTableData();
        }
    }, 5000); // 5 seconds for responsive AI status updates
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

/**
 * 
 * ┌─────────────────────────────────────┐
 * │      GENERATE AI MEGASUMMARY        │
 * └─────────────────────────────────────┘
 * Generates AI-powered megasummary analysis
 * 
 * Calls the AI megasummary endpoint and displays results in the generate block.
 * Shows loading state and handles errors gracefully.
 * 
 * Parameters:
 * - None
 * 
 * Returns:
 * - None
 * 
 * Notes:
 * - Makes POST request to /summary/generate endpoint
 * - Updates generate block with AI analysis results
 * - Handles loading states and error conditions
 */
async function generateAIMegasummary() {
    try {
        // Show generate block and loading state
        const generateBlock = document.getElementById('generateBlock');
        const generateContent = document.getElementById('generateContent');
        const generateBtn = document.querySelector('.generate-btn');
        
        // Show the generate block
        generateBlock.style.display = 'block';
        
        // Show loading state
        generateContent.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-warning" role="status">
                    <span class="visually-hidden">Generating...</span>
                </div>
                <p class="mt-2">Generating AI analysis...</p>
            </div>
        `;
        
        // Disable button during generation
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> GENERATING...';
        
        // Call the AI megasummary endpoint
        const response = await fetch('/summary/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        if (response.ok) {
            const aiAnalysis = await response.text();
            
            // Display the AI analysis
            generateContent.innerHTML = `
                <div class="ai-analysis">
                    <div class="ai-content">
                        ${aiAnalysis.replace(/\n/g, '<br>').replace(/\r/g, '').replace(/\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;')}
                    </div>
                </div>
            `;
        } else {
            generateContent.innerHTML = `
                <div class="text-center text-danger">
                    <i class="bi bi-exclamation-triangle"></i>
                    <p class="mt-2">Error generating AI analysis</p>
                    <p class="small">HTTP ${response.status}</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error generating AI megasummary:', error);
        const generateContent = document.getElementById('generateContent');
        generateContent.innerHTML = `
            <div class="text-center text-danger">
                <i class="bi bi-exclamation-triangle"></i>
                <p class="mt-2">Network error while generating AI analysis</p>
                <p class="small">${error.message}</p>
            </div>
        `;
    } finally {
        // Re-enable button
        const generateBtn = document.querySelector('.generate-btn');
        generateBtn.disabled = false;
        generateBtn.innerHTML = 'GENERATE';
    }
}


