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
        
        self.name = None
        self.type = None
        self.currency = None
        self.sector = None
        self.industry = None
        self.country = None
        self.description = None
        self.website = None
        self.isin = None
        self.inception = None
        
        self._load_profile_data()
    
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