"""
BasketItem Entity

This module defines the BasketItem class, which represents an item in a financial basket.
"""

from .json_serializable import JsonSerializable
from .symbol import Symbol


class BasketItem(JsonSerializable):
    """
    Represents an item in a financial basket.
    
    Attributes:
        symbol (Symbol): The symbol of the financial instrument
        amount (float): The quantity of the item
    """
    
    def __init__(self, symbol: Symbol, amount: float = 1):
        """
        Initialize a basket item.
        
        Args:
            symbol: The symbol of the financial instrument
            amount: The quantity of the item (default: 1)
        """
        self.symbol = symbol
        self.amount = amount
    
    def __str__(self) -> str:
        """Return the string representation of the basket item."""
        return f"{self.amount} x {self.symbol}"
    
    def to_dict(self):
        """
        Convert the basket item to a dictionary.
        
        Returns:
            A dictionary representation of the basket item
        """
        return {
            "class": "BasketItem",
            "symbol": self.symbol.to_dict(),
            "quantity": self.amount
        } 