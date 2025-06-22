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
from .entity import Entity
from .basket_item import BasketItem
from .column import Column


class Basket(Entity):
    """
    A weighted list of BasketItems (wrapped Symbols) and a lot of column-functions for analytics.
    """
    
    def __init__(self, *symbols, items: list[BasketItem] = None, name: Optional[str] = None):
        """Initialize a basket."""
        super().__init__()
        self._name = name
        self._items = list(symbols) if len(symbols) > 0 else (items or [])
        self._columns: List[Column] = []

    def __str__(self) -> str:
        """Return the string representation of the basket."""
        if not self._items:
            return ""
            
        # Simple text representation preserving order
        return "\n".join(f"{item.amount:g}x {item.ticker}" for item in sorted(self._items, key=lambda x: (-x.amount, x.ticker)))
    
    def __repr__(self) -> str:
        """Return a simple string representation of the basket."""
        if not self._items:
            return "Empty Basket"
        return repr(self.df())
    
    def _repr_html_(self) -> str:
        """Return HTML representation for rich Jupyter display."""
        if not self._items:
            return "<i>Empty Basket</i>"
        return self.df()._repr_html_()
    
    def __len__(self) -> int:
        return len(self._items)
    
    def __iter__(self) -> Iterator[BasketItem]:
        return iter(self._items)
    
    def __contains__(self, other) -> bool:
        if isinstance(other, str):
            ticker = other
        elif isinstance(other, BasketItem):
            ticker = other.ticker
        else:
            raise Exception(f"Unsupported type {type(other)}")

        return any(item.ticker == ticker for item in self._items)



    def __add__(self, other) -> 'Basket':
        """Add operator: Basket + Basket or Basket + BasketItem."""
        if isinstance(other, Basket):
            result = Basket(name=self._name)

            # Add all items from this basket
            for item in self._items:
                result._add_item(BasketItem(item.ticker, item.amount))

            # Add all items from the other basket
            for item in other._items:
                result._add_item(BasketItem(item.ticker, item.amount))

            # Merge columns
            result._columns = self._columns.copy()
            for col in other._columns:
                if col not in result._columns:
                    result._columns.append(col)

            return result
        elif isinstance(other, BasketItem):
            new_basket = self._copy_of()
            new_basket._add_item(other)
            return new_basket
        else:
            return NotImplemented

    def __sub__(self, other) -> 'Basket':
        if isinstance(other, Basket):
            result = Basket(name=self._name)

            for item in self._items:
                if other.__contains__(item):
                    continue
                result._add_item(BasketItem(item.ticker, item.amount))

            result._columns = self._columns.copy()

            return result
        elif isinstance(other, BasketItem):
            new_basket = self._copy_of()
            new_basket._remove_item(other.ticker)
            return new_basket
        else:
            return NotImplemented

    def __and__(self, other) -> 'Basket':
        """Intersection operator: Basket & Basket or Basket & BasketItem."""
        if isinstance(other, Basket):
            # Basket & Basket - intersection
            result = Basket(name=self._name)

            # Find symbols that are in both baskets
            this_symbols = {item.ticker for item in self._items}
            other_symbols = {item.ticker for item in other._items}
            common_symbols = this_symbols.intersection(other_symbols)

            # Add items for common symbols with minimum quantity
            for item in self._items:
                if item.ticker in common_symbols:
                    other_item = next(i for i in other._items if i.ticker == item.ticker)
                    quantity = min(item.amount, other_item.amount)
                    result._add_item(BasketItem(item.ticker, quantity))

            # Merge columns from both baskets
            result._columns = self._columns.copy()
            for col in other._columns:
                if col not in result._columns:
                    result._columns.append(col)

            return result

        elif isinstance(other, BasketItem):
            # Basket & BasketItem - return basket with item if it exists, empty otherwise
            if other.ticker in self:
                result = Basket(name=self._name)
                existing_item = next(item for item in self._items if item.ticker == other.ticker)
                result._add_item(BasketItem(other.ticker, min(existing_item.amount, other.amount)))
                result._columns = self._columns.copy()
                return result
            else:
                return Basket(name=self._name)  # Empty basket
        else:
            return NotImplemented

    def __xor__(self, other) -> 'Basket':
        """Symmetric difference operator: Basket ^ Basket or Basket ^ BasketItem."""
        if isinstance(other, Basket):
            # Basket ^ Basket - symmetric difference (items in either but not both)
            result = Basket(name=self._name)

            # Get all symbols from both baskets
            this_symbols = {item.ticker for item in self._items}
            other_symbols = {item.ticker for item in other._items}

            # Add items that are only in this basket
            for item in self._items:
                if item.ticker not in other_symbols:
                    result._add_item(BasketItem(item.ticker, item.amount))

            # Add items that are only in the other basket
            for item in other._items:
                if item.ticker not in this_symbols:
                    result._add_item(BasketItem(item.ticker, item.amount))

            # Merge columns from both baskets
            result._columns = self._columns.copy()
            for col in other._columns:
                if col not in result._columns:
                    result._columns.append(col)

            return result

        elif isinstance(other, BasketItem):
            # Basket ^ BasketItem - toggle the item (remove if exists, add if doesn't)
            result = self._copy_of()
            if other.ticker in self:
                result._remove_item(other.ticker)
            else:
                result._add_item(other)
            return result
        else:
            return NotImplemented

    def __mul__(self, other) -> 'Basket':
        """Multiplication operator: Basket * number to scale all weights."""
        if isinstance(other, (int, float)):
            result = self._copy_of()
            for item in result._items:
                item.amount *= other
            return result
        else:
            return NotImplemented

    def __rmul__(self, other) -> 'Basket':
        """Reverse multiplication operator: number * Basket."""
        return self.__mul__(other)

    def _add_item(self, item: BasketItem) -> None:
        for existing_item in self._items:
            if existing_item.ticker == item.ticker:
                existing_item.amount += item.amount
                return
        
        self._items.append(item)

    def _remove_item(self, ticker: str) -> None:
        self._items = [item for item in self._items if item.ticker != ticker]

    def _copy_of(self) -> 'Basket':
        copy = Basket(name=self._name)
        for item in self._items:
            copy._add_item(BasketItem(item.ticker, item.amount))
        copy._columns = self._columns.copy()
        return copy

    def _add_column(self, column: Column) -> 'Basket':
        """Add a column to the basket and return a new basket."""
        result = self._copy_of()
        result._columns.append(column)
        return result

    def _remove_column(self, name: str) -> 'Basket':
        """Remove a column by name/alias and return a new basket."""
        result = self._copy_of()
        result._columns = [col for col in result._columns if col.alias() != name]
        return result

    def _has_column(self, name: str) -> bool:
        """Check if basket has a column by name/alias."""
        return any(col.alias() == name for col in self._columns)

    def _get_column(self, name: str) -> Optional[Column]:
        """Get a column by name/alias."""
        return next((col for col in self._columns if col.alias() == name), None)

    def _list_columns(self) -> List[str]:
        """Get list of column names/aliases in order."""
        return [col.alias() for col in self._columns]



    def sort(self, criteria:List) -> 'Basket':
        """Sort the basket, each sort criteria is a tuple (field, direction) with direction being 1 (asc) or -1 (desc)"""
        if len(criteria) != 1:
            raise ValueError(f"Invalid sort criteria: {criteria} - currently only a single criteria is supported")

        field, direction = criteria[0]
        result = self._copy_of()

        # Special case for built-in fields
        if field == "ticker":
            result._items.sort(key=lambda item: item.ticker, reverse=(direction == -1))
        elif field == "weight" or field == "amount":
            result._items.sort(key=lambda item: item.amount, reverse=(direction == -1))
        else:
            # For custom columns, get the column and use its value for sorting
            column = self._get_column(field)
            if column is None:
                raise ValueError(f"Unknown sort field: {field}")

            # Sort based on column values
            result._items.sort(
                key=lambda item: column.value(item.ticker),
                reverse=(direction == -1)
            )

        return result


    def df(self) -> pd.DataFrame:
        """Convert basket to DataFrame with all column values."""
        # Start with basic ticker data
        data = {
            'ticker': [item.ticker for item in self._items],
            'weight': [item.amount for item in self._items]
        }
        
        # Add column values in order
        for col in self._columns:
            data[col.alias()] = [col.value(item.ticker) for item in self._items]
            
        return pd.DataFrame(data)
    
    def to_dict(self) -> dict:
        """Convert to dictionary describing the basket - does NOT contain the actual data points."""
        return {
            "class": "Basket",
            "name": self._name,
            "items": [item.to_dict() for item in self._items],
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
            basket._add_column(column_from_dict(col_data))

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
        if not self._has_column(column_class._name()):
            self._add_column(column_class())
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





