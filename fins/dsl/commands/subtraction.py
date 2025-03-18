"""
Difference command for FINS.

This command removes elements of one basket from another using set difference.
"""

from typing import Type, Dict
from ...entities import Entity, Basket, BasketItem
from .command import Command, CommandArgs

class SubtractionCommand(Command):
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
    def input_type(self):
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
        if len(args.left_operands) != 1:
            raise RuntimeError("The operand must be specified")
        return
        
    def execute(self, args: CommandArgs) -> Entity:
        basket = args.left_operands[0]

        for right in args.right_operands:
            if not isinstance(right, Basket):
                raise TypeError("Expected right operand of type {}, got {}".format(type(right), right))
            basket = Basket.subtract(basket, right)

        return basket