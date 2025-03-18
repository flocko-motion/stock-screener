"""
Create basket command for FINS.

This command creates a new basket from a list of symbols.
"""

from typing import Type, Optional

from ...entities import Entity, Basket, BasketItem, Token
from .command import Command, CommandArgs

class CreateBasketCommand(Command):
    """
    Command to create a new basket from a list of symbols.
    
    Example:
        AAPL MSFT GOOGL
        
    The command expects:
    - No input (can be None)
    - List of symbols as right tokens
    """
    
    @property
    def input_type(self):
        return None  # This command doesn't require input
        
    @property
    def output_type(self):
        return Basket
        
    @property
    def description(self) -> str:
        return "Create a new basket from a list of symbols"
        
    @property
    def right_tokens(self) -> dict[str, str]:
        return {
            "symbols": "List of symbols to include in the basket"
        }
        
    @property
    def examples(self) -> dict[str, str]:
        return {
            "AAPL MSFT GOOGL": "Create a basket with Apple, Microsoft, and Google",
            "SPY QQQ IWM": "Create a basket with major ETFs"
        }
        
    def validate_input(self, args: CommandArgs) -> None:
        """
        Validate command input and arguments.
        
        Args:
            args: The command arguments to validate
            
        Raises:
            ValueError: If no symbols are specified
        """
        return

    def execute(self, args: CommandArgs) -> Entity:
        """
        Create a new basket from a list of symbols.

        Args:
            args: The command arguments containing:
                - right_operands: List of ticker names
            
        Returns:
            The created basket
            
        Raises:
            ValueError: If no symbols are specified
        """
        items = list[BasketItem]()
        for ticker in args.right_operands:
            if not isinstance(ticker, BasketItem):
                raise ValueError(f"Invalid ticker: {ticker}, expected BasketItem, got {type(ticker)}")
            items.append(ticker)

        return Basket(items)
