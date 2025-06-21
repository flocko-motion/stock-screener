"""
BasketItem Entity

This module defines the BasketItem class, which represents an item in a financial basket.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List

from .entity import Entity
from fins.financial import Symbol


class BasketItem(Entity):
    """
    Represents an item in a financial basket.
    
    Attributes:
        ticker (str): The ticker of the financial instrument
        amount (float): The quantity of the item
    """
    
    def __init__(self, ticker: str, amount: float = 1,
                 id: Optional[str] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 tags: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 ):
        """
        Initialize a basket item.
        
        Args:
            ticker: The ticker of the financial instrument
            amount: The quantity of the item (default: 1)
        """
        super().__init__(id=id, created_at=created_at, updated_at=updated_at, tags=tags, metadata=metadata)
        self.ticker = ticker
        self.amount = amount
        self._symbol = None
    
    def __str__(self) -> str:
        """Return the string representation of the basket item."""
        return f"{self.amount} x {self.ticker}"

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return BasketItem(self.ticker, amount=other * self.amount)
        return NotImplemented

    def symbol(self) -> Symbol:
        if self._symbol is None:
            self._symbol = Symbol.get(self.ticker)
        return self._symbol

    def to_dict(self):
        """
        Convert the basket item to a dictionary.
        
        Returns:
            A dictionary representation of the basket item
        """
        return {
            "class": "BasketItem",
            "ticker": self.ticker,
            "amount": self.amount
        }

    def copy_of(self):
        return BasketItem(self.ticker, self.amount)



