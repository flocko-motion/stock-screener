"""
Spread command for FINS.

This command expands a symbol (like an ETF) into its constituents.
"""

from typing import Type, Dict
from ...storage.entity import Entity
from ...entities.basket import Basket
from ...entities.symbol import Symbol
from .command import Command, CommandArgs

class SpreadCommand(Command):
    """
    Command to expand a symbol (like an ETF) into its constituents.
    
    Example:
        basket -> spread SPY
        $etfs spread QQQ
        
    The command expects:
    - A Basket as input (implicit or explicit)
    - Symbol to expand as right token
    """
    
    @property
    def input_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def output_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def description(self) -> str:
        return "Expand a symbol (like an ETF) into its constituents"
        
    @property
    def right_tokens(self) -> Dict[str, str]:
        return {
            "symbol": "The symbol to expand"
        }
        
    @property
    def examples(self) -> Dict[str, str]:
        return {
            "basket -> spread SPY": "Expand SPY into its constituents",
            "$etfs spread QQQ": "Expand QQQ into its constituents",
            "SPY -> spread": "Expand SPY into its constituents"
        }
        
    def validate_input(self, args: CommandArgs) -> None:
        """
        Validate command input and arguments.
        
        Args:
            args: The command arguments to validate
            
        Raises:
            TypeError: If input is not a Basket
            ValueError: If symbol is not specified
        """
        # First validate input type
        super().validate_input(args)
        
        # Validate right tokens
        if not args.right_tokens:
            raise ValueError("Spread command requires a symbol to expand")
        
    def execute(self, args: CommandArgs) -> Entity:
        """
        Expand a symbol (like an ETF) into its constituents.
        
        Args:
            args: The command arguments containing:
                - implicit_input or left_input: The basket containing the symbol
                - right_tokens: [symbol]
            
        Returns:
            The expanded basket
            
        Raises:
            TypeError: If input is not a Basket
            ValueError: If symbol is not specified
        """
        self.validate_input(args)
        
        # Get symbol name
        symbol_token = args.right_tokens[0]
        symbol_name = symbol_token.as_literal() if symbol_token.is_literal else symbol_token.get_reference_name()
        
        # In a real implementation, this would fetch the constituents
        # For now, just return a basket with some dummy constituents
        constituents = [Symbol(f"{symbol_name}_{i}") for i in range(1, 6)]
        result = Basket(constituents)
            
        return result 