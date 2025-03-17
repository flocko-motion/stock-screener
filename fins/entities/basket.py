"""
Basket Entity

This module defines the Basket class, which represents a collection of financial symbols
with associated data and analysis columns.
"""

from typing import List, Dict, Any, Optional, Set, Iterator
import pandas as pd
import traceback
from concurrent.futures import ThreadPoolExecutor

from .entity import Entity
from .basket_item import BasketItem
from .column import Column


class Basket(Entity):
    """
    Represents a collection of financial symbols with associated data and analysis columns.
    
    Attributes:
        name (Optional[str]): The name of the basket
        items (List[BasketItem]): The items in the basket
        columns (Dict[str, Column]): The analysis columns associated with the basket
        data (pd.DataFrame): The data frame containing symbol data and analysis results
        note (str): A free text note associated with the basket
    """
    
    def __init__(self, items: List[BasketItem] = None, name: Optional[str] = None, note: str = ""):
        """
        Initialize a basket.

        Args:
            items: The items in the basket
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
        out = ""
        if all(item.amount == 1 for item in self.items):
            sorted_items = sorted(self.items, key=lambda item: item.symbol.ticker)
            for item in sorted_items:
                try:
                    out += f"{item.ticker:<14}\n"
                except Exception as e:
                    return f"error formatting item {item}: {e}"
        else:
            sorted_items = sorted(self.items, key=lambda item: item.amount, reverse=True)
            for item in sorted_items:
                try:
                    out += f"{item.amount:>10.2f}  {item.ticker:<14}\n"
                except Exception as e:
                    return f"error formatting item {item}: {e}"
        
        return out
    
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
        # Check if the symbol already exists in the basket
        for existing_item in self.items:
            if existing_item.symbol == item.symbol:
                # Update the quantity
                existing_item.amount += item.amount
                return
        
        # If the symbol doesn't exist, add the new item
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

    
    def sort_by(self, attribute: str, ascending: bool = True) -> 'Basket':
        """
        Sort the basket by a specific attribute.
        
        Args:
            attribute: The attribute to sort by
            ascending: Whether to sort in ascending order
            
        Returns:
            A new basket with the sorted items
        """
        sorted_items = sorted(
            self.items,
            key=lambda item: item.symbol.get_data(attribute, 0),
            reverse=not ascending
        )
        
        result = Basket(sorted_items, name=self.name, note=self.note)
        result.columns = self.columns.copy()
        return result
    
    def filter_by(self, attribute: str, operator: str, value: Any) -> 'Basket':
        """
        Filter the basket by a specific attribute.
        
        Args:
            attribute: The attribute to filter by
            operator: The comparison operator ('>', '<', '>=', '<=', '==', '!=')
            value: The value to compare against
            
        Returns:
            A new basket with the filtered items
        """
        operators = {
            '>': lambda a, b: a > b,
            '<': lambda a, b: a < b,
            '>=': lambda a, b: a >= b,
            '<=': lambda a, b: a <= b,
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b
        }
        
        if operator not in operators:
            raise ValueError(f"Invalid operator: {operator}")
        
        compare = operators[operator]
        filtered_items = [
            item for item in self.items 
            if item.symbol.get_data(attribute) is not None and compare(item.symbol.get_data(attribute), value)
        ]
        
        result = Basket(filtered_items, name=self.name, note=self.note)
        result.columns = self.columns.copy()
        return result
    
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
            result.add_item(BasketItem(item.symbol, item.amount))
        
        # Add all items from the other basket
        for item in other.items:
            result.add_item(BasketItem(item.symbol, item.amount))
        
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
        this_symbols = {item.symbol for item in self.items}
        other_symbols = {item.symbol for item in other.items}
        common_symbols = this_symbols.intersection(other_symbols)
        
        # Add items for common symbols
        for symbol in common_symbols:
            # Find the item in this basket
            this_item = next(item for item in self.items if item.symbol == symbol)
            # Find the item in the other basket
            other_item = next(item for item in other.items if item.symbol == symbol)
            # Use the minimum quantity
            quantity = min(this_item.amount, other_item.amount)
            result.add_item(BasketItem(symbol, quantity))
        
        # Include columns from both baskets
        result.columns = self.columns.copy()
        for name, column in other.columns.items():
            if name not in result.columns:
                result.columns[name] = column
        
        return result
    
    def difference(self, other: 'Basket') -> 'Basket':
        """
        Create a new basket that is the difference of this basket and another.
        
        Args:
            other: The other basket
            
        Returns:
            A new basket containing only items that are in this basket but not in the other
        """
        result = Basket(name=self.name, note=self.note)
        
        # Find symbols that are in this basket but not in the other
        this_symbols = {item.symbol for item in self.items}
        other_symbols = {item.symbol for item in other.items}
        diff_symbols = this_symbols.difference(other_symbols)
        
        # Add items for different symbols
        for symbol in diff_symbols:
            # Find the item in this basket
            this_item = next(item for item in self.items if item.symbol == symbol)
            result.add_item(BasketItem(symbol, this_item.amount))
        
        # Include only columns from this basket
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
    def from_dict(cls, data: Dict[str, float]) -> 'Basket':
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

