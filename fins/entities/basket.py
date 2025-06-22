"""
Basket Entity

This module defines the Basket class, which represents a collection of financial symbols
with associated data and analysis columns.
"""

from typing import Any, Optional, Iterator, Dict, List
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import inspect

from . import columns
from .columns import IndustryColumn, NameColumn
from .entity import Entity
from .basket_item import BasketItem
from .column import Column


class Basket(Entity):
    """
    A weighted list of BasketItems (wrapped Symbols) and a lot of column-functions for analytics.


    
    Attributes:
        name: Optional name of the basket
        items: The items in the basket, order is significant
        columns: List of columns in display order
    """
    
    def __init__(self, *symbols, items: list[BasketItem] = None, name: Optional[str] = None):
        """Initialize a basket."""
        super().__init__()
        self.name = name
        self.items = list(symbols) if len(symbols) > 0 else (items or [])
        self._columns: List[Column] = []

    def __str__(self) -> str:
        """Return the string representation of the basket."""
        if not self.items:
            return ""
            
        # Simple text representation preserving order
        return "\n".join(f"{item.amount:g}x {item.ticker}" for item in sorted(self.items, key=lambda x: (-x.amount, x.ticker)))
    
    def __repr__(self) -> str:
        """Return a simple string representation of the basket."""
        if not self.items:
            return "Empty Basket"
        return repr(self.df())
    
    def _repr_html_(self) -> str:
        """Return HTML representation for rich Jupyter display."""
        if not self.items:
            return "<i>Empty Basket</i>"
        return self.df()._repr_html_()
    
    def __len__(self) -> int:
        """Return the number of items in the basket."""
        return len(self.items)
    
    def __iter__(self) -> Iterator[BasketItem]:
        """Return an iterator over the items in the basket."""
        return iter(self.items)
    
    def __contains__(self, ticker: str) -> bool:
        """Check if a symbol is in the basket."""
        return any(item.ticker == ticker for item in self.items)

    def add_basket_items(self, basket: 'Basket'):
        for item in basket.items:
            self.add_item(item.copy_of())
        pass

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

    def copy_of(self) -> 'Basket':
        copy = Basket(name=self.name)
        for item in self.items:
            copy.add_item(BasketItem(item.ticker, item.amount))
        copy._columns = self._columns.copy()
        return copy

    def add_column(self, column: Column) -> 'Basket':
        """Add a column to the basket and return a new basket."""
        result = self.copy_of()
        result._columns.append(column)
        return result

    def remove_column(self, name: str) -> 'Basket':
        """Remove a column by name/alias and return a new basket."""
        result = self.copy_of()
        result._columns = [col for col in result._columns if col.alias() != name]
        return result

    def has_column(self, name: str) -> bool:
        """Check if basket has a column by name/alias."""
        return any(col.alias() == name for col in self._columns)

    def get_column(self, name: str) -> Optional[Column]:
        """Get a column by name/alias."""
        return next((col for col in self._columns if col.alias() == name), None)

    def list_columns(self) -> List[str]:
        """Get list of column names/aliases in order."""
        return [col.alias() for col in self._columns]


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

    def multiply(self, weight) -> 'Basket':
        """
        Return a new basket with all weights multiplied by a factor.
        """
        basket = self.copy_of()
        for item in basket.items:
            item.amount *= weight
        return basket

    def sort(self, criteria:List) -> 'Basket':
        """Sort the basket, each sort criteria is a tuple (field, direction) with direction being 1 (asc) or -1 (desc)"""
        if len(criteria) != 1:
            raise ValueError(f"Invalid sort criteria: {criteria} - currently only a single criteria is supported")

        field, direction = criteria[0]
        result = self.copy_of()

        # Special case for built-in fields
        if field == "ticker":
            result.items.sort(key=lambda item: item.ticker, reverse=(direction == -1))
        elif field == "weight" or field == "amount":
            result.items.sort(key=lambda item: item.amount, reverse=(direction == -1))
        else:
            # For custom columns, get the column and use its value for sorting
            column = self.get_column(field)
            if column is None:
                raise ValueError(f"Unknown sort field: {field}")

            # Sort based on column values
            result.items.sort(
                key=lambda item: column.value(item.ticker),
                reverse=(direction == -1)
            )

        return result


    def df(self) -> pd.DataFrame:
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
        """Convert to dictionary describing the basket - does NOT contain the actual data points."""
        return {
            "class": "Basket",
            "name": self.name,
            "items": [item.to_dict() for item in self.items],
            "columns": [col.to_dict() for col in self._columns]
        }


    @classmethod
    def from_dict(cls, data: dict) -> 'Basket':
        from . import entity_from_dict
        from .columns import column_from_dict

        items = []
        for item_data in data.get('items', []):
            items.append(entity_from_dict(item_data))

        basket = cls(items=items, name=data.get('name'))
        
        for col_data in data.get('columns', []):
            basket.add_column(column_from_dict(col_data))

        return basket

    @classmethod
    def from_symbols(cls, symbols: list[str], ignore_unresolved: bool = True, max_workers: int = 10) -> 'Basket':
        """
        Create a basket from a list of symbols using multithreading for faster symbol resolution.
        
        Args:
            symbols: List of symbol tickers
            ignore_unresolved: Whether to ignore symbols that can't be resolved
            max_workers: Maximum number of threads to use for parallel processing
            
        Returns:
            A new Basket containing the symbols
        """
        def create_basket_item(symbol: str) -> Optional[BasketItem]:
            """Create a single basket item, handling errors if ignore_unresolved is True."""
            try:
                print(f"Processing {symbol}...")
                result = BasketItem(symbol)
                print(f"✓ {symbol} resolved")
                return result
            except Exception as e:
                if ignore_unresolved:
                    print(f"⚠ Warning: Could not resolve symbol {symbol}: {e}")
                    return None
                else:
                    raise
        
        print(f"Creating basket from {len(symbols)} symbols using {max_workers} threads...")
        basket_items = []
        completed_count = 0
        
        # Use ThreadPoolExecutor to parallelize symbol resolution
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_symbol = {executor.submit(create_basket_item, symbol): symbol for symbol in symbols}
            
            # Collect results as they complete
            for future in as_completed(future_to_symbol):
                print("completed..")
                symbol = future_to_symbol[future]
                completed_count += 1
                try:
                    basket_item = future.result()
                    if basket_item is not None:
                        basket_items.append(basket_item)
                except Exception as e:
                    if not ignore_unresolved:
                        raise
                    print(f"⚠ Warning: Could not resolve symbol {symbol}: {e}")
                
                # Progress indicator
                print(f"Progress: {completed_count}/{len(symbols)} symbols processed")
        
        # Preserve original order by sorting basket_items according to symbols list
        symbol_to_item = {item.ticker: item for item in basket_items}
        ordered_items = [symbol_to_item[symbol] for symbol in symbols if symbol in symbol_to_item]
        
        print(f"✓ Basket creation complete! Successfully resolved {len(ordered_items)}/{len(symbols)} symbols")
        return cls(ordered_items)


# Dynamic method creation for all column types
def _create_column_method(column_class):
    """Create a method that adds the specified column to the basket."""
    def method(self):
        """Add column to the basket."""
        if not self.has_column(column_class.name()):
            self.add_column(column_class())
        return self
    
    method.__name__ = column_class.name()
    method.__doc__ = column_class.__doc__
    return method


# Scan all column classes and add methods to Basket
for name, obj in inspect.getmembers(columns):
    if (inspect.isclass(obj) and 
        hasattr(obj, 'name') and 
        hasattr(obj, 'description') and
        name.endswith('Column')):
        
        method_name = obj.name()
        method = _create_column_method(obj)
        setattr(Basket, method_name, method)





