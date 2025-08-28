/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        TASK INDICATOR               │
 *  └─────────────────────────────────────┘
 *  Minimal task status indicator
 * 
 *  Displays running, queued, and failed task counts
 *  in a compact, minimal format.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - TaskIndicator class
 * 
 *  Notes:
 *  - Shows counts for active and failed tasks
 *  - Updates automatically every 5 seconds
 *  - Minimal visual footprint
 */

import { tasksService } from '../services/tasks.js';

export class TaskIndicator {
    constructor() {
        this.element = null;
        this.updateInterval = null;
        this.initialize();
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         INITIALIZE                  │
     *  └─────────────────────────────────────┘
     *  Initializes the task indicator
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    initialize() {
        this.createIndicator();
        this.startUpdates();
        
        // Initial fetch
        this.updateDisplay();
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      CREATE INDICATOR               │
     *  └─────────────────────────────────────┘
     *  Creates the task indicator element
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    createIndicator() {
        // Create indicator container
        this.element = document.createElement('div');
        this.element.className = 'task-indicator';
        
        // Create content
        this.element.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="color: #6c757d;">TASKS</span>
                <span class="task-counts"></span>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(this.element);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         START UPDATES               │
     *  └─────────────────────────────────────┘
     *  Starts automatic updates
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    startUpdates() {
        // Start task service updates
        tasksService.startAutoUpdates(5000);
        
        // Update display every 2 seconds
        this.updateInterval = setInterval(() => {
            this.updateDisplay();
        }, 2000);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       UPDATE DISPLAY                │
     *  └─────────────────────────────────────┘
     *  Updates the task indicator display
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    updateDisplay() {
        const stats = tasksService.getCurrentStats();
        const countsElement = this.element.querySelector('.task-counts');
        
        if (!countsElement) return;
        
        // Format counts
        const running = stats.processing;
        const queued = stats.pending;
        const failed = stats.failed;
        
        // Create formatted string
        let countsHtml = '';
        
        if (running > 0) {
            countsHtml += `<span style="color: #28a745;">⚡${running}</span>`;
        }
        
        if (queued > 0) {
            if (countsHtml) countsHtml += ' ';
            countsHtml += `<span style="color: #ffc107;">⏳${queued}</span>`;
        }
        
        if (failed > 0) {
            if (countsHtml) countsHtml += ' ';
            countsHtml += `<span style="color: #dc3545;">❌${failed}</span>`;
        }
        
        // Show "idle" if no active tasks
        if (!running && !queued && !failed) {
            countsHtml = '<span style="color: #6c757d;">idle</span>';
        }
        
        countsElement.innerHTML = countsHtml;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         STOP UPDATES                │
     *  └─────────────────────────────────────┘
     *  Stops automatic updates
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    stopUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        tasksService.stopAutoUpdates();
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │           DESTROY                   │
     *  └─────────────────────────────────────┘
     *  Cleans up the component
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    destroy() {
        this.stopUpdates();
        
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}
