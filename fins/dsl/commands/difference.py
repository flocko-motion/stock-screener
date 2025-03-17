"""
Difference command for FINS.

This command removes elements of one basket from another using set difference.
"""

from typing import Type, Dict
from ...entities.entity import Entity
from ...entities.basket import Basket
from ...entities.symbol import Symbol
from .command import Command, CommandArgs

class DifferenceCommand(Command):
    """
    Command to remove elements of one basket from another using set difference.
    
    Example:
        basket1 -> - basket2
        $tech_stocks - $faang_stocks
        
    The command expects:
    - A Basket as input (implicit or explicit)
    - Another basket as right token
    """
    
    @property
    def input_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def output_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def description(self) -> str:
        return "Remove elements of one basket from another using set difference"
        
    @property
    def right_tokens(self) -> Dict[str, str]:
        return {
            "operand": "The basket whose elements to remove"
        }
        
    @property
    def examples(self) -> Dict[str, str]:
        return {
            "basket1 -> - basket2": "Remove elements of basket2 from basket1",
            "$tech_stocks - $faang_stocks": "Remove FAANG stocks from tech stocks",
            "AAPL MSFT GOOGL -> - GOOGL": "Remove GOOGL from a basket containing AAPL, MSFT, and GOOGL"
        }
        
    def validate_input(self, args: CommandArgs) -> None:
        """
        Validate command input and arguments.
        
        Args:
            args: The command arguments to validate
            
        Raises:
            TypeError: If input is not a Basket
            ValueError: If operand is not specified
        """
        # First validate input type
        super().validate_input(args)
        
        # Validate right tokens
        if not args.right_input:
            raise ValueError("Difference command requires an operand")
        
    def execute(self, args: CommandArgs) -> Entity:
        """
        Remove elements of one basket from another using set difference.
        
        Args:
            args: The command arguments containing:
                - implicit_input or left_input: The first basket
                - right_tokens: [operand]
            
        Returns:
            The resulting basket
            
        Raises:
            TypeError: If input is not a Basket
            ValueError: If operand is not specified
        """
        self.validate_input(args)
        basket = args.effective_input
        
        # Get operand
        operand_token = args.right_input[0]
        operand = operand_token.as_literal() if operand_token.is_literal else operand_token.get_reference_name()
        
        # Get symbols from operand
        operand_symbol_names = set()
        if isinstance(operand, Basket):
            operand_symbol_names = {symbol.name for symbol in operand.symbols}
        elif isinstance(operand, dict) and operand.get("type") == "basket":
            operand_symbol_names = {s["ticker"] for s in operand.get("symbols", [])}
        elif isinstance(operand, str):
            # Assume it's a symbol name
            operand_symbol_names = {operand}
        
        # Remove symbols that are in the operand
        filtered_symbols = [s for s in basket.symbols if s.name not in operand_symbol_names]
        
        # Create new basket
        result = Basket(filtered_symbols)
        
        # Copy columns from input basket
        for name, values in basket.columns.items():
            result.add_column(name, {
                symbol: values[symbol]
                for symbol in filtered_symbols
                if symbol in values
            })
            
        return result 