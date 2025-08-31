"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        SYMBOL SERVICE               │
 *  └─────────────────────────────────────┘
 *  Business logic for trading symbol operations
 * 
 *  Handles symbol search, validation, and normalization
 *  across the application.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - SymbolService instance
 * 
 *  Notes:
 *  - Extracted from scraping service for clarity
 *  - Uses exchange manager for validation
 */
"""

from typing import Dict, Any, List
from symbol_validator import exchange_manager
from data import InsightsRepository
from debugger import debug_info, debug_error


class SymbolService:
    """
     ┌─────────────────────────────────────┐
     │         SYMBOLSERVICE               │
     └─────────────────────────────────────┘
     Business logic for symbol operations
     
     Provides symbol search, validation, and normalization.
    """
    
    def __init__(self):
        self.insights_repo = InsightsRepository()
    
    def search_symbols(self, query: str) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │       SEARCH_SYMBOLS                │
         └─────────────────────────────────────┘
         Search for trading symbols
         
         Parameters:
         - query: Search query string
         
         Returns:
         - Dictionary with symbol suggestions
        """
        try:
            if not query or len(query.strip()) < 1:
                return {"suggestions": []}
            
            # Search symbols using exchange manager
            results = exchange_manager.search_symbol(query.strip())
            
            # Process results to match frontend expectations
            suggestions = []
            
            # Group results by symbol to show multiple exchange options
            symbol_groups = {}
            for result in results:
                symbol = result.symbol.upper()
                if symbol not in symbol_groups:
                    symbol_groups[symbol] = []
                symbol_groups[symbol].append(result)
            
            # Show multiple exchange options for each symbol, respecting TradingView's ranking
            for symbol, group in list(symbol_groups.items())[:5]:  # Limit to 5 unique symbols
                # For symbols with multiple exchanges, show up to 6 options
                if len(group) > 1:
                    # Show multiple exchange options, respecting TradingView's order
                    # Filter for spot trading first (most relevant for users)
                    spot_results = [r for r in group if r.type == 'spot']
                    other_results = [r for r in group if r.type != 'spot']
                    
                    # Combine spot results first, then others, respecting TradingView's ranking
                    all_results = spot_results + other_results
                    top_exchanges = all_results[:6]
                    
                    for result in top_exchanges:
                        suggestions.append({
                            "symbol": result.symbol,
                            "description": result.description,
                            "exchange": result.exchange,
                            "type": result.type,
                            "provider_id": result.provider_id
                        })
                else:
                    # Single exchange result
                    best_result = group[0]
                    suggestions.append({
                        "symbol": best_result.symbol,
                        "description": best_result.description,
                        "exchange": best_result.exchange,
                        "type": best_result.type,
                        "provider_id": best_result.provider_id
                    })
            
            return {"suggestions": suggestions}
            
        except Exception as e:
            debug_error(f"Symbol search failed: {e}")
            return {"suggestions": [], "error": str(e)}
    
    def get_normalized_symbols(self) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │    GET_NORMALIZED_SYMBOLS           │
         └─────────────────────────────────────┘
         Get normalized list of unique symbols from insights
         
         Returns:
         - Dictionary with unique symbols and metadata
        """
        try:
            # Get all insights to extract unique symbols
            insights = self.insights_repo.find_all()
            
            # Create a dictionary to normalize symbols (symbol -> exchange)
            symbol_map = {}
            
            for insight in insights:
                if insight.symbol:
                    symbol = insight.symbol.upper()
                    exchange = insight.exchange or 'NASDAQ'
                    
                    # If symbol already exists, prefer the first exchange found
                    if symbol not in symbol_map:
                        symbol_map[symbol] = exchange
            
            # Convert to list format
            normalized_symbols = [
                {
                    "symbol": symbol,
                    "exchange": exchange,
                    "url": f"/api/insights/{exchange}:{symbol}"
                }
                for symbol, exchange in symbol_map.items()
            ]
            
            # Sort by symbol for consistent ordering
            normalized_symbols.sort(key=lambda x: x["symbol"])
            
            return {
                "success": True,
                "count": len(normalized_symbols),
                "symbols": normalized_symbols
            }
            
        except Exception as e:
            debug_error(f"Failed to get normalized symbols: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_symbol(self, symbol: str, exchange: str) -> bool:
        """
         ┌─────────────────────────────────────┐
         │       VALIDATE_SYMBOL               │
         └─────────────────────────────────────┘
         Validate if symbol exists on given exchange
         
         Parameters:
         - symbol: Trading symbol
         - exchange: Exchange name
         
         Returns:
         - True if valid, False otherwise
        """
        try:
            results = exchange_manager.search_symbol(symbol)
            for result in results:
                if result.symbol.upper() == symbol.upper() and result.exchange.upper() == exchange.upper():
                    return True
            return False
        except Exception:
            return False
