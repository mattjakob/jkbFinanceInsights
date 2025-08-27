"""
Exchange and Symbol Management System

This module provides unified management of trading exchanges and symbols,
including dynamic validation and proper formatting for TradingView APIs.
The existing scrapers remain independent but can use these utilities for
consistent symbol and exchange handling.
"""

import requests
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import re
import json
from functools import lru_cache
from debugger import debug_info, debug_warning, debug_error, debug_success

@dataclass
class ExchangeInfo:
    """Information about a trading exchange"""
    name: str
    display_name: str
    category: str  # 'crypto', 'stock', 'forex', 'commodity'
    supported_symbols: List[str]
    symbol_format: str  # How symbols should be formatted for this exchange

@dataclass
class SymbolInfo:
    """Information about a trading symbol from TradingView search"""
    symbol: str
    description: str
    type: str  # 'stock', 'spot', 'futures', etc.
    exchange: str
    currency_code: str
    provider_id: str
    is_primary_listing: bool = False

class ExchangeManager:
    """Manages trading exchanges and symbol formatting"""
    
    TRADINGVIEW_SEARCH_URL = "https://symbol-search.tradingview.com/symbol_search/"
    
    def __init__(self):
        self.exchanges: Dict[str, ExchangeInfo] = {}
        self.symbol_cache: Dict[str, List[SymbolInfo]] = {}
        self._initialize_exchanges()
    
    def _initialize_exchanges(self):
        """Initialize supported exchanges with their configurations"""
        
        # Crypto exchanges
        self.exchanges.update({
            "BINANCE": ExchangeInfo(
                name="BINANCE",
                display_name="Binance",
                category="crypto",
                supported_symbols=["BTCUSD", "ETHUSD", "ADAUSD", "DOTUSD", "LINKUSD"],
                symbol_format="SYMBOL"
            ),
            "BITSTAMP": ExchangeInfo(
                name="BITSTAMP", 
                display_name="Bitstamp",
                category="crypto",
                supported_symbols=["BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD"],
                symbol_format="SYMBOL"
            ),
            "COINBASE": ExchangeInfo(
                name="COINBASE",
                display_name="Coinbase",
                category="crypto", 
                supported_symbols=["BTCUSD", "ETHUSD", "ADAUSD", "SOLUSD"],
                symbol_format="SYMBOL"
            ),
            "KRAKEN": ExchangeInfo(
                name="KRAKEN",
                display_name="Kraken",
                category="crypto",
                supported_symbols=["BTCUSD", "ETHUSD", "ADAUSD", "DOTUSD"],
                symbol_format="SYMBOL"
            )
        })
        
        # Stock exchanges
        self.exchanges.update({
            "NASDAQ": ExchangeInfo(
                name="NASDAQ",
                display_name="NASDAQ",
                category="stock",
                supported_symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
                symbol_format="SYMBOL"
            ),
            "NYSE": ExchangeInfo(
                name="NYSE", 
                display_name="NYSE",
                category="stock",
                supported_symbols=["JPM", "JNJ", "PG", "UNH", "HD"],
                symbol_format="SYMBOL"
            )
        })
    
    def get_exchange_info(self, exchange: str) -> Optional[ExchangeInfo]:
        """Get information about a specific exchange"""
        return self.exchanges.get(exchange.upper())
    
    def get_supported_exchanges(self) -> List[Dict[str, str]]:
        """Get list of supported exchanges for frontend"""
        return [
            {
                "value": info.name,
                "label": info.display_name,
                "category": info.category
            }
            for info in self.exchanges.values()
        ]
    
    def validate_symbol_for_exchange(self, symbol: str, exchange: str) -> bool:
        """Validate if a symbol is supported by the exchange"""
        exchange_info = self.get_exchange_info(exchange)
        if not exchange_info:
            return False
        
        # For crypto, allow common patterns
        if exchange_info.category == "crypto":
            return self._is_valid_crypto_symbol(symbol)
        
        # For stocks, check against supported list
        return symbol.upper() in exchange_info.supported_symbols
    
    def _is_valid_crypto_symbol(self, symbol: str) -> bool:
        """Check if symbol follows valid crypto format"""
        # Common crypto patterns: BTCUSD, ETHUSDT, ADAUSD, etc.
        crypto_pattern = r'^[A-Z]{2,10}(USD|USDT|EUR|BTC|ETH)$'
        return bool(re.match(crypto_pattern, symbol.upper()))
    
    def format_symbol_for_tradingview(self, symbol: str, exchange: str) -> str:
        """Format symbol for TradingView API calls"""
        exchange_info = self.get_exchange_info(exchange)
        if not exchange_info:
            return symbol.upper()
        
        # For crypto, use the symbol as-is
        if exchange_info.category == "crypto":
            return symbol.upper()
        
        # For stocks, add exchange prefix if needed
        if exchange_info.category == "stock":
            return f"{exchange_info.name}-{symbol.upper()}"
        
        return symbol.upper()
    
    def get_symbol_suggestions(self, query: str, exchange: str) -> List[str]:
        """Get symbol suggestions based on query and exchange"""
        exchange_info = self.get_exchange_info(exchange)
        if not exchange_info:
            return []
        
        query_upper = query.upper()
        suggestions = []
        
        for symbol in exchange_info.supported_symbols:
            if query_upper in symbol.upper():
                suggestions.append(symbol)
        
        return suggestions[:10]  # Limit to 10 suggestions
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to standard format"""
        # Remove common suffixes and normalize
        normalized = symbol.upper().strip()
        
        # Handle common variations
        if normalized.endswith('USDT'):
            normalized = normalized[:-4] + 'USD'
        elif normalized.endswith('BTC'):
            normalized = normalized[:-3] + 'USD'
        
        return normalized
    
    def get_exchange_category(self, exchange: str) -> str:
        """Get the category of an exchange"""
        exchange_info = self.get_exchange_info(exchange)
        return exchange_info.category if exchange_info else "unknown"
    
    @lru_cache(maxsize=1000)
    def search_symbol(self, query: str, symbol_type: str = "") -> List[SymbolInfo]:
        """
        Search for symbols using TradingView's search API
        
        Parameters:
        - query: The symbol to search for (e.g., "AAPL", "BTCUSD")
        - symbol_type: Optional type filter (e.g., "stock", "crypto", "forex")
        
        Returns:
        - List of SymbolInfo objects with matching symbols
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Origin': 'https://www.tradingview.com',
                'Referer': 'https://www.tradingview.com/'
            }
            
            params = {
                'text': query,
                'type': symbol_type
            }
            
            response = requests.get(
                self.TRADINGVIEW_SEARCH_URL,
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data:
                    symbol_info = SymbolInfo(
                        symbol=item.get('symbol', ''),
                        description=item.get('description', ''),
                        type=item.get('type', ''),
                        exchange=item.get('exchange', ''),
                        currency_code=item.get('currency_code', 'USD'),
                        provider_id=item.get('provider_id', ''),
                        is_primary_listing=item.get('is_primary_listing', False)
                    )
                    results.append(symbol_info)
                
                return results
            else:
                debug_error(f"Failed to search symbol: {response.status_code}")
                return []
        
        except Exception as e:
            debug_error(f"Error searching symbol '{query}': {e}")
            return []
    
    def find_best_exchange_for_symbol(self, symbol: str) -> Optional[str]:
        """
        Find the best exchange for a given symbol using TradingView search
        
        Parameters:
        - symbol: The symbol to find exchange for
        
        Returns:
        - Best exchange name or None if not found
        """
        results = self.search_symbol(symbol)
        
        if not results:
            return None
        
        # Filter for exact symbol matches first
        exact_matches = [r for r in results if r.symbol.upper() == symbol.upper()]
        if not exact_matches:
            return None
        
        # Group exact matches by type
        crypto_results = [r for r in exact_matches if r.type in ['spot', 'crypto']]
        stock_results = [r for r in exact_matches if r.type == 'stock']
        forex_results = [r for r in exact_matches if r.type == 'forex']
        
        # Determine likely type based on symbol pattern
        is_likely_crypto = False
        is_likely_forex = False
        
        # Common crypto patterns
        if symbol.upper().endswith(('USD', 'USDT', 'EUR', 'BTC', 'ETH')):
            crypto_bases = ['BTC', 'ETH', 'ADA', 'DOT', 'LINK', 'SOL', 'XRP', 'LTC', 'BCH', 'MATIC']
            for base in crypto_bases:
                if symbol.upper().startswith(base):
                    is_likely_crypto = True
                    break
        
        # Common forex patterns
        forex_currencies = ['EUR', 'USD', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NZD']
        if len(symbol) == 6:  # Forex pairs are typically 6 chars
            pair1 = symbol[:3].upper()
            pair2 = symbol[3:].upper()
            if pair1 in forex_currencies and pair2 in forex_currencies:
                is_likely_forex = True
        
        # Priority logic for selecting best exchange
        # 1. Primary listings first (within the correct type)
        if is_likely_crypto and crypto_results:
            primary_crypto = [r for r in crypto_results if r.is_primary_listing]
            if primary_crypto:
                return primary_crypto[0].exchange
        elif is_likely_forex and forex_results:
            primary_forex = [r for r in forex_results if r.is_primary_listing]
            if primary_forex:
                return primary_forex[0].exchange
        else:
            primary_listings = [r for r in results if r.is_primary_listing]
            if primary_listings:
                return primary_listings[0].exchange
        
        # 2. For crypto, prefer major exchanges
        if is_likely_crypto and crypto_results:
            crypto_priority = ['BINANCE', 'COINBASE', 'BITSTAMP', 'KRAKEN']
            for exchange in crypto_priority:
                for result in crypto_results:
                    if result.exchange == exchange:
                        return exchange
            # Return first crypto result if no priority exchange found
            return crypto_results[0].exchange
        
        # 3. For forex, prefer major forex platforms
        if is_likely_forex and forex_results:
            forex_priority = ['FX', 'OANDA', 'FOREXCOM', 'FX_IDC']
            for exchange in forex_priority:
                for result in forex_results:
                    if result.exchange == exchange:
                        return exchange
            # Return first forex result
            return forex_results[0].exchange
        
        # 4. For stocks, prefer major exchanges
        if stock_results and not is_likely_crypto and not is_likely_forex:
            stock_priority = ['NASDAQ', 'NYSE', 'AMEX']
            for exchange in stock_priority:
                for result in stock_results:
                    if result.exchange == exchange:
                        return exchange
            # Return first stock result
            return stock_results[0].exchange
        
        # 5. Return first result as fallback
        return results[0].exchange
    
    def get_symbol_type(self, symbol: str) -> Optional[str]:
        """
        Get the type of a symbol (stock, crypto, forex, etc.)
        
        Parameters:
        - symbol: The symbol to check
        
        Returns:
        - Symbol type or None if not found
        """
        results = self.search_symbol(symbol)
        
        if not results:
            return None
        
        # Return the type of the primary listing or first result
        primary_listings = [r for r in results if r.is_primary_listing]
        if primary_listings:
            return primary_listings[0].type
        
        return results[0].type
    
    def get_tradingview_url_for_symbol(self, symbol: str, exchange: str, data_type: str = "ideas", sort: str = None) -> str:
        """
        Generate the correct TradingView URL for a symbol and data type
        
        Parameters:
        - symbol: trading symbol
        - exchange: exchange name
        - data_type: type of data ('ideas', 'news', 'opinions')
        - sort: sorting method for ideas ('recent', 'popular')
        
        Returns:
        - Properly formatted TradingView URL
        """
        formatted_symbol = self.format_symbol_for_tradingview(symbol, exchange)
        
        if data_type == "ideas":
            if sort == "recent":
                return f"https://www.tradingview.com/symbols/{formatted_symbol}/ideas/?component-data-only=1&sort=recent"
            else:
                # Popular ideas (no sort parameter means popular by default)
                return f"https://www.tradingview.com/symbols/{formatted_symbol}/ideas/"
        elif data_type == "news":
            return f"https://www.tradingview.com/symbols/{formatted_symbol}/news/"
        elif data_type == "opinions":
            return f"https://www.tradingview.com/symbols/{formatted_symbol}/discussions/"
        else:
            return f"https://www.tradingview.com/symbols/{formatted_symbol}/"
    
    def validate_request(self, symbol: str, exchange: str = None, data_type: str = "ideas") -> Dict[str, Any]:
        """
        Validate a scraping request and return formatted parameters
        
        Parameters:
        - symbol: trading symbol
        - exchange: exchange name (optional - will auto-detect if not provided)
        - data_type: type of data to scrape
        
        Returns:
        - Dictionary with validation results and formatted parameters
        """
        # If exchange not provided, find best exchange for symbol
        if not exchange:
            exchange = self.find_best_exchange_for_symbol(symbol)
            if not exchange:
                return {
                    "valid": False,
                    "error": f"Symbol '{symbol}' not found on any exchange",
                    "supported_exchanges": self.get_supported_exchanges()
                }
        
        # Search for symbol details
        search_results = self.search_symbol(symbol)
        # Filter for exact symbol and exchange matches
        matching_results = [r for r in search_results 
                          if r.exchange == exchange.upper() and r.symbol.upper() == symbol.upper()]
        
        if not matching_results:
            # Try to find symbol on any exchange
            if search_results:
                suggested_exchanges = list(set([r.exchange for r in search_results[:5]]))
                return {
                    "valid": False,
                    "error": f"Symbol '{symbol}' not found on exchange '{exchange}'",
                    "suggested_exchanges": suggested_exchanges,
                    "symbol_type": search_results[0].type if search_results else None
                }
            else:
                return {
                    "valid": False,
                    "error": f"Symbol '{symbol}' not found",
                    "supported_exchanges": self.get_supported_exchanges()
                }
        
        # Use the matching result
        symbol_info = matching_results[0]
        
        # Format symbol for TradingView
        formatted_symbol = self.format_symbol_for_tradingview(symbol, exchange)
        
        # Get all available exchanges for this symbol
        all_exchanges_for_symbol = list(set([r.exchange for r in search_results 
                                           if r.symbol.upper() == symbol.upper()]))
        
        return {
            "valid": True,
            "symbol": symbol,
            "exchange": exchange,
            "formatted_symbol": formatted_symbol,
            "symbol_type": symbol_info.type,
            "symbol_description": symbol_info.description,
            "currency": symbol_info.currency_code,
            "is_primary_listing": symbol_info.is_primary_listing,
            "suggested_exchanges": all_exchanges_for_symbol,
            "tradingview_url": self.get_tradingview_url_for_symbol(symbol, exchange, data_type)
        }

# Global instance
exchange_manager = ExchangeManager()
