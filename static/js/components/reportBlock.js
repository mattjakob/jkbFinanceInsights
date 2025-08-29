/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         REPORT BLOCK                │
 *  └─────────────────────────────────────┘
 *  Component for displaying AI analysis reports
 * 
 *  Manages the report block UI, fetching and displaying
 *  report data for the current symbol.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - ReportBlock class
 * 
 *  Notes:
 *  - Auto-loads report for current symbol
 *  - Updates when symbol changes
 *  - Shows/hides based on report availability
 */

import { reportsService } from '../services/reports.js';
import unifiedRefreshManager from '../core/unifiedRefresh.js';

export class ReportBlock {
    constructor() {
        this.reportBlock = document.getElementById('reportBlock');
        this.reportSymbol = document.getElementById('reportSymbol');
        this.currentSymbol = null;
        
        // Field elements
        this.fields = {
            timeFetched: document.getElementById('reportTimeFetched'),
            aiSummary: document.getElementById('reportAISummary'),
            aiAction: document.getElementById('reportAIAction'),
            aiConfidence: document.getElementById('reportAIConfidence'),
            aiEventTime: document.getElementById('reportAIEventTime'),
            aiLevels: document.getElementById('reportAILevels'),
            aiAnalysisStatus: document.getElementById('reportAIAnalysisStatus')
        };
        
        this.initialize();
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │          INITIALIZE                 │
     *  └─────────────────────────────────────┘
     *  Initializes the report block
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    initialize() {
        // Register with unified refresh manager
        unifiedRefreshManager.register(this);
        
        // Get current symbol from URL or UI
        this.currentSymbol = this.getCurrentSymbol();
        
        if (this.currentSymbol) {
            this.loadReport(this.currentSymbol);
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      GET CURRENT SYMBOL             │
     *  └─────────────────────────────────────┘
     *  Gets the current symbol from URL or UI
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Symbol string or null
     */
    getCurrentSymbol() {
        // Check URL path first
        const pathParts = window.location.pathname.split('/').filter(p => p);
        if (pathParts.length >= 3 && pathParts[0] === 'api' && pathParts[1] === 'insights') {
            const exchangeSymbol = pathParts[2];
            if (exchangeSymbol.includes(':')) {
                return exchangeSymbol.split(':')[1];
            }
            return exchangeSymbol;
        }
        
        // Check symbol input
        const symbolInput = document.getElementById('symbolInput');
        if (symbolInput && symbolInput.value) {
            return symbolInput.value.toUpperCase();
        }
        
        return null;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         LOAD REPORT                 │
     *  └─────────────────────────────────────┘
     *  Loads and displays report for a symbol
     * 
     *  Parameters:
     *  - symbol: Trading symbol
     * 
     *  Returns:
     *  - Promise
     */
    async loadReport(symbol) {
        try {
            const report = await reportsService.getLatestReportBySymbol(symbol);
            
            if (report) {
                this.displayReport(report);
                this.showBlock();
            } else {
                this.hideBlock();
            }
        } catch (error) {
            console.error('Error loading report:', error);
            this.hideBlock();
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       DISPLAY REPORT                │
     *  └─────────────────────────────────────┘
     *  Displays report data in the UI
     * 
     *  Parameters:
     *  - report: Report object
     * 
     *  Returns:
     *  - None
     */
    displayReport(report) {
        // Update symbol
        this.reportSymbol.textContent = report.symbol;
        
        // Format and display report data
        const formatted = reportsService.formatReportForUI(report);
        
        // Update fields
        this.fields.timeFetched.textContent = formatted.timeFetchedFormatted;
        this.fields.aiSummary.textContent = report.AISummary;
        
        // Action with styling
        this.fields.aiAction.textContent = report.AIAction;
        this.fields.aiAction.className = `field-value action-badge ${formatted.actionClass}`;
        
        // Confidence with styling
        this.fields.aiConfidence.textContent = `${formatted.confidencePercent}%`;
        this.fields.aiConfidence.className = `field-value confidence-badge ${formatted.confidenceClass}`;
        
        // Event time
        this.fields.aiEventTime.textContent = report.AIEventTime || '-';
        
        // Levels
        this.fields.aiLevels.textContent = report.AILevels || '-';
        
        // Status
        this.fields.aiAnalysisStatus.textContent = report.AIAnalysisStatus;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         SHOW BLOCK                  │
     *  └─────────────────────────────────────┘
     *  Shows the report block
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    showBlock() {
        this.reportBlock.classList.remove('d-none');
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         HIDE BLOCK                  │
     *  └─────────────────────────────────────┘
     *  Hides the report block
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    hideBlock() {
        this.reportBlock.classList.add('d-none');
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       UPDATE SYMBOL                 │
     *  └─────────────────────────────────────┘
     *  Updates the report for a new symbol
     * 
     *  Parameters:
     *  - symbol: New trading symbol
     * 
     *  Returns:
     *  - Promise
     */
    async updateSymbol(symbol) {
        if (symbol && symbol !== this.currentSymbol) {
            this.currentSymbol = symbol;
            await this.loadReport(symbol);
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │          REFRESH                    │
     *  └─────────────────────────────────────┘
     *  Refreshes the current report
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Promise
     */
    async refresh() {
        if (this.currentSymbol) {
            await this.loadReport(this.currentSymbol);
        }
    }
}
