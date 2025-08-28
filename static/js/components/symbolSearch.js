/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        SYMBOL SEARCH                │
 *  └─────────────────────────────────────┘
 *  Symbol search and validation component
 * 
 *  Provides symbol search suggestions and validation
 *  functionality for the symbol input field.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - SymbolSearch class
 * 
 *  Notes:
 *  - Currently uses mock data until API is available
 *  - Will be updated when symbol API is implemented
 */

import { debounce } from '../core/utils.js';

export class SymbolSearch {
    constructor(inputElement) {
        this.input = inputElement;
        this.dropdown = null;
        this.validationIcon = null;
        
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
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    initialize() {
        // Create dropdown container
        this.createDropdown();
        
        // Create validation icon
        this.createValidationIcon();
        
        // Set up event listeners
        this.input.addEventListener('input', debounce((e) => this.handleInput(e), 300));
        this.input.addEventListener('blur', () => this.hideDropdown());
        this.input.addEventListener('focus', (e) => this.handleInput(e));
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       CREATE DROPDOWN               │
     *  └─────────────────────────────────────┘
     *  Creates dropdown for search results
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    createDropdown() {
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'symbol-dropdown dropdown-menu';
        this.dropdown.style.display = 'none';
        this.dropdown.style.position = 'absolute';
        this.dropdown.style.width = '100%';
        
        // Insert after input
        this.input.parentNode.style.position = 'relative';
        this.input.parentNode.appendChild(this.dropdown);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │     CREATE VALIDATION ICON          │
     *  └─────────────────────────────────────┘
     *  Creates validation status icon
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    createValidationIcon() {
        const wrapper = document.createElement('div');
        wrapper.style.position = 'relative';
        
        this.validationIcon = document.createElement('span');
        this.validationIcon.className = 'symbol-validation-icon';
        this.validationIcon.style.cssText = 'position: absolute; right: 10px; top: 50%; transform: translateY(-50%);';
        
        // Wrap input
        this.input.parentNode.insertBefore(wrapper, this.input);
        wrapper.appendChild(this.input);
        wrapper.appendChild(this.validationIcon);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         HANDLE INPUT                │
     *  └─────────────────────────────────────┘
     *  Handles input changes
     * 
     *  Parameters:
     *  - event: Input event
     * 
     *  Returns:
     *  - None
     */
    async handleInput(event) {
        const query = event.target.value.trim();
        
        if (query.length < 1) {
            this.hideDropdown();
            this.setValidationIcon('');
            return;
        }
        
        // Show loading state
        this.setValidationIcon('loading');
        
        try {
            // Mock symbol search until API is available
            const suggestions = this.getMockSuggestions(query);
            this.showSuggestions(suggestions);
            
            // Validate symbol
            if (query.length >= 2) {
                const isValid = this.validateSymbol(query);
                this.setValidationIcon(isValid ? 'valid' : 'invalid');
            }
        } catch (error) {
            console.error('Symbol search error:', error);
            this.hideDropdown();
            this.setValidationIcon('error');
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      GET MOCK SUGGESTIONS           │
     *  └─────────────────────────────────────┘
     *  Returns mock suggestions for testing
     * 
     *  Parameters:
     *  - query: Search query
     * 
     *  Returns:
     *  - Array of suggestions
     */
    getMockSuggestions(query) {
        const symbols = [
            { symbol: 'BTCUSD', description: 'Bitcoin / US Dollar' },
            { symbol: 'ETHUSD', description: 'Ethereum / US Dollar' },
            { symbol: 'AAPL', description: 'Apple Inc.' },
            { symbol: 'GOOGL', description: 'Alphabet Inc.' },
            { symbol: 'MSFT', description: 'Microsoft Corporation' },
            { symbol: 'TSLA', description: 'Tesla Inc.' },
            { symbol: 'AMZN', description: 'Amazon.com Inc.' },
            { symbol: 'NVDA', description: 'NVIDIA Corporation' }
        ];
        
        return symbols.filter(s => 
            s.symbol.toLowerCase().includes(query.toLowerCase()) ||
            s.description.toLowerCase().includes(query.toLowerCase())
        ).slice(0, 8);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       VALIDATE SYMBOL               │
     *  └─────────────────────────────────────┘
     *  Validates if symbol is valid
     * 
     *  Parameters:
     *  - symbol: Symbol to validate
     * 
     *  Returns:
     *  - Boolean
     */
    validateSymbol(symbol) {
        // Mock validation - just check if it's alphanumeric and 2-10 chars
        return /^[A-Z0-9]{2,10}$/.test(symbol.toUpperCase());
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       SHOW SUGGESTIONS              │
     *  └─────────────────────────────────────┘
     *  Shows suggestion dropdown
     * 
     *  Parameters:
     *  - suggestions: Array of suggestions
     * 
     *  Returns:
     *  - None
     */
    showSuggestions(suggestions) {
        if (!suggestions.length) {
            this.hideDropdown();
            return;
        }
        
        this.dropdown.innerHTML = suggestions.map(s => `
            <a class="dropdown-item symbol-suggestion" href="#" data-symbol="${s.symbol}">
                <strong>${s.symbol}</strong> - ${s.description}
            </a>
        `).join('');
        
        // Add click handlers
        this.dropdown.querySelectorAll('.symbol-suggestion').forEach(item => {
            item.addEventListener('mousedown', (e) => {
                e.preventDefault();
                this.input.value = e.currentTarget.dataset.symbol;
                this.hideDropdown();
                this.setValidationIcon('valid');
            });
        });
        
        this.dropdown.style.display = 'block';
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         HIDE DROPDOWN               │
     *  └─────────────────────────────────────┘
     *  Hides suggestion dropdown
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    hideDropdown() {
        if (this.dropdown) {
            this.dropdown.style.display = 'none';
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      SET VALIDATION ICON            │
     *  └─────────────────────────────────────┘
     *  Sets validation icon state
     * 
     *  Parameters:
     *  - state: Icon state
     * 
     *  Returns:
     *  - None
     */
    setValidationIcon(state) {
        if (!this.validationIcon) return;
        
        const icons = {
            loading: '<i class="spinner-border spinner-border-sm text-info"></i>',
            valid: '<i class="bi bi-check-circle-fill text-success"></i>',
            invalid: '<i class="bi bi-x-circle-fill text-danger"></i>',
            error: '<i class="bi bi-exclamation-circle-fill text-warning"></i>',
            '': ''
        };
        
        this.validationIcon.innerHTML = icons[state] || '';
    }
}



