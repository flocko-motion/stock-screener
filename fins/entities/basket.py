"""
Basket Entity

This module defines the Basket class, which represents a collection of financial symbols
with associated data and analysis columns.
"""

from typing import Optional, Iterator
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from .entity import Entity
from .basket_item import BasketItem


class Basket(Entity):
    """
    A weighted list of BasketItems (wrapped Symbols) and a lot of column-functions for analytics.
    """
    
    def __init__(self, *symbols, items: list[BasketItem] = None, name: Optional[str] = None):
        """Initialize a basket."""
        super().__init__()
        self._name = name
        self._items = list(symbols) if len(symbols) > 0 else (items or [])

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
            # Create lookup dict for other basket items
            other_dict = {item.ticker: item.amount for item in other._items}
            this_tickers = {item.ticker for item in self._items}
            
            # Update existing items and preserve order
            updated_items = [
                item if item.ticker not in other_dict  # reuse unchanged items
                else BasketItem(item.ticker, item.amount + other_dict[item.ticker])  # create new with combined amount
                for item in self._items
            ]
            
            # Add new items from other basket (items not in this basket) - reuse existing items
            new_items = [
                item  # reuse existing item from other basket
                for item in other._items
                if item.ticker not in this_tickers
            ]
            
            return Basket(name=self._name, items=updated_items + new_items)
            
        elif isinstance(other, BasketItem):
            # Simple: update existing or append new
            has_item = any(item.ticker == other.ticker for item in self._items)
            
            new_items = [
                item if item.ticker != other.ticker else BasketItem(item.ticker, item.amount + other.amount)
                for item in self._items
            ] + ([] if has_item else [other])
            
            return Basket(name=self._name, items=new_items)
        else:
            return NotImplemented

    def __sub__(self, other) -> 'Basket':
        """Subtract operator: Basket - Basket or Basket - BasketItem with weight handling."""
        if isinstance(other, Basket):
            other_dict = {item.ticker: item.amount for item in other._items}
            
            new_items = [
                item if item.ticker not in other_dict  # reuse unchanged items
                else (BasketItem(item.ticker, new_amount) if new_amount != item.amount else item)
                for item in self._items
                if item.ticker not in other_dict or (new_amount := item.amount - other_dict[item.ticker]) > 0
            ]
            
            return Basket(name=self._name, items=new_items)
        
        elif isinstance(other, BasketItem):
            new_items = [
                item if item.ticker != other.ticker  # reuse unchanged items
                else (BasketItem(item.ticker, new_amount) if new_amount != item.amount else item)
                for item in self._items
                if item.ticker != other.ticker or (new_amount := item.amount - other.amount) > 0
            ]
            
            return Basket(name=self._name, items=new_items)
        else:
            return NotImplemented

    def __truediv__(self, other) -> 'Basket':
        """Slash operator: Basket / Basket or Basket / BasketItem to slash (remove) items."""
        if isinstance(other, Basket):
            # Basket / Basket - remove all items that exist in other basket
            other_tickers = {item.ticker for item in other._items}
            remaining_items = [item for item in self._items if item.ticker not in other_tickers]
            return Basket(items=remaining_items, name=self._name)
        
        elif isinstance(other, BasketItem):
            # Basket / BasketItem - remove the specific item completely
            remaining_items = [item for item in self._items if item.ticker != other.ticker]
            return Basket(items=remaining_items, name=self._name)
        else:
            return NotImplemented

    def __and__(self, other) -> 'Basket':
        """Intersection operator: Basket & Basket or Basket & BasketItem."""
        if isinstance(other, Basket):
            # Basket & Basket - intersection with summed weights
            other_dict = {item.ticker: item for item in other._items}
            intersection_items = [
                BasketItem(item.ticker, item.amount + other_dict[item.ticker].amount)
                for item in self._items if item.ticker in other_dict
            ]
            return Basket(items=intersection_items, name=self._name)

        elif isinstance(other, BasketItem):
            # Basket & BasketItem - return basket with item if it exists, with summed weight
            matching_items = [
                BasketItem(item.ticker, item.amount + other.amount)
                for item in self._items if item.ticker == other.ticker
            ]
            return Basket(items=matching_items, name=self._name)
        else:
            return NotImplemented

    def __xor__(self, other) -> 'Basket':
        """Symmetric difference operator: Basket ^ Basket or Basket ^ BasketItem."""
        if isinstance(other, Basket):
            # Basket ^ Basket - symmetric difference (items in either but not both)
            other_symbols = {item.ticker for item in other._items}
            this_symbols = {item.ticker for item in self._items}
            
            # Items only in this basket + items only in other basket
            symmetric_diff_items = (
                [item for item in self._items if item.ticker not in other_symbols] +
                [item for item in other._items if item.ticker not in this_symbols]
            )
            return Basket(items=symmetric_diff_items, name=self._name)

        elif isinstance(other, BasketItem):
            # Basket ^ BasketItem - toggle the item (remove if exists, add if doesn't)
            if other.ticker in self:
                # Remove the item
                remaining_items = [item for item in self._items if item.ticker != other.ticker]
                return Basket(items=remaining_items, name=self._name)
            else:
                # Add the item
                return Basket(items=self._items + [other], name=self._name)
        else:
            return NotImplemented

    def __mul__(self, other) -> 'Basket':
        """Multiplication operator: Basket * number to scale all weights."""
        if isinstance(other, (int, float)):
            scaled_items = [BasketItem(item.ticker, item.amount * other) for item in self._items]
            return Basket(items=scaled_items, name=self._name)
        else:
            return NotImplemented

    def __rmul__(self, other) -> 'Basket':
        """Reverse multiplication operator: number * Basket."""
        return self.__mul__(other)


    def __call__(self, arg): # -> BasketRuntime
        """Execute a pipeline of Plugins and return the processed basket."""
        from . import Plugin, BasketPipeline, BasketRuntime

        if isinstance(arg, Plugin):
            return BasketPipeline(arg).run(self)
        elif isinstance(arg, BasketPipeline):
            return arg.run(self)
        else:            
            raise TypeError(f"Expected Plugin or BasketPipeline, got {type(arg)}")
        
    def items(self):
        return self._items


    def df(self) -> pd.DataFrame:
        """Convert basket to DataFrame with all column values."""
        data = {
            'ticker': [item.ticker for item in self._items],
            'weight': [item.amount for item in self._items]
        }
        return pd.DataFrame(data)
    
    def to_dict(self) -> dict:
        """Convert to dictionary describing the basket - does NOT contain the actual data points."""
        return {
            "class": "Basket",
            "name": self._name,
            "items": [item.to_dict() for item in self._items],
        }


    @classmethod
    def from_dict(cls, data: dict) -> 'Basket':
        from . import entity_from_dict

        items = []
        for item_data in data.get('items', []):
            items.append(entity_from_dict(item_data))

        basket = cls(items=items, name=data.get('name'))

        return basket

    @classmethod
    def from_tickers(cls, tickers: list[str], name: Optional[str] = None) -> 'Basket':
        print(f"Creating basket from {len(tickers)} tickers")
        basket_items = [BasketItem(ticker, amount=1.0) for ticker in tickers]

        basket = cls(items=basket_items, name=name)
        basket.fetch_symbols()
        return basket

    def fetch_symbols(self, max_workers: int = 10) -> None:
        """
        Fetch symbols for all basket items concurrently.
        
        Args:
            max_workers: Maximum number of concurrent threads (default: 10)
        """
        from fins.financial import Symbol
        from fins.utils import ProgressTracker
        
        tracker = ProgressTracker(len(self._items), "Fetching symbols")
        
        def fetch_symbol_for_item(item: BasketItem):
            if item._symbol is None:
                item._symbol = Symbol.get(item.ticker)
            tracker.next()
            return item
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_symbol_for_item, item): item for item in self._items}
            for future in as_completed(futures):
                future.result()  # This will raise any exceptions that occurred
        
        tracker.done()

