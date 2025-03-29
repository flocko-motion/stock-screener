"""
Basket Entity

This module defines the Basket class, which represents a collection of financial symbols
with associated data and analysis columns.
"""

from typing import Any, Optional, Iterator, Dict, List
import pandas as pd

from .entity import Entity
from .basket_item import BasketItem
from .column import Column


class Basket(Entity):
    """
    Represents a collection of financial symbols with associated data and analysis columns.
    
    Attributes:
        name: Optional name of the basket
        items: The items in the basket, order is significant
        columns: List of columns in display order
    """
    
    def __init__(self, items: list[BasketItem] = None, name: Optional[str] = None):
        """Initialize a basket."""
        super().__init__()
        self.name = name
        self.items = items or []
        self._columns: List[Column] = []

    def __str__(self) -> str:
        """Return the string representation of the basket."""
        if not self.items:
            return ""
            
        # Simple text representation preserving order
        return "\n".join(f"{item.amount:g}x {item.ticker}" for item in sorted(self.items, key=lambda x: (-x.amount, x.ticker)))
    
    def __len__(self) -> int:
        """Return the number of items in the basket."""
        return len(self.items)
    
    def __iter__(self) -> Iterator[BasketItem]:
        """Return an iterator over the items in the basket."""
        return iter(self.items)
    
    def __contains__(self, ticker: str) -> bool:
        """Check if a symbol is in the basket."""
        return any(item.ticker == ticker for item in self.items)

    def add_item(self, item: BasketItem) -> None:
        """
        Add an item to the basket.
        
        Args:
            item: The item to add
        """
        for existing_item in self.items:
            if existing_item.ticker == item.ticker:
                existing_item.amount += item.amount
                return
        
        self.items.append(item)

    def remove_item(self, ticker: str) -> None:
        """
        Remove an item from the basket.
        
        Args:
            ticker: The ticker of the item to remove
        """
        self.items = [item for item in self.items if item.ticker != ticker]
    
    def add_column(self, column: Column) -> None:
        """Add a column to the basket."""
        self._columns.append(column)

    def remove_column(self, name: str) -> None:
        """Remove a column by name/alias."""
        self._columns = [col for col in self._columns if col.alias() != name]

    def has_column(self, name: str) -> bool:
        """Check if basket has a column by name/alias."""
        return any(col.alias() == name for col in self._columns)

    def get_column(self, name: str) -> Optional[Column]:
        """Get a column by name/alias."""
        return next((col for col in self._columns if col.alias() == name), None)

    def list_columns(self) -> List[str]:
        """Get list of column names/aliases in order."""
        return [col.alias() for col in self._columns]

    def get_values(self, ticker: str) -> Dict[str, Any]:
        """
        Get all column values for a ticker.
        
        Returns:
            Dictionary mapping column names to their values
        """
        return {
            col.alias(): col.value(ticker)
            for col in self._columns
        }

    def operation(self, other: 'Basket', operator: str) -> 'Basket':
        if operator == "+":
            return self.union(other)
        elif operator == "-":
            return self.subtract(other)
        elif operator == "&":
            return self.intersection(other)
        else:
            raise ValueError(f"Unknown operator: {operator}")

    def union(self, other: 'Basket') -> 'Basket':
        """
        Create a new basket that is the union of this basket and another.
        
        Args:
            other: The other basket
            
        Returns:
            A new basket containing all items from both baskets
        """
        result = Basket(name=self.name)
        
        # Add all items from this basket
        for item in self.items:
            result.add_item(BasketItem(item.ticker, item.amount))
        
        # Add all items from the other basket
        for item in other.items:
            result.add_item(BasketItem(item.ticker, item.amount))
        
        # Merge columns
        result._columns = self._columns.copy()
        for col in other._columns:
            if col not in result._columns:
                result._columns.append(col)
        
        return result
    
    def intersection(self, other: 'Basket') -> 'Basket':
        """
        Create a new basket that is the intersection of this basket and another.
        
        Args:
            other: The other basket
            
        Returns:
            A new basket containing only items that are in both baskets
        """
        result = Basket(name=self.name)
        
        # Find symbols that are in both baskets
        this_symbols = {item.ticker for item in self.items}
        other_symbols = {item.ticker for item in other.items}
        common_symbols = this_symbols.intersection(other_symbols)
        
        # Add items for common symbols in this basket's order
        for item in self.items:
            if item.ticker in common_symbols:
                other_item = next(i for i in other.items if i.ticker == item.ticker)
                quantity = min(item.amount, other_item.amount)
                result.add_item(BasketItem(item.ticker, quantity))
        
        # Include columns from both baskets
        result._columns = self._columns.copy()
        for col in other._columns:
            if col not in result._columns:
                result._columns.append(col)
        
        return result
    
    def subtract(self, other: 'Basket') -> 'Basket':
        """
        Create a new basket that is the difference of this basket and another.
        
        Args:
            other: The other basket
            
        Returns:
            A new basket containing only items that are in this basket but not in the other
        """
        result = Basket(name=self.name)
        
        # Add items that aren't in other basket, preserving this basket's order
        other_symbols = {item.ticker for item in other.items}
        for item in self.items:
            if item.ticker not in other_symbols:
                result.add_item(BasketItem(item.ticker, item.amount))
        
        # Include columns from this basket
        result._columns = self._columns.copy()
        
        return result
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert basket to DataFrame with all column values."""
        # Start with basic ticker data
        data = {
            'ticker': [item.ticker for item in self.items],
            'weight': [item.amount for item in self.items]
        }
        
        # Add column values in order
        for col in self._columns:
            data[col.alias()] = [col.value(item.ticker) for item in self.items]
            
        return pd.DataFrame(data)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "class": "Basket",
            "name": self.name,
            "items": [item.to_dict() for item in self.items],
            "columns": [col.to_dict() for col in self._columns]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Basket':
        """Create from dictionary."""
        items = []
        for item_data in data.get('items', []):
            if isinstance(item_data, dict) and item_data.get('class') == 'BasketItem':
                from .basket_item import BasketItem
                item = BasketItem.from_dict(item_data)
                items.append(item)

        basket = cls(items=items, name=data.get('name'))
        
        for col_data in data.get('columns', []):
            if isinstance(col_data, dict) and 'class' in col_data:
                from .column import Column
                col = Column.from_dict(col_data)
                basket.add_column(col)
        
        return basket

