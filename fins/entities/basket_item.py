"""
BasketItem Entity

This module defines the BasketItem class, which represents an item in a financial basket.
"""

from .entity import Entity


class BasketItem(Entity):
    """
    Represents an item in a financial basket.
    
    Attributes:
        ticker (str): The ticker of the financial instrument
        amount (float): The quantity of the item
    """
    
    def __init__(self, ticker: str, amount: float = 1):
        """
        Initialize a basket item.
        
        Args:
            ticker: The ticker of the financial instrument
            amount: The quantity of the item (default: 1)
        """
        super().__init__()
        self.ticker = ticker
        self.amount = amount
    
    def __str__(self) -> str:
        """Return the string representation of the basket item."""
        return f"{self.amount} x {self.ticker}"
    
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