"""
Basket Entity

This module defines the Basket class, which represents a collection of financial symbols
with associated data and analysis columns.
"""

from typing import Any, Optional, Iterator, Dict
import pandas as pd

from .entity import Entity
from .basket_item import BasketItem
from .column import Column


class Basket(Entity):
    """
    Represents a collection of financial symbols with associated data and analysis columns.
    
    Attributes:
        name (Optional[str]): The name of the basket
        items (List[BasketItem]): The items in the basket, order is significant and preserved
        columns (Dict[str, Column]): The analysis columns associated with the basket
        data (pd.DataFrame): The data frame containing symbol data and analysis results
        note (str): A free text note associated with the basket
    """
    
    def __init__(self, items: list[BasketItem] = None, name: Optional[str] = None, note: str = ""):
        """
        Initialize a basket.

        Args:
            items: The items in the basket (order will be preserved)
            name: The name of the basket
            note: A free text note associated with the basket
        """
        super().__init__()
        self.items = items or []
        self.name = name
        self.note = note
        self.columns = {}
        self.data = None

    def __str__(self) -> str:
        """Return the string representation of the basket."""
        if not self.items:
            return ""
            
        # Simple text representation preserving order
        return "\n".join(f"{item.amount:g}x {item.ticker}" for item in self.items)
    
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
        """
        Add an analysis column to the basket.
        
        Args:
            column: The column to add
        """
        self.columns[column.name] = column
    
    def get_column(self, name: str) -> Optional[Column]:
        """
        Get an analysis column by name.
        
        Args:
            name: The name of the column
            
        Returns:
            The column if found, None otherwise
        """
        return self.columns.get(name)

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
        result = Basket(name=self.name, note=self.note)
        
        # Add all items from this basket
        for item in self.items:
            result.add_item(BasketItem(item.ticker, item.amount))
        
        # Add all items from the other basket
        for item in other.items:
            result.add_item(BasketItem(item.ticker, item.amount))
        
        # Merge columns
        result.columns = self.columns.copy()
        for name, column in other.columns.items():
            if name not in result.columns:
                result.columns[name] = column
        
        return result
    
    def intersection(self, other: 'Basket') -> 'Basket':
        """
        Create a new basket that is the intersection of this basket and another.
        
        Args:
            other: The other basket
            
        Returns:
            A new basket containing only items that are in both baskets
        """
        result = Basket(name=self.name, note=self.note)
        
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
        result.columns = self.columns.copy()
        for name, column in other.columns.items():
            if name not in result.columns:
                result.columns[name] = column
        
        return result
    
    def subtract(self, other: 'Basket') -> 'Basket':
        """
        Create a new basket that is the difference of this basket and another.
        
        Args:
            other: The other basket
            
        Returns:
            A new basket containing only items that are in this basket but not in the other
        """
        result = Basket(name=self.name, note=self.note)
        
        # Add items that aren't in other basket, preserving this basket's order
        other_symbols = {item.ticker for item in other.items}
        for item in self.items:
            if item.ticker not in other_symbols:
                result.add_item(BasketItem(item.ticker, item.amount))
        
        # Include columns from this basket
        result.columns = self.columns.copy()
        
        return result
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the basket to a pandas DataFrame.
        
        Returns:
            A DataFrame containing the basket data
        """
        # Create a basic DataFrame with symbol information
        data = {
            'ticker': [item.symbol.ticker for item in self.items],
            'name': [item.symbol.name for item in self.items],
            'exchange': [item.symbol.exchange for item in self.items],
            'quantity': [item.amount for item in self.items]
        }
        
        # Add data from each symbol
        for i, item in enumerate(self.items):
            for key in dir(item.symbol):
                # Skip private attributes and methods
                if key.startswith('_') or callable(getattr(item.symbol, key)):
                    continue
                
                value = getattr(item.symbol, key)
                if key not in data:
                    data[key] = [None] * len(self.items)
                data[key][i] = value
        
        return pd.DataFrame(data)
    
    def to_dict(self):
        """
        Convert the basket to a dictionary.
        
        Returns:
            A dictionary representation of the basket
        """
        return {
            "class": "Basket",
            "name": self.name,
            "note": self.note,
            "items": [item.to_dict() for item in self.items],
            "columns": {name: column.to_dict() for name, column in self.columns.items()}
        }

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> 'Basket':
        """
        Create a basket from a dictionary.
        
        Args:
            data: The dictionary containing basket data
            
        Returns:
            A new Basket instance
        """
        # Parse items
        items = []
        for item_data in data.get('items', []):
            if isinstance(item_data, dict) and item_data.get('class') == 'BasketItem':
                from .basket_item import BasketItem
                raise NotImplementedError("BasketItem.from_dict")


        # Create the basket
        basket = cls(
            items=items,
            name=data.get('name'),
            note=data.get('note', '')
        )
        
        # Parse columns
        for name, column_data in data.get('columns', {}).items():
            if isinstance(column_data, dict) and column_data.get('class') == 'Column':
                from .column import Column
                column = Column.from_dict(column_data)
                basket.columns[name] = column
        
        return basket

