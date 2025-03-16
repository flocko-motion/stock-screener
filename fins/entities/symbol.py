"""
Symbol Entity

This module defines the Symbol class, which represents a financial symbol such as a stock, ETF, or index.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, ClassVar
import traceback

from .json_serializable import JsonSerializable


class Symbol(JsonSerializable):
    """
    Represents a financial symbol (stock, ETF, index).
    
    Attributes:
        ticker (str): The ticker symbol (e.g., 'AAPL', 'SPY')
        exchange (Optional[str]): The exchange where the symbol is traded
        currency (Optional[str]): The currency of the symbol
        name (Optional[str]): The full name of the security
        price (Optional[float]): The current price of the symbol
        market_cap (Optional[float]): The market capitalization of the symbol
        beta (Optional[float]): The beta of the symbol
        sector (Optional[str]): The sector of the symbol
        country (Optional[str]): The country of the symbol
        ipo (Optional[str]): The IPO date of the symbol
        is_etf (Optional[bool]): Whether the symbol is an ETF
        is_fund (Optional[bool]): Whether the symbol is a fund
        is_trading (Optional[bool]): Whether the symbol is currently trading
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
            cls.symbols[ticker] = Symbol(ticker)
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
        self.currency = None
        self.name = None
        self.price = None
        self.market_cap = None
        self.beta = None
        self.sector = None
        self.country = None
        self.ipo = None
        self.is_etf = None
        self.is_fund = None
        self.is_trading = None
        
        # Load profile data from FMP API
        self._load_profile_data()
    
    def _load_profile_data(self):
        """Load profile data from the FMP API."""
        # This is a placeholder for the actual implementation
        # In the real implementation, this would call the FMP API
        pass
    
    def __str__(self) -> str:
        """Return the string representation of the symbol."""
        return self.ticker + ":" + self.exchange if self.exchange else self.ticker
    
    def type_string(self) -> str:
        """
        Get the type of the symbol as a string.
        
        Returns:
            The type of the symbol (ETF, Fund, Crypto, Stock)
        """
        if self.is_etf:
            return "ETF"
        if self.is_fund:
            return "Fund"
        if self.exchange == "CRYPTO":
            return "Crypto"
        return "Stock"
    
    def profile_string(self) -> str:
        """
        Get a formatted string with the symbol's profile information.
        
        Returns:
            A formatted string with the symbol's profile information
        """
        return f"{self.ticker}:{self.exchange} {self.name}\n" \
            + f"{self.type_string()} {self.sector if self.sector is not None else ''} {self.country if self.country is not None else ''} {self.ipo if self.ipo is not None else ''}\n" \
            + f"{self.currency} {self.price} (MktCap: {self.currency} {self.market_cap})"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the symbol to a dictionary.
        
        Returns:
            A dictionary representation of the symbol
        """
        return {
            "class": "Symbol",
            "ticker": self.ticker,
            "exchange": self.exchange,
            "identifier": self.ticker + ":" + self.exchange if self.exchange else self.ticker,
            "currency": self.currency,
            "name": self.name,
            "price": self.price,
            "market_cap": self.market_cap,
            "beta": self.beta,
            "sector": self.sector,
            "country": self.country,
            "ipo": self.ipo,
            "is_etf": self.is_etf,
            "is_fund": self.is_fund,
            "is_trading": self.is_trading
        }
    
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