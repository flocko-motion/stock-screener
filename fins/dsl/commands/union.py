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
    Command to combine two baskets using set union.
    
    Example:
        basket1 -> + basket2
        $tech_stocks + $finance_stocks
        
    The command expects:
    - A Basket as input (implicit or explicit)
    - Another basket as right token
    """
    
    @property
    def input_type(self):
        return Sequence[Entity]
        
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
        
    def execute(self, args: CommandArgs) -> Entity:
        """
        Combine the input basket with another basket using set union.
        
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
        self.validate_input(args)
        basket = args.effective_input
        
        # Get operand
        operand_token = args.right_operands[0]
        operand = operand_token.as_literal() if operand_token.is_literal else operand_token.get_reference_name()
        
        # Get symbols from operand
        operand_symbols = []
        if isinstance(operand, Basket):
            operand_symbols = operand.symbols
        elif isinstance(operand, dict) and operand.get("type") == "basket":
            operand_symbols = [Symbol(s["ticker"]) for s in operand.get("symbols", [])]
        elif isinstance(operand, str):
            # Assume it's a symbol name
            operand_symbols = [Symbol(operand)]
        
        # Combine symbols
        all_symbols = list(basket.symbols) + operand_symbols
        
        # Remove duplicates (by name)
        unique_symbols = []
        seen = set()
        for symbol in all_symbols:
            if symbol.name not in seen:
                unique_symbols.append(symbol)
                seen.add(symbol.name)
        
        # Create new basket
        result = Basket(unique_symbols)
        
        # Copy columns from input basket
        for name, values in basket.columns.items():
            result.add_column(name, values)
            
        return result 