"""
PE (Price/Earnings) ratio column command.

This command calculates the P/E ratio for each symbol in a basket.
It can be used both as an analysis column and as a filter.
"""

from typing import Any
from ...entities.entity import Entity
from ...entities.basket import Basket
from .command import Command, CommandArgs
from .function import ColumnCommand

class PEColumnCommand(ColumnCommand):
    """
    Calculate Price/Earnings ratio for symbols.
    
    Examples:
        basket -> pe  # Just add PE column
        basket -> pe < 20  # Add PE column and filter to PE < 20
        $tech_stocks pe > $min_pe  # Filter tech stocks by PE
    """
    
    @property
    def description(self) -> str:
        return "Calculate Price/Earnings ratio for each symbol"
        
    def calculate(self, symbol: Entity) -> Any:
        """
        Calculate P/E ratio for a symbol.
        
        Args:
            symbol: The symbol to calculate for
            
        Returns:
            The P/E ratio or None if earnings are 0/missing
        """
        if not hasattr(symbol, "price") or not hasattr(symbol, "earnings"):
            return None
            
        if symbol.earnings == 0:
            return None
            
        return symbol.price / symbol.earnings 