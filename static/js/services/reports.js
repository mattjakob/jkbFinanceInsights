/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         REPORTS SERVICE             │
 *  └─────────────────────────────────────┘
 *  Service for managing AI analysis reports
 * 
 *  Handles all client-side operations for reports including
 *  creating, fetching, updating, and deleting reports.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - ReportsService singleton instance
 * 
 *  Notes:
 *  - Uses apiClient for backend communication
 *  - Handles error states gracefully
 *  - Caches latest report per symbol
 */

import { apiClient } from '../core/api.js';

class ReportsService {
    constructor() {
        this.cache = new Map(); // Cache latest report per symbol
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         CREATE REPORT               │
     *  └─────────────────────────────────────┘
     *  Creates a new AI analysis report
     * 
     *  Parameters:
     *  - reportData: Object with report fields
     * 
     *  Returns:
     *  - Created report object
     */
    async createReport(reportData) {
        try {
            const response = await apiClient.post('/api/reports/', reportData);
            
            // Update cache with new report
            if (response.symbol) {
                this.cache.set(response.symbol, response);
            }
            
            Debugger.success(`Report created for ${response.symbol}`);
            return response;
        } catch (error) {
            Debugger.error(`Failed to create report: ${error.message}`);
            throw error;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       GET REPORT BY ID              │
     *  └─────────────────────────────────────┘
     *  Fetches a specific report by ID
     * 
     *  Parameters:
     *  - reportId: Report ID
     * 
     *  Returns:
     *  - Report object or null
     */
    async getReportById(reportId) {
        try {
            const response = await apiClient.get(`/api/reports/${reportId}`);
            return response;
        } catch (error) {
            if (error.status === 404) {
                return null;
            }
            Debugger.error(`Failed to fetch report: ${error.message}`);
            throw error;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │     GET REPORTS BY SYMBOL           │
     *  └─────────────────────────────────────┘
     *  Fetches all reports for a symbol
     * 
     *  Parameters:
     *  - symbol: Trading symbol
     *  - limit: Maximum number of reports
     * 
     *  Returns:
     *  - Array of report objects
     */
    async getReportsBySymbol(symbol, limit = 10) {
        try {
            const response = await apiClient.get(`/api/reports/symbol/${symbol}`, { 
                params: { limit } 
            });
            
            // Cache the latest report
            if (response.length > 0) {
                this.cache.set(symbol, response[0]);
            }
            
            return response;
        } catch (error) {
            Debugger.error(`Failed to fetch reports for ${symbol}: ${error.message}`);
            return [];
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │   GET LATEST REPORT BY SYMBOL       │
     *  └─────────────────────────────────────┘
     *  Fetches the most recent report for a symbol
     * 
     *  Parameters:
     *  - symbol: Trading symbol
     * 
     *  Returns:
     *  - Latest report object or null
     */
    async getLatestReportBySymbol(symbol) {
        try {
            // Check cache first
            if (this.cache.has(symbol)) {
                return this.cache.get(symbol);
            }
            
            const response = await apiClient.get(`/api/reports/symbol/${symbol}/latest`);
            
            // Update cache
            if (response) {
                this.cache.set(symbol, response);
            }
            
            return response;
        } catch (error) {
            Debugger.error(`Failed to fetch latest report for ${symbol}: ${error.message}`);
            return null;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         UPDATE REPORT               │
     *  └─────────────────────────────────────┘
     *  Updates an existing report
     * 
     *  Parameters:
     *  - reportId: Report ID
     *  - updates: Object with fields to update
     * 
     *  Returns:
     *  - Updated report object
     */
    async updateReport(reportId, updates) {
        try {
            const response = await apiClient.put(`/api/reports/${reportId}`, updates);
            
            // Update cache if needed
            if (response.symbol && this.cache.has(response.symbol)) {
                const cachedReport = this.cache.get(response.symbol);
                if (cachedReport.id === reportId) {
                    this.cache.set(response.symbol, response);
                }
            }
            
            Debugger.success(`Report ${reportId} updated`);
            return response;
        } catch (error) {
            Debugger.error(`Failed to update report: ${error.message}`);
            throw error;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         DELETE REPORT               │
     *  └─────────────────────────────────────┘
     *  Deletes a report
     * 
     *  Parameters:
     *  - reportId: Report ID
     * 
     *  Returns:
     *  - Success boolean
     */
    async deleteReport(reportId) {
        try {
            // Get report first to clear cache
            const report = await this.getReportById(reportId);
            
            await apiClient.delete(`/api/reports/${reportId}`);
            
            // Clear from cache
            if (report && report.symbol && this.cache.has(report.symbol)) {
                const cachedReport = this.cache.get(report.symbol);
                if (cachedReport.id === reportId) {
                    this.cache.delete(report.symbol);
                }
            }
            
            Debugger.success(`Report ${reportId} deleted`);
            return true;
        } catch (error) {
            Debugger.error(`Failed to delete report: ${error.message}`);
            return false;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    GET HIGH CONFIDENCE REPORTS      │
     *  └─────────────────────────────────────┘
     *  Fetches reports with high confidence
     * 
     *  Parameters:
     *  - minConfidence: Minimum confidence threshold
     *  - limit: Maximum number of reports
     * 
     *  Returns:
     *  - Array of high-confidence reports
     */
    async getHighConfidenceReports(minConfidence = 0.8, limit = 50) {
        try {
            const response = await apiClient.get(
                `/api/reports/high-confidence/${minConfidence}`,
                { params: { limit } }
            );
            return response;
        } catch (error) {
            Debugger.error(`Failed to fetch high confidence reports: ${error.message}`);
            return [];
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         CLEAR CACHE                 │
     *  └─────────────────────────────────────┘
     *  Clears the report cache
     * 
     *  Parameters:
     *  - symbol: Optional - clear specific symbol only
     * 
     *  Returns:
     *  - None
     */
    clearCache(symbol = null) {
        if (symbol) {
            this.cache.delete(symbol);
        } else {
            this.cache.clear();
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      FORMAT REPORT FOR UI           │
     *  └─────────────────────────────────────┘
     *  Formats report data for UI display
     * 
     *  Parameters:
     *  - report: Report object
     * 
     *  Returns:
     *  - Formatted report object
     */
    formatReportForUI(report) {
        if (!report) return null;
        
        return {
            ...report,
            confidencePercent: Math.round(report.AIConfidence * 100),
            timeFetchedFormatted: new Date(report.timeFetched).toLocaleString(),
            actionClass: this.getActionClass(report.AIAction),
            confidenceClass: this.getConfidenceClass(report.AIConfidence)
        };
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       GET ACTION CLASS              │
     *  └─────────────────────────────────────┘
     *  Gets CSS class for action type
     * 
     *  Parameters:
     *  - action: AI action (BUY, SELL, etc)
     * 
     *  Returns:
     *  - CSS class name
     */
    getActionClass(action) {
        const actionClasses = {
            'BUY': 'action-buy',
            'SELL': 'action-sell',
            'HOLD': 'action-hold',
            'WATCH': 'action-watch'
        };
        return actionClasses[action] || 'action-default';
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │     GET CONFIDENCE CLASS            │
     *  └─────────────────────────────────────┘
     *  Gets CSS class for confidence level
     * 
     *  Parameters:
     *  - confidence: Confidence value (0-1)
     * 
     *  Returns:
     *  - CSS class name
     */
    getConfidenceClass(confidence) {
        if (confidence >= 0.8) return 'confidence-high';
        if (confidence >= 0.6) return 'confidence-medium';
        return 'confidence-low';
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      CHECK REPORTS AVAILABLE        │
     *  └─────────────────────────────────────┘
     *  Checks if reports are available for a symbol
     * 
     *  Parameters:
     *  - symbol: Trading symbol to check
     * 
     *  Returns:
     *  - Boolean indicating if reports exist
     */
    async checkReportsAvailable(symbol) {
        if (!symbol) return false;
        
        try {
            // Check cache first
            if (this.cache.has(symbol)) {
                return true;
            }
            
            // Fetch from API if not in cache
            const reports = await this.getReportsBySymbol(symbol, 1);
            return reports && reports.length > 0;
        } catch (error) {
            console.error(`Error checking reports for ${symbol}:`, error);
            return false;
        }
    }
}

// Export singleton instance
const reportsService = new ReportsService();
export { reportsService };
