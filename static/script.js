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
    const aiCheckbox = document.getElementById('aiCheck');
    const selects = document.querySelectorAll('select');
    
    if (updateBtn) {
        updateBtn.addEventListener('click', function() {
            updateData();
        });
    }
    
    if (aiCheckbox) {
        aiCheckbox.addEventListener('change', function() {
            updateAIStatus();
        });
    }
    
    // Add change listeners to all selects
    selects.forEach(select => {
        if (select) {
            select.addEventListener('change', function() {
                updateAIStatus();
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
    const aiStatus = document.querySelector('.ai-status-text');
    
    if (!updateBtn || !aiStatus) {
        console.warn('Required elements not found for updateData');
        return;
    }
    
    try {
        // Show loading state
        updateBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>UPDATING...';
        updateBtn.disabled = true;
        
        // Call the update market data API
        fetch('/api/update-market-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update AI status with results
                const timestamp = new Date().toLocaleTimeString();
                const updateText = data.updated_insights > 0 
                    ? `${data.updated_insights} insights analyzed` 
                    : 'No insights to update';
                aiStatus.textContent = `[AI ENGINE] ${updateText} - ${timestamp}`;
                
                // Reload the page to show new data if any updates were made
                if (data.updated_insights > 0) {
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                }
            } else {
                aiStatus.textContent = `[AI ENGINE] Update failed: ${data.message || 'Unknown error'}`;
            }
            
            // Reset button
            updateBtn.innerHTML = 'UPDATE';
            updateBtn.disabled = false;
        })
        .catch(error => {
            console.error('Error updating data:', error);
            aiStatus.textContent = '[AI ENGINE] Update failed: Network error';
            
            // Reset button
            updateBtn.innerHTML = 'UPDATE';
            updateBtn.disabled = false;
        });
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
 * 
 * ┌─────────────────────────────────────┐
 * │         UPDATE AI STATUS            │
 * └─────────────────────────────────────┘
 * Updates the AI engine status display
 * 
 * Reflects changes in control panel settings and shows current AI processing state.
 * 
 * Parameters:
 * - None
 * 
 * Returns:
 * - None
 * 
 * Notes:
 * - Updates status based on AI checkbox state
 * - Shows different messages for enabled/disabled AI
 */
function updateAIStatus() {
    const aiCheckbox = document.getElementById('aiCheck');
    const aiStatus = document.querySelector('.ai-status-text');
    
    if (!aiCheckbox || !aiStatus) {
        console.warn('Required elements not found for updateAIStatus');
        return;
    }
    
    try {
        if (aiCheckbox.checked) {
            aiStatus.textContent = '[AI ENGINE] Active - Processing new data streams';
        } else {
            aiStatus.textContent = '[AI ENGINE] Disabled - Manual mode active';
        }
    } catch (error) {
        console.error('Error in updateAIStatus:', error);
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
