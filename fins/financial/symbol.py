"""
Symbol Entity

This module defines the Symbol class, which represents a financial symbol such as a stock, ETF, or index.
"""
from datetime import datetime
from typing import Optional, Dict, Any, ClassVar

from fins.data_sources import fmp

TYPE_STOCK="stock"
TYPE_CRYPTO="crypto"
TYPE_ETF="etf"
TYPE_INDEX="index"

class Symbol:
    """
    Represents a financial symbol (stock, ETF, index).
    """
    
    # Class variable to store all symbols
    symbols: ClassVar[Dict[str, 'Symbol']] = {}
    
    @classmethod
    def get(cls, ticker: str) -> 'Symbol':
        """
        Get a symbol by ticker, creating it if it doesn't exist.
        
        Args:
            ticker: The ticker symbol
            
        Returns:
            The Symbol instance
        """
        if ticker not in cls.symbols:
                s = Symbol(ticker)
                cls.symbols[ticker] = s
        return cls.symbols[ticker]
    
    def __init__(self, ticker: str):
        """
        Initialize a symbol.
        
        Args:
            ticker: The ticker symbol
        """
        if not isinstance(ticker, str):
            raise ValueError(f"Invalid ticker value: {ticker}")
        
        tokens = ticker.split(":", 1)
        
        self.ticker = tokens[0]
        self.exchange = None if len(tokens) < 2 else tokens[1]
        
        self.name: str | None = None
        self.type: str | None = None
        self.currency: str | None = None
        self.sector: str | None = None
        self.industry: str | None = None
        self.country: str | None = None
        self.description: str | None = None
        self.website: str | None = None
        self.isin: str | None = None
        self.inception: datetime | None = None

        self._load_analytics_expiry = None
        self.market_cap: int | None = None
        self.volume: int | None = None

        self.return_on_equity_ttm: float | None = None
        self.net_profit_margin_ttm: float | None = None
        self.pe_ratio_ttm: float | None = None
        self.peg_ratio_ttm: float | None = None
        self.dividend_yield_ttm: float | None = None

        self._load_profile_data()
        self._load_analytics()

    
    def _load_profile_data(self):
        """Load profile data from appropriate API based on symbol type."""
        try:
            if self.ticker.endswith("USD"):
                profile = fmp.profile_crypto(self.ticker)
                if profile:
                    self.type = TYPE_CRYPTO
                    self._load_profile(profile)
                    self.currency = "USD"
                    self.exchange = "CRYPTO"
                    return
        except ValueError:
            pass

        try:
            profile = fmp.profile(self.ticker)
            if profile:
                if profile.get("isEtf", False):
                    self.type = TYPE_ETF
                else:
                    self.type = TYPE_STOCK
                self._load_profile(profile)
                return
        except ValueError:
            pass

        try:
            profile = fmp.profile_etf(self.ticker)
            if profile:
                self.type = TYPE_ETF
                self._load_profile(profile)
                return
        except ValueError:
            pass

        raise ValueError(f"Symbol not found: {self.ticker}")


    def _load_profile(self, profile: Dict[str, Any]):
        """Load unified profile data."""
        self.name = profile.get("companyName") or profile.get("name")
        self.currency = profile.get("currency") or profile.get("navCurrency")
        self.exchange = profile.get("exchangeShortName") or profile.get("exchange")
        
        self.sector = profile.get("sector")
        self.industry = profile.get("industry")
        self.country = profile.get("country") or profile.get("domicile")
        
        self.description = profile.get("description")
        self.website = profile.get("website")
        self.isin = profile.get("isin")

        self.inception = datetime.strptime(profile.get("icoDate"), '%Y-%m-%d') if profile.get("icoDate") else None


    def _load_analytics(self):
        if not (self._load_analytics_expiry is None) and self._load_analytics_expiry > datetime.now():
            return
        analytics = fmp.outlook(self.ticker)

        self.return_on_equity_ttm = analytics.get("ratios", {}).get("returnOnEquityTTM", None)
        self.net_profit_margin_ttm = analytics.get("ratios", {}).get("netProfitMarginTTM", None)
        self.pe_ratio_ttm = analytics.get("ratios", {}).get("peRatioTTM", None)
        self.peg_ratio_ttm = analytics.get("ratios", {}).get("pegRatioTTM", None)
        self.dividend_yield_ttm = analytics.get("ratios", {}).get("dividendYielTTM", None)



    def __str__(self) -> str:
        """Return the string representation of the symbol."""
        return self.ticker + ":" + self.exchange if self.exchange else self.ticker
    
    def profile_string(self) -> str:
        """
        Get a formatted string with the symbol's profile information.
        
        Returns:
            A formatted string with the symbol's profile information
        """
        return f"{self.ticker}:{self.exchange} {self.name}\n" \
            + f"{self.type} {self.sector if self.sector is not None else ''} {self.country if self.country is not None else ''}\n" \
            + f"{self.currency} {self.description if self.description is not None else ''}"
    
    def add_data(self, key: str, value: Any) -> None:
        """
        Add data to the symbol.
        
        Args:
            key: The key for the data
            value: The value to store
        """
        setattr(self, key, value)
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Get data from the symbol.
        
        Args:
            key: The key for the data
            default: The default value to return if the key is not found
            
        Returns:
            The value associated with the key, or the default value if not found
        """
        return getattr(self, key, default)



def expiry_end_of_month():
    """ number of seconds until noon on the first day of next month"""
    now = datetime.now()
    # Get the first day of next month
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1, 12, 0)  # Noon on Jan 1st of next year
    else:
        next_month = datetime(now.year, now.month + 1, 1, 12, 0)  # Noon on 1st of next month
    return next_month - now
