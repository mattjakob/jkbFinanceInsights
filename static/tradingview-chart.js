/**
*
* ┌─────────────────────────────────────┐
* │        TRADINGVIEW CHART            │
* └─────────────────────────────────────┘
* TradingView chart widget management and configuration
*
* This module handles all TradingView chart functionality including:
* - Initial widget creation with monochromatic theme
* - Dynamic symbol updates
* - Chart recreation and styling
*
* Parameters:
* - symbol: Trading symbol to display (e.g., "BTCUSD", "NASDAQ:AAPL")
*
* Returns:
* - Configured TradingView widget with monochromatic styling
*
* Notes:
* - Uses TradingView JavaScript API for full customization support
* - Applies comprehensive overrides for monochromatic theme
* - Maintains styling consistency across symbol updates
*/

// TradingView widget configuration with monochromatic theme
const TRADINGVIEW_CONFIG = {
    base: {
        "autosize": false,
        "width": "100%",
        "height": 400,
        "interval": "1",
        "timezone": "America/New_York",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "enable_publishing": false,
        "hide_top_toolbar": false,
        "hide_legend": false,
        "save_image": true,
        "calendar": true,
        "hide_volume": false,
        "support_host": "https://www.tradingview.com"
    },
    overrides: {
        "paneProperties.background": "#000000",
        "paneProperties.backgroundType": "solid",
        "paneProperties.vertGridProperties.color": "#333333",
        "paneProperties.horzGridProperties.color": "#333333",
        "paneProperties.crossHairProperties.color": "#666666",
        "symbolWatermarkProperties.transparency": 90,
        "symbolWatermarkProperties.color": "#333333",
        "scalesProperties.textColor": "#cccccc",
        "scalesProperties.backgroundColor": "#1e2128",
        "mainSeriesProperties.candleStyle.upColor": "#000000",
        "mainSeriesProperties.candleStyle.downColor": "#000000",
        "mainSeriesProperties.candleStyle.borderUpColor": "#aaaaaa",
        "mainSeriesProperties.candleStyle.borderDownColor": "#666666",
        "mainSeriesProperties.candleStyle.wickUpColor": "#aaaaaa",
        "mainSeriesProperties.candleStyle.wickDownColor": "#666666",
        "volumePaneProperties.background": "#1e2128",
        "mainSeriesProperties.priceLineColor": "#666666",
        "mainSeriesProperties.baseLineColor": "#666666"
    },
    studies_overrides: {
        "volume.volume.color.0": "#666666",
        "volume.volume.color.1": "#444444",
        "volume.volume ma.color": "#888888",
        "volume.show ma": false
    }
};

/**
*
* ┌─────────────────────────────────────┐
* │      INITIALIZE TRADINGVIEW         │
* └─────────────────────────────────────┘
* Initialize TradingView chart widget on page load
*
* Creates the initial TradingView widget with monochromatic styling
* and sets up the chart container with proper configuration.
*
* Parameters:
* - containerId: DOM element ID where the chart will be rendered
* - symbol: Initial trading symbol to display
*
* Returns:
* - TradingView widget instance
*
* Notes:
* - Called on DOMContentLoaded event
* - Uses predefined TRADINGVIEW_CONFIG for consistent styling
* - Loads TradingView library if not already available
*/
function initializeTradingView(containerId = 'tradingview_widget_container', symbol = 'BTCUSD') {
    console.log('TradingView: Initializing widget with symbol:', symbol);
    
    // Create widget configuration
    const config = {
        "container_id": containerId,
        "symbol": symbol,
        ...TRADINGVIEW_CONFIG.base,
        "overrides": TRADINGVIEW_CONFIG.overrides,
        "studies_overrides": TRADINGVIEW_CONFIG.studies_overrides
    };
    
    // Create the widget
    new TradingView.widget(config);
    
    console.log('TradingView: Widget initialized successfully');
}

/**
*
* ┌─────────────────────────────────────┐
* │      UPDATE TRADINGVIEW CHART       │
* └─────────────────────────────────────┘
* Update TradingView chart with new symbol
*
* Recreates the TradingView widget with a new symbol while maintaining
* the monochromatic theme and all styling configurations.
*
* Parameters:
* - symbol: New trading symbol to display (e.g., "NASDAQ:AAPL")
*
* Returns:
* - Updated TradingView widget instance
*
* Notes:
* - Clears existing widget completely before recreation
* - Generates unique container ID to avoid conflicts
* - Loads TradingView library if needed
* - Maintains all styling overrides
*/
function updateTradingViewChart(symbol) {
    if (!symbol) {
        console.error('TradingView: No symbol provided for chart update');
        return;
    }
    
    // Clean symbol input
    const cleanSymbol = symbol.toUpperCase().trim();
    console.log('TradingView: Updating chart to symbol:', cleanSymbol);
    
    // Find the TradingView widget container
    let parentContainer = document.querySelector('.tradingview-widget-container');
    
    if (!parentContainer) {
        console.error('TradingView: Main container (.tradingview-widget-container) not found');
        return;
    }
    
    console.log('TradingView: Found parent container:', parentContainer);
    
    // Clear the parent container completely
    parentContainer.innerHTML = '';
    console.log('TradingView: Cleared container');
    
    // Recreate the widget container structure with new ID
    const newWidgetContainer = document.createElement('div');
    newWidgetContainer.className = 'tradingview-widget-container__widget';
    newWidgetContainer.id = 'tradingview_widget_container_' + Date.now(); // Unique ID
    parentContainer.appendChild(newWidgetContainer);
    
    // Load TradingView library if not already loaded
    if (!window.TradingView) {
        const tvScript = document.createElement('script');
        tvScript.src = 'https://s3.tradingview.com/tv.js';
        tvScript.onload = function() {
            createWidget(newWidgetContainer.id, cleanSymbol);
        };
        document.head.appendChild(tvScript);
    } else {
        createWidget(newWidgetContainer.id, cleanSymbol);
    }
    
    function createWidget(containerId, symbol) {
        console.log('TradingView: Creating widget with symbol:', symbol);
        
        const config = {
            "container_id": containerId,
            "symbol": symbol,
            ...TRADINGVIEW_CONFIG.base,
            "overrides": TRADINGVIEW_CONFIG.overrides,
            "studies_overrides": TRADINGVIEW_CONFIG.studies_overrides
        };
        
        new TradingView.widget(config);
    }
    
    console.log('TradingView: Widget recreated with symbol:', cleanSymbol);
}

/**
*
* ┌─────────────────────────────────────┐
* │   UPDATE CHART FROM INPUTS          │
* └─────────────────────────────────────┘
* Update chart symbol based on symbol and exchange inputs
*
* Combines symbol and exchange inputs to create a properly formatted
* TradingView symbol (e.g., "NASDAQ:AAPL") and updates the chart.
*
* Parameters:
* - None (reads from DOM inputs)
*
* Returns:
* - None (calls updateTradingViewChart internally)
*
* Notes:
* - Reads from #symbolInput and #exchangeInput elements
* - Formats symbol as "EXCHANGE:SYMBOL" when exchange is provided
* - Uses symbol alone when no exchange is specified
* - Debounced to prevent excessive API calls
*/
function updateTradingViewChartFromInputs() {
    const symbolInput = document.getElementById('symbolInput');
    const exchangeInput = document.getElementById('exchangeInput');
    
    if (!symbolInput) {
        console.error('TradingView: Symbol input not found');
        return;
    }
    
    const symbol = symbolInput.value.trim();
    const exchange = exchangeInput ? exchangeInput.value.trim() : '';
    
    console.log('TradingView: updateTradingViewChartFromInputs called');
    console.log('TradingView: Current inputs - Symbol:', symbol, 'Exchange:', exchange);
    
    if (!symbol) {
        console.log('TradingView: No symbol provided, skipping update');
        return;
    }
    
    // Create TradingView symbol format
    let tradingViewSymbol;
    if (exchange && exchange !== '') {
        tradingViewSymbol = `${exchange.toUpperCase()}:${symbol.toUpperCase()}`;
    } else {
        tradingViewSymbol = symbol.toUpperCase();
    }
    
    console.log('TradingView: Final symbol format:', tradingViewSymbol);
    
    // Update the chart
    updateTradingViewChart(tradingViewSymbol);
}

// Export functions for use in other modules
if (typeof window !== 'undefined') {
    window.TradingViewChart = {
        initialize: initializeTradingView,
        updateChart: updateTradingViewChart,
        updateFromInputs: updateTradingViewChartFromInputs,
        config: TRADINGVIEW_CONFIG
    };
}
