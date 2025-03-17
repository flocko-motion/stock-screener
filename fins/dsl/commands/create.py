"""
Create basket command for FINS.

This command creates a new basket from a list of symbols.
"""

from typing import Type, Dict, List, Optional

from ...entities import Entity, Basket, Symbol, Token
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
    def input_type(self) -> Optional[Type[Entity]]:
        return None  # This command doesn't require input
        
    @property
    def output_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def description(self) -> str:
        return "Create a new basket from a list of symbols"
        
    @property
    def right_tokens(self) -> Dict[str, str]:
        return {
            "symbols": "List of symbols to include in the basket"
        }
        
    @property
    def examples(self) -> Dict[str, str]:
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
        # This command doesn't require input, so we don't call super().validate_input()
        
        # Validate right tokens
        if not args.right_operands:
            raise ValueError("Create basket command requires at least one symbol")
        
    def execute(self, args: CommandArgs) -> Entity:
        """
        Create a new basket from a list of symbols.
        As args we accept both generic Token objects or Symbol objects.
        
        Args:
            args: The command arguments containing:
                - right_tokens: List of symbols
            
        Returns:
            The created basket
            
        Raises:
            ValueError: If no symbols are specified
        """
        self.validate_input(args)
        
        # Convert args to Symbol objects
        symbol_objects = []
        for arg in args.right_operands:
            if isinstance(arg, Token):
                if arg.is_literal:
                    symbol_objects.append(Symbol(arg.as_literal()))
                else:
                    raise NotImplemented("reference not implemented")
            elif isinstance(arg, Symbol):
                symbol_objects.append(arg)

        return Basket.from_tickers(symbol_objects)
