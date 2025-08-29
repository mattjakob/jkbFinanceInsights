/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        SYMBOL SEARCH                │
 *  └─────────────────────────────────────┘
 *  TradingView-inspired symbol search with autocomplete
 * 
 *  Provides real-time symbol search using TradingView API
 *  with minimal, console-inspired dropdown interface.
 * 
 *  Parameters:
 *  - inputElement: Symbol input element
 *  - exchangeElement: Exchange input element (optional)
 * 
 *  Returns:
 *  - SymbolSearch class instance
 * 
 *  Notes:
 *  - Uses real TradingView symbol search API
 *  - Auto-populates exchange field with most popular exchange
 *  - Supports both keyboard and mouse interaction
 */

import { debounce } from '../core/utils.js';

export class SymbolSearch {
    constructor(inputElement, exchangeElement = null) {
        this.input = inputElement;
        this.exchangeInput = exchangeElement || document.getElementById('exchangeInput');
        this.dropdown = null;
        this.selectedIndex = -1;
        this.suggestions = [];
        this.isLoading = false;
        this.symbolUpdateTimeout = null;
        
        if (this.input) {
            this.initialize();
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         INITIALIZE                  │
     *  └─────────────────────────────────────┘
     *  Initializes symbol search functionality
     */
    initialize() {
        this.createDropdown();
        this.setupEventListeners();
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       CREATE DROPDOWN               │
     *  └─────────────────────────────────────┘
     *  Creates the autocomplete dropdown element
     */
    createDropdown() {
        // Use existing dropdown or create new one
        this.dropdown = document.getElementById('symbolAutocomplete');
        
        if (!this.dropdown) {
            this.dropdown = document.createElement('div');
            this.dropdown.id = 'symbolAutocomplete';
            this.dropdown.className = 'autocomplete-dropdown';
            
            const container = this.input.closest('.symbol-autocomplete-container');
            if (container) {
                container.appendChild(this.dropdown);
            } else {
                this.input.parentNode.appendChild(this.dropdown);
            }
        }
        
        this.dropdown.style.display = 'none';
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       SETUP EVENT LISTENERS         │
     *  └─────────────────────────────────────┘
     *  Sets up all event handlers for the component
     */
    setupEventListeners() {
        // Debounced input handler for search
        const debounceDelay = window.AppConfig?.app_symbol_search_debounce || 200;
        const debouncedSearch = debounce((e) => this.handleSearch(e), debounceDelay);
        
        this.input.addEventListener('input', debouncedSearch);
        this.input.addEventListener('focus', (e) => this.handleFocus(e));
        this.input.addEventListener('blur', (e) => this.handleBlur(e));
        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
        
        // Handle clicks outside to close dropdown
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.dropdown.contains(e.target)) {
                this.hideDropdown();
            }
        });
        
        // Add change listeners to update TradingView chart when inputs change
        this.input.addEventListener('change', () => {
            this.updateTradingViewChart();
            this.updateSymbolFilter();
        });
        if (this.exchangeInput) {
            this.exchangeInput.addEventListener('change', () => {
                this.updateTradingViewChart();
                this.updateSymbolFilter();
            });
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         HANDLE SEARCH               │
     *  └─────────────────────────────────────┘
     *  Handles symbol search input
     */
    async handleSearch(event) {
        const query = event.target.value.trim().toUpperCase();
        
        if (query.length < 1) {
            this.hideDropdown();
            return;
        }
        
        if (query.length < 2) {
            
            return;
        }
        
        this.isLoading = true;
        this.showLoadingState();
        
        try {
            const response = await fetch(`/api/scraping/symbols/search?query=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.suggestions && data.suggestions.length > 0) {
                this.suggestions = data.suggestions;
                this.selectedIndex = -1;
                this.showSuggestions(this.suggestions);
            } else {
                this.suggestions = [];
                this.showNoResults();
            }
        } catch (error) {
            if (window.Debugger) {
                window.Debugger.error('Symbol search error:', error);
            }
            this.suggestions = [];
            this.showError();
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         HANDLE FOCUS                │
     *  └─────────────────────────────────────┘
     *  Handles input focus - shows dropdown if has suggestions
     */
    handleFocus(event) {
        const query = event.target.value.trim();
        if (query.length >= 2 && this.suggestions.length > 0) {
            this.showSuggestions(this.suggestions);
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         HANDLE BLUR                 │
     *  └─────────────────────────────────────┘
     *  Handles input blur - hides dropdown with delay
     */
    handleBlur(event) {
        // Delay hiding to allow for dropdown clicks
        setTimeout(() => {
            if (!this.dropdown.matches(':hover')) {
                this.hideDropdown();
            }
        }, 150);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │        HANDLE KEYDOWN               │
     *  └─────────────────────────────────────┘
     *  Handles keyboard navigation in dropdown
     */
    handleKeydown(event) {
        if (!this.dropdown || this.dropdown.style.display === 'none' || this.suggestions.length === 0) {
            return;
        }

        switch (event.key) {
            case 'ArrowDown':
                event.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, this.suggestions.length - 1);
                this.updateSelection();
                break;
                
            case 'ArrowUp':
                event.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, -1);
                this.updateSelection();
                break;
                
            case 'Enter':
                event.preventDefault();
                if (this.selectedIndex >= 0) {
                    this.selectSuggestion(this.suggestions[this.selectedIndex]);
                }
                break;
                
            case 'Escape':
                this.hideDropdown();
                this.input.blur();
                break;
                
            case 'Tab':
                // Allow tab to work normally but hide dropdown
                this.hideDropdown();
                break;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       SHOW SUGGESTIONS              │
     *  └─────────────────────────────────────┘
     *  Displays the suggestion dropdown with results
     */
    showSuggestions(suggestions) {
        if (!suggestions || suggestions.length === 0) {
            this.hideDropdown();
            return;
        }
        
        this.dropdown.innerHTML = suggestions.map((suggestion, index) => `
            <div class="autocomplete-item" data-index="${index}">
                <div class="autocomplete-item-content">
                    <span class="symbol">${suggestion.symbol}</span>
                    <span class="description">${suggestion.description}</span>
                </div>
                <span class="exchange">${suggestion.exchange}</span>
            </div>
        `).join('');
        
        // Add click handlers
        this.dropdown.querySelectorAll('.autocomplete-item').forEach((item, index) => {
            item.addEventListener('mousedown', (e) => {
                e.preventDefault();
                this.selectSuggestion(suggestions[index]);
            });
            
            item.addEventListener('mouseenter', () => {
                this.selectedIndex = index;
                this.updateSelection();
            });
            
            item.addEventListener('mouseleave', () => {
                this.selectedIndex = -1;
                this.updateSelection();
            });
        });
        
        this.dropdown.style.display = 'block';
        this.dropdown.classList.add('show');
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       SHOW LOADING STATE            │
     *  └─────────────────────────────────────┘
     *  Shows loading indicator in dropdown
     */
    showLoadingState() {
        this.dropdown.innerHTML = `
            <div class="autocomplete-loading">
                <span>Searching symbols...</span>
            </div>
        `;
        this.dropdown.style.display = 'block';
        this.dropdown.classList.add('show');
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       SHOW NO RESULTS               │
     *  └─────────────────────────────────────┘
     *  Shows no results message
     */
    showNoResults() {
        this.dropdown.innerHTML = `
            <div class="autocomplete-no-results">
                <span>No symbols found</span>
            </div>
        `;
        this.dropdown.style.display = 'block';
        this.dropdown.classList.add('show');
        
        // Auto-hide after delay
        setTimeout(() => this.hideDropdown(), 2000);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         SHOW ERROR                  │
     *  └─────────────────────────────────────┘
     *  Shows error message in dropdown
     */
    showError() {
        this.dropdown.innerHTML = `
            <div class="autocomplete-no-results">
                <span>Search failed - try again</span>
            </div>
        `;
        this.dropdown.style.display = 'block';
        this.dropdown.classList.add('show');
        
        // Auto-hide after delay
        setTimeout(() => this.hideDropdown(), 3000);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         HIDE DROPDOWN               │
     *  └─────────────────────────────────────┘
     *  Hides the suggestion dropdown
     */
    hideDropdown() {
        if (this.dropdown) {
            this.dropdown.style.display = 'none';
            this.dropdown.classList.remove('show');
        }
        this.selectedIndex = -1;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       UPDATE SELECTION              │
     *  └─────────────────────────────────────┘
     *  Updates visual selection highlighting in dropdown
     */
    updateSelection() {
        const items = this.dropdown.querySelectorAll('.autocomplete-item');
        items.forEach((item, index) => {
            if (index === this.selectedIndex) {
                item.classList.add('highlighted');
                item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            } else {
                item.classList.remove('highlighted');
            }
        });
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       SELECT SUGGESTION             │
     *  └─────────────────────────────────────┘
     *  Handles selection of a suggestion from dropdown
     */
    selectSuggestion(suggestion) {
        // Update symbol input
        this.input.value = suggestion.symbol;
        
        // Auto-populate exchange field
        if (this.exchangeInput && suggestion.exchange) {
            this.exchangeInput.value = suggestion.exchange;
        }
        
        // Hide dropdown and update validation
        this.hideDropdown();
        this.setValidationIcon('valid');
        
        // Trigger change events for other components
        this.input.dispatchEvent(new Event('change', { bubbles: true }));
        if (this.exchangeInput) {
            this.exchangeInput.dispatchEvent(new Event('change', { bubbles: true }));
        }
        
        // Focus exchange input if empty, otherwise blur
        if (this.exchangeInput && !this.exchangeInput.value.trim()) {
            this.exchangeInput.focus();
        } else {
            this.input.blur();
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      SET VALIDATION ICON            │
     *  └─────────────────────────────────────┘
     *  Updates the validation icon state
     */
    setValidationIcon(state) {
        if (!this.validationIcon) return;
        
        const iconClasses = {
            search: 'bi bi-search',
            loading: 'bi bi-arrow-clockwise',
            valid: 'bi bi-check',
            invalid: 'bi bi-x',
            error: 'bi bi-exclamation-triangle'
        };
        
        const iconClass = iconClasses[state] || 'bi bi-search';
        this.validationIcon.className = iconClass;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         GET CURRENT VALUE           │
     *  └─────────────────────────────────────┘
     *  Returns current symbol and exchange values
     */
    getCurrentValues() {
        return {
            symbol: this.input.value.trim().toUpperCase(),
            exchange: this.exchangeInput ? this.exchangeInput.value.trim().toUpperCase() : ''
        };
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         SET VALUES                  │
     *  └─────────────────────────────────────┘
     *  Sets symbol and exchange values programmatically
     */
    setValues(symbol, exchange = '') {
        this.input.value = symbol.toUpperCase();
        if (this.exchangeInput && exchange) {
            this.exchangeInput.value = exchange.toUpperCase();
        }
        this.setValidationIcon(symbol ? 'valid' : 'search');
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      UPDATE TRADINGVIEW CHART       │
     *  └─────────────────────────────────────┘
     *  Updates the TradingView chart with current symbol and exchange
     */
    updateTradingViewChart() {
        if (window.TradingViewChart && window.TradingViewChart.updateFromInputs) {
            window.TradingViewChart.updateFromInputs();
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       UPDATE SYMBOL FILTER          │
     *  └─────────────────────────────────────┘
     *  Updates the table filtering based on symbol input
     * 
     *  Uses path-based routing to navigate to filtered views.
     */
    updateSymbolFilter() {
        const currentValues = this.getCurrentValues();
        const symbol = currentValues.symbol;
        const exchange = currentValues.exchange;
        
        // Get current type filter from page
        const typeFilter = document.getElementById('typeFilter')?.value || '';
        
        // Build new URL path using EXCHANGE:SYMBOL format
        let newPath = '/';
        if (symbol && exchange) {
            const exchangeSymbol = `${exchange}:${symbol}`;
            newPath = `/api/insights/${exchangeSymbol}`;
            if (typeFilter) {
                // Replace spaces with underscores for URL
                const urlSafeType = typeFilter.replace(/\s+/g, '_');
                newPath = `/api/insights/${exchangeSymbol}/${urlSafeType}`;
            }
        } else if (symbol) {
            // Fallback to just symbol if no exchange
            newPath = `/api/insights/${symbol}`;
            if (typeFilter) {
                // Replace spaces with underscores for URL
                const urlSafeType = typeFilter.replace(/\s+/g, '_');
                newPath = `/api/insights/${symbol}/${urlSafeType}`;
            }
        } else if (typeFilter) {
            // If no symbol but type is selected, don't navigate
            return;
        }
        
        // Get current path
        const currentPath = window.location.pathname;
        
        // Only navigate if path has changed
        if (newPath !== currentPath) {
            this.debounceSymbolUpdate(newPath);
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │     DEBOUNCE SYMBOL UPDATE          │
     *  └─────────────────────────────────────┘
     *  Debounces symbol filter updates to avoid rapid page reloads
     */
    debounceSymbolUpdate(newPath) {
        // Clear existing timeout
        if (this.symbolUpdateTimeout) {
            clearTimeout(this.symbolUpdateTimeout);
        }
        
        // Set new timeout
        const filterDelay = window.AppConfig?.app_symbol_filter_delay || 800;
        this.symbolUpdateTimeout = setTimeout(() => {
            window.location.href = newPath;
        }, filterDelay); // Configurable delay to allow for rapid typing
    }
}