"""
Database Models

This module defines SQLAlchemy models for the financial data.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, ClassVar

import pandas as pd
from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base

from fins.data_sources import fmp
from fins.financial.cache import session_scope, get_expiration_time

Base = declarative_base()

TYPE_STOCK = "stock"
TYPE_CRYPTO = "crypto"
TYPE_ETF = "etf"
TYPE_INDEX = "index"

class Symbol(Base):
    """SQLAlchemy model for symbol data with business logic."""
    
    __tablename__ = 'symbols'
    
    # Class variables for caching
    symbols: ClassVar[Dict[str, 'Symbol']] = {}
    
    # Core fields that are unlikely to change
    ticker = Column(String(20), primary_key=True)
    exchange = Column(String(20), nullable=True)
    valid_until = Column(DateTime, nullable=False)
    
    # Profile data
    name = Column(String(200), nullable=True)
    type = Column(String(20), nullable=True)
    currency = Column(String(10), nullable=True)
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    website = Column(String(200), nullable=True)
    isin = Column(String(20), nullable=True)
    inception = Column(DateTime, nullable=True)
    
    # Flexible data storage for analytics and other future fields
    analytics = Column(JSON, nullable=True)
    details = Column(JSON, nullable=True)  # For any future fields we might add
    
    # Runtime-only attributes (not stored in DB)
    history = None
    
    @classmethod
    def _get_from_cache(cls, ticker: str) -> Optional['Symbol']:
        """Get a symbol from the cache."""
        with session_scope() as session:
            symbol = session.query(cls).filter_by(ticker=ticker).first()
            if symbol and symbol.valid_until > datetime.now():
                # Detach the symbol from the session and return a copy
                session.expunge(symbol)
                return symbol
            return None
    
    @classmethod
    def _save_to_cache(cls, symbol: 'Symbol') -> None:
        """Store a symbol in the cache."""
        with session_scope() as session:
            # Delete any existing entry
            session.query(cls).filter_by(ticker=symbol.ticker).delete()
            # Add the new entry
            session.add(symbol)
            session.flush()  # Ensure the symbol is in the database
            session.expunge(symbol)  # Detach it from the session
    
    @classmethod
    def _delete_from_cache(cls, ticker: str) -> None:
        """Delete a symbol from the cache."""
        with session_scope() as session:
            session.query(cls).filter_by(ticker=ticker).delete()
    
    @classmethod
    def _clear_expired_cache(cls) -> None:
        """Remove all expired entries from the cache."""
        with session_scope() as session:
            session.query(cls).filter(cls.valid_until <= datetime.now()).delete()
    
    @classmethod
    def _clear_all_cache(cls) -> None:
        """Remove all entries from the cache."""
        with session_scope() as session:
            session.query(cls).delete()
    
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
            # Check cache first
            cached_symbol = cls._get_from_cache(ticker)
            
            if cached_symbol:
                cls.symbols[ticker] = cached_symbol
            else:
                # Create new symbol only if not in cache
                s = Symbol(ticker)
                cls.symbols[ticker] = s
                
        return cls.symbols[ticker]
    
    def __init__(self, ticker: str, **kwargs):
        """
        Initialize a symbol.
        
        Args:
            ticker: The ticker symbol
            **kwargs: Additional fields when loading from cache
        """
        if not isinstance(ticker, str):
            raise ValueError(f"Invalid ticker value: {ticker}")
        
        # Always set the ticker first
        self.ticker = ticker.split(":", 1)[0]
        
        # If we're loading from cache, set all fields directly
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)
            return
            
        # Otherwise, initialize a new symbol
        self.exchange = ticker.split(":", 1)[1] if ":" in ticker else None
        self.valid_until = get_expiration_time()
        
        # Load data from API
        self._load_profile_data()
        self._load_analytics()
        
        # Cache the new symbol
        self._save_to_cache(self)
    
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

    ratios_field_mapping = {
        "return_on_equity_ttm": "returnOnEquityTTM",
        "net_profit_margin_ttm": "netProfitMarginTTM",
        "pe_ratio_ttm": "peRatioTTM",
        "peg_ratio_ttm": "pegRatioTTM",
        "dividend_yield_ttm": "dividendYielTTM",
    }

    def _load_analytics(self):
        """Load analytics data from API."""
        if not (self.type == TYPE_STOCK or self.type == TYPE_ETF):
            return
            
        outlook = fmp.outlook(self.ticker)
        analytics = {}
        if len(outlook.get("ratios", [])) == 1:
            ratios = outlook.get("ratios")[0]
            for k0, k1 in self.ratios_field_mapping.items():
                analytics[k0] = ratios.get(k1, None)
        analytics["market_cap"] = outlook.get("profile", {}).get("mktCap", None)
        analytics["volume"] = outlook.get("profile", {}).get("volAvg", None)
        self.analytics = analytics

    def _load_history(self):
        """Load price history from API."""
        self.history = fmp.price_history(self.ticker)

    def get_history(self) -> pd.DataFrame | None:
        """Get price history data, loading it if necessary."""
        if self.history is None:
            self._load_history()
        return self.history

    def get_analytics(self, field: str) -> float | None:
        """Get a specific analytics field."""
        if not self.analytics:
            self._load_analytics()
        return self.analytics.get(field, None)

    def __str__(self) -> str:
        """Return the string representation of the symbol."""
        return self.ticker + ":" + self.exchange if self.exchange else self.ticker

    def profile_string(self) -> str:
        """Get a formatted string with the symbol's profile information."""
        return f"{self.ticker}:{self.exchange} {self.name}\n" \
            + f"{self.type} {self.sector if self.sector is not None else ''} {self.country if self.country is not None else ''}\n" \
            + f"{self.currency} {self.description if self.description is not None else ''}"
    
    def add_data(self, key: str, value: Any) -> None:
        """Add data to the symbol."""
        setattr(self, key, value)
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get data from the symbol."""
        return getattr(self, key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            'ticker': self.ticker,
            'exchange': self.exchange,
            'name': self.name,
            'type': self.type,
            'currency': self.currency,
            'sector': self.sector,
            'industry': self.industry,
            'country': self.country,
            'description': self.description,
            'website': self.website,
            'isin': self.isin,
            'inception': self.inception,
            'analytics': self.analytics,
            'valid_until': self.valid_until,
            **(self.details or {})  # Include any additional fields
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Symbol':
        """Create a model instance from a dictionary."""
        # Separate core fields from details
        core_fields = {
            'ticker', 'exchange', 'name', 'type', 'currency', 'sector',
            'industry', 'country', 'description', 'website', 'isin',
            'inception', 'analytics', 'valid_until'
        }
        
        # Create base instance with core fields, excluding ticker from kwargs
        kwargs = {k: v for k, v in data.items() if k in core_fields and k != 'ticker'}
        instance = cls(data['ticker'], **kwargs)
        
        # Store any additional fields in details
        details = {k: v for k, v in data.items() if k not in core_fields}
        if details:
            instance.details = details
            
        return instance

def beginning_of_next_month() -> datetime:
    """Get the beginning of next month plus 12 hours for market data to settle."""
    now = datetime.now()
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)
    
    # Add 12 hours to allow for market data to settle
    return next_month + timedelta(hours=12) 