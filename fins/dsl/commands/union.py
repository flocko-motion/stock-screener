"""
Union command for FINS.

This command combines two baskets using set union.
"""
from collections.abc import Sequence
from typing import Type, Optional
from ...entities import Entity, Basket, BasketItem
from .command import Command, CommandArgs

class UnionCommand(Command):
    """
    Command to combine two baskets using superimposition - a union in which items from latter basket overwrite identical items of earlier basket.
    
    Example:
        basket1 -> + basket2
        $tech_stocks + $finance_stocks
        
    The command expects:
    - A Basket as input (implicit or explicit)
    - Another basket as right token
    """
    
    @property
    def input_type(self):
        return None
        
    @property
    def output_type(self):
        return Basket
        
    @property
    def description(self) -> str:
        return "Combine two baskets using set union"
        
    @property
    def right_tokens(self) -> dict[str, str]:
        return {
            "operand": "The second basket to combine with"
        }
        
    @property
    def examples(self) -> dict[str, str]:
        return {
            "basket1 -> + basket2": "Combine basket1 and basket2",
            "$tech_stocks + $finance_stocks": "Combine tech stocks and finance stocks",
            "AAPL MSFT -> + GOOGL": "Add GOOGL to a basket containing AAPL and MSFT"
        }

    def validate_input(self, args: CommandArgs) -> None:
        """
        Validate command input and arguments.

        Args:
            args: The command arguments to validate

        Raises:
            ValueError: If no symbols are specified
        """
        if len(args.left_operands) != 1:
            raise ValueError("Expected 1 left operand, got {}".format(len(args.left_operands)))

    def execute(self, args: CommandArgs) -> Entity:
        """
        Combine the input basket with another basket by adding their contents together.
        
        Args:
            args: The command arguments containing:
                - implicit_input or left_input: The first basket
                - right_tokens: [operand]
            
        Returns:
            The combined basket
            
        Raises:
            TypeError: If input is not a Basket
            ValueError: If operand is not specified
        """
        basket = args.left_operands[0]
        
        for right in args.right_operands:
            if not isinstance(right, Basket):
                raise TypeError("Expected right operand of type {}, got {}".format(type(right), right))
            basket = Basket.union(basket, right)

        return basket