from typing import Optional

from ..plugin import Plugin
from .. import Basket


class Top(Plugin):
    """
    Plugin that keeps only the first n items from a basket.
    
    This plugin truncates the basket to contain only the first n items,
    preserving their original order and weights.
    
    Args:
        n: Number of items to keep (must be positive)
        alias: Optional alias for the plugin
    
    Examples:
        basket(Top(5))           # Keep only first 5 items
        basket(Top(10))          # Keep only first 10 items
        basket(Sort() >> Top(3)) # Sort then keep top 3
    """
    
    def __init__(self, n: int, alias: Optional[str] = None):
        if not isinstance(n, int) or n <= 0:
            raise ValueError("n must be a positive integer")
        
        super().__init__(alias)
        self.n = n
    
    def run(self, runtime: 'BasketRuntime'):
        """Apply the Top filter to keep only the first n items."""
        current_items = runtime.basket_items()
        
        # If basket already has n or fewer items, no change needed
        if len(current_items) <= self.n:
            return
        
        # Keep only the first n items
        top_items = current_items[:self.n]
        
        # Create new basket with top items
        filtered_basket = Basket(items=top_items, name=runtime.basket()._name)
        
        # Update the DataFrame to keep only the first n rows
        if hasattr(runtime, '_df') and runtime._df is not None:
            runtime._df = runtime._df.head(self.n).reset_index(drop=True)
        
        # Update output data to keep only the first n items
        if hasattr(runtime, '_output_data') and runtime._output_data is not None:
            old_items = runtime._output_data._items
            new_items = {}
            for i in range(min(self.n, len(old_items))):
                if i in old_items:
                    new_items[i] = old_items[i]
            runtime._output_data._items = new_items
        
        # Update the basket reference
        runtime._basket = filtered_basket
    
    def __repr__(self) -> str:
        return f"Top({self.n})" 