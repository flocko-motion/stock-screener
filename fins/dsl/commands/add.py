"""
Add column command for FINS.

This command adds symbols to a basket.
"""

from typing import Type
from ...entities.entity import Entity
from ...entities.basket import Basket
from ...entities.symbol import Symbol
from .command import Command, CommandArgs

class AddCommand(Command):
    """
    Command to add symbols to a basket.
    
    Example:
        basket -> + NFLX AMZN  # Add NFLX and AMZN to basket
        $tech_stocks + NFLX    # Explicit syntax
        
    The command expects:
    - A Basket as input (implicit or explicit)
    - Symbol(s) as right tokens
    """
    
    @property
    def input_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def output_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def description(self) -> str:
        return "Add symbols to a basket"
        
    @property
    def right_tokens(self) -> dict:
        return {
            "symbols": "Symbols to add to the basket"
        }
        
    @property
    def examples(self) -> dict:
        return {
            "basket -> + NFLX AMZN": "Add NFLX and AMZN to the basket",
            "$tech_stocks + NFLX": "Add NFLX to tech_stocks (explicit syntax)"
        }
        
    def validate_input(self, args: CommandArgs) -> None:
        """
        Validate command input and arguments.
        
        Args:
            args: The command arguments to validate
            
        Raises:
            TypeError: If input is not a Basket
            ValueError: If no symbols are provided
        """
        # First validate input type
        super().validate_input(args)
        
        # Validate right tokens
        if not args.right_operands:
            raise ValueError("At least one symbol must be specified")
        
    def execute(self, args: CommandArgs) -> Entity:
        """
        Add symbols to the input basket.
        
        Args:
            args: The command arguments containing:
                - implicit_input or left_input: The basket to add to
                - right_tokens: Symbols to add
            
        Returns:
            The basket with added symbols
            
        Raises:
            TypeError: If input is not a Basket
            ValueError: If no symbols are provided
        """
        self.validate_input(args)
        basket = args.effective_input
        
        # Get symbols to add
        new_symbols = []
        for token in args.right_operands:
            if not token.is_literal:
                raise ValueError(f"Symbol '{token}' must be a literal value")
                
            symbol_name = token.as_literal()
            new_symbols.append(Symbol(symbol_name))
            
        # Create a new basket with all symbols
        all_symbols = basket.symbols + new_symbols
        result = Basket(all_symbols)
        
        # Copy columns from input basket
        for name, values in basket.columns.items():
            result.add_column(name, values)
            
        return result 