/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        INSIGHTS TABLE               │
 *  └─────────────────────────────────────┘
 *  Table component for displaying insights
 * 
 *  Manages table updates, row interactions, and
 *  dynamic content updates for insights display.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - InsightsTable class
 * 
 *  Notes:
 *  - Handles age updates and confidence styling
 *  - Manages expandable row content
 */

import { config } from '../core/config.js';
import unifiedRefreshManager from '../core/unifiedRefresh.js';
import { calculateAge, formatEventTime, formatLevels, getConfidenceClass, formatTimestamp } from '../core/utils.js';
import { insightsService } from '../services/insights.js';

export class InsightsTable {
    constructor() {
        this.table = document.querySelector('table');
        this.initializeTableFeatures();
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    INITIALIZE TABLE FEATURES        │
     *  └─────────────────────────────────────┘
     *  Sets up table interactions and features
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    initializeTableFeatures() {
        this.initializeExpandableRows();
        this.initializeRowClickHandlers();
        this.updateConfidenceStyling();
        this.formatSpecialCells();
        
        // Register with unified refresh manager
        unifiedRefreshManager.register(this);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    INITIALIZE EXPANDABLE ROWS       │
     *  └─────────────────────────────────────┘
     *  Sets up expandable row functionality
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    initializeExpandableRows() {
        const rows = document.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const expandBtn = row.querySelector('.expand-btn');
            const contentCell = row.querySelector('.expandable-content');
            
            if (expandBtn && contentCell) {
                expandBtn.addEventListener('click', () => {
                    const isExpanded = expandBtn.classList.contains('expanded');
                    
                    if (isExpanded) {
                        expandBtn.classList.remove('expanded');
                        expandBtn.innerHTML = '<i class="bi bi-chevron-right"></i>';
                        contentCell.style.maxHeight = '2.5em';
                        contentCell.classList.remove('expanded');
                    } else {
                        expandBtn.classList.add('expanded');
                        expandBtn.innerHTML = '<i class="bi bi-chevron-down"></i>';
                        contentCell.style.maxHeight = 'none';
                        contentCell.classList.add('expanded');
                    }
                });
            }
        });
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    INITIALIZE ROW CLICK HANDLERS    │
     *  └─────────────────────────────────────┘
     *  Sets up row click navigation to detail pages
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    initializeRowClickHandlers() {
        const rows = document.querySelectorAll('tbody tr.insight-row, tbody tr');
        
        rows.forEach(row => {
            // Skip if row already has click handler
            if (row.dataset.clickHandler) return;
            
            row.addEventListener('click', (e) => {
                // Don't navigate if clicking on buttons or interactive elements
                if (e.target.closest('button, a, .expand-btn, .reset-ai-btn')) {
                    return;
                }
                
                // Get insight ID from data attribute or row position
                let insightId = row.dataset.insightId;
                
                // If no data-insight-id, try to get from dynamically created rows
                if (!insightId && row.querySelector('.reset-ai-btn')) {
                    insightId = row.querySelector('.reset-ai-btn').dataset.id;
                }
                
                if (insightId) {
                    window.location.href = `/insight/${insightId}`;
                }
            });
            
            // Mark as having click handler
            row.dataset.clickHandler = 'true';
        });
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      START AGE UPDATES              │
     *  └─────────────────────────────────────┘
     *  Starts automatic age updates
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */



    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │        UPDATE ALL AGES              │
     *  └─────────────────────────────────────┘
     *  Updates all age displays in the table
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    updateAllAges() {
        const ageCells = document.querySelectorAll('.age-text');
        
        ageCells.forEach(cell => {
            const timestamp = cell.getAttribute('data-time-posted');
            if (timestamp) {
                const age = calculateAge(timestamp);
                cell.textContent = age;
            }
        });
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    UPDATE CONFIDENCE STYLING        │
     *  └─────────────────────────────────────┘
     *  Updates confidence level styling
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    updateConfidenceStyling() {
        const rows = document.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const confidenceCell = row.querySelector('td:nth-child(4)');
            if (!confidenceCell) return;
            
            const confidence = parseInt(confidenceCell.textContent) || 0;
            const className = getConfidenceClass(confidence);
            
            // Apply class to row
            row.classList.remove(...Object.values(config.cssClasses.confidence));
            row.classList.add(className);
        });
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      FORMAT SPECIAL CELLS           │
     *  └─────────────────────────────────────┘
     *  Formats special cell content
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    formatSpecialCells() {
        // Format horizon cells
        const horizonCells = document.querySelectorAll('.horizon-cell');
        horizonCells.forEach(cell => {
            const data = cell.getAttribute('data-horizon');
            if (data) {
                try {
                    const horizonData = JSON.parse(data);
                    cell.innerHTML = formatEventTime(horizonData);
                } catch (e) {
                    console.error('Error parsing horizon data:', e);
                }
            }
        });
        
        // Format level cells
        const levelCells = document.querySelectorAll('.level-cell');
        levelCells.forEach(cell => {
            const data = cell.getAttribute('data-levels');
            if (data) {
                try {
                    const levelsData = JSON.parse(data);
                    cell.innerHTML = formatLevels(levelsData);
                } catch (e) {
                    console.error('Error parsing levels data:', e);
                }
            }
        });
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       UPDATE TABLE ROWS             │
     *  └─────────────────────────────────────┘
     *  Updates table with new insights data
     * 
     *  Parameters:
     *  - insights: Array of insights
     * 
     *  Returns:
     *  - None
     */
    async updateTableRows(insights) {
        const tbody = this.table?.querySelector('tbody');
        if (!tbody) return;
        
        // Only update if we have valid data
        if (!insights || !Array.isArray(insights)) {
            console.warn('updateTableRows: Invalid insights data received, keeping existing table');
            return;
        }
        
        // Don't clear table if no insights returned (might be a failed refresh)
        if (insights.length === 0) {
            console.info('updateTableRows: No insights returned, keeping existing table');
            return;
        }
        
        // Smart update: preserve existing rows and update only changed data
        const existingRows = new Map();
        tbody.querySelectorAll('tr').forEach(row => {
            const insightId = row.dataset.insightId;
            if (insightId) {
                existingRows.set(parseInt(insightId), row);
            }
        });
        
        // Update or add rows
        insights.forEach(insight => {
            const existingRow = existingRows.get(insight.id);
            
            if (existingRow) {
                // Update existing row
                this.updateExistingRow(existingRow, insight);
                existingRows.delete(insight.id); // Mark as processed
            } else {
                // Add new row
                const newRow = this.createInsightRow(insight);
                tbody.appendChild(newRow);
            }
        });
        
        // Remove rows that no longer exist in the data
        existingRows.forEach(row => {
            row.remove();
        });
        
        // Reinitialize features for new rows only
        this.initializeTableFeatures();
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      UPDATE EXISTING ROW            │
     *  └─────────────────────────────────────┘
     *  Updates an existing table row with new data
     * 
     *  Parameters:
     *  - row: Existing TR element
     *  - insight: Updated insight data
     * 
     *  Returns:
     *  - None
     */
    updateExistingRow(row, insight) {
        // Update symbol
        const symbolCell = row.querySelector('td:nth-child(1)');
        if (symbolCell) {
            symbolCell.textContent = insight.symbol || '-';
        }
        
        // Update type (preserve icon)
        const typeCell = row.querySelector('td:nth-child(2)');
        if (typeCell) {
            typeCell.innerHTML = `${this.getTypeIcon(insight.type)} ${insight.type || '-'}`;
        }
        
        // Update age
        const ageCell = row.querySelector('.age-cell');
        if (ageCell) {
            ageCell.setAttribute('data-timestamp', insight.timePosted);
            ageCell.textContent = calculateAge(insight.timePosted);
        }
        
        // Update confidence
        const confidenceCell = row.querySelector('td:nth-child(4)');
        if (confidenceCell) {
            confidenceCell.textContent = insight.confidence || '-';
            // Update confidence styling
            row.classList.remove(...Object.values(config.cssClasses.confidence));
            const confidenceClass = getConfidenceClass(insight.confidence);
            row.classList.add(confidenceClass);
        }
        
        // Update horizon
        const horizonCell = row.querySelector('.horizon-cell');
        if (horizonCell) {
            horizonCell.setAttribute('data-horizon', JSON.stringify(insight.event_time || {}));
            horizonCell.innerHTML = formatEventTime(insight.event_time);
        }
        
        // Update levels
        const levelCell = row.querySelector('.level-cell');
        if (levelCell) {
            levelCell.setAttribute('data-levels', JSON.stringify(insight.levels || {}));
            levelCell.innerHTML = formatLevels(insight.levels);
        }
        
        // Update AI analysis
        const aiCell = row.querySelector('.ai-analysis-cell');
        if (aiCell) {
            aiCell.innerHTML = this.formatAIAnalysis(insight);
        }
        
        // Update content (if expandable)
        const contentCell = row.querySelector('.expandable-content');
        if (contentCell) {
            contentCell.innerHTML = this.formatContent(insight);
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      CREATE INSIGHT ROW             │
     *  └─────────────────────────────────────┘
     *  Creates a table row for an insight
     * 
     *  Parameters:
     *  - insight: Insight object
     * 
     *  Returns:
     *  - TR element
     */
    createInsightRow(insight) {
        const row = document.createElement('tr');
        const confidenceClass = getConfidenceClass(insight.confidence);
        row.className = `insight-row ${confidenceClass}`;
        row.dataset.insightId = insight.id;
        
        // Build row HTML
        row.innerHTML = `
            <td>${insight.symbol || '-'}</td>
            <td>${this.getTypeIcon(insight.type)} ${insight.type || '-'}</td>
            <td class="age-cell" data-timestamp="${insight.timePosted}">${calculateAge(insight.timePosted)}</td>
            <td>${insight.confidence || '-'}</td>
            <td class="horizon-cell" data-horizon='${JSON.stringify(insight.event_time || {})}'>
                ${formatEventTime(insight.event_time)}
            </td>
            <td class="level-cell" data-levels='${JSON.stringify(insight.levels || {})}'>
                ${formatLevels(insight.levels)}
            </td>
            <td>
                <button class="btn btn-sm btn-link expand-btn">
                    <i class="bi bi-chevron-right"></i>
                </button>
            </td>
            <td class="expandable-content">${this.formatContent(insight)}</td>
            <td class="ai-analysis-cell">${this.formatAIAnalysis(insight)}</td>
            <td>
                <button class="btn btn-sm btn-outline-secondary reset-ai-btn" data-id="${insight.id}">
                    Reset AI
                </button>
            </td>
        `;
        
        return row;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         GET TYPE ICON               │
     *  └─────────────────────────────────────┘
     *  Gets icon for insight type
     * 
     *  Parameters:
     *  - type: Insight type
     * 
     *  Returns:
     *  - Icon HTML
     */
    getTypeIcon(type) {
        const iconMap = {
            'TD NEWS': config.icons.news,
            'TD IDEAS RECENT': config.icons.ideas,
            'TD IDEAS POPULAR': config.icons.ideas,
            'TD OPINIONS': config.icons.opinions
        };
        
        const iconClass = iconMap[type] || 'bi-circle';
        return `<i class="bi ${iconClass}"></i>`;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       FORMAT CONTENT                │
     *  └─────────────────────────────────────┘
     *  Formats insight content for display
     * 
     *  Parameters:
     *  - insight: Insight object
     * 
     *  Returns:
     *  - Formatted HTML
     */
    formatContent(insight) {
        const parts = [];
        
        if (insight.title) {
            parts.push(`<strong>${insight.title}</strong>`);
        }
        
        if (insight.content) {
            parts.push(insight.content);
        }
        
        if (insight.url) {
            parts.push(`<a href="${insight.url}" target="_blank" class="text-primary">View Source</a>`);
        }
        
        return parts.join('<br>') || '-';
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      FORMAT AI ANALYSIS             │
     *  └─────────────────────────────────────┘
     *  Formats AI analysis data for display
     * 
     *  Parameters:
     *  - insight: Insight object
     * 
     *  Returns:
     *  - Formatted HTML
     */
    formatAIAnalysis(insight) {
        if (!insight.ai_analysis_status || insight.ai_analysis_status === 'pending') {
            return '<span class="text-muted">Pending</span>';
        }
        
        if (insight.ai_analysis_status === 'error') {
            return '<span class="text-danger">Error</span>';
        }
        
        if (insight.ai_analysis_status === 'completed' && insight.ai_summary) {
            const summary = insight.ai_summary;
            return `
                <div class="ai-summary">
                    <div><strong>Direction:</strong> ${summary.direction || '-'}</div>
                    <div><strong>Confidence:</strong> ${summary.confidence || '-'}/10</div>
                    <div><strong>Summary:</strong> ${summary.summary || '-'}</div>
                </div>
            `;
        }
        
        return '<span class="text-info">Processing...</span>';
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         STOP UPDATES                │
     *  └─────────────────────────────────────┘
     *  Stops all update intervals
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    stopUpdates() {
        // Unregister from unified refresh manager
        unifiedRefreshManager.unregister(this);
    }
}
