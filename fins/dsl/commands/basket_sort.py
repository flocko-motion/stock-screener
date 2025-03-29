"""
Sort column command for FINS.

This command sorts a basket of symbols based on a specified column.
"""

from typing import Type

from fins.entities.entity import Entity
from fins.entities.basket import Basket

from fins.dsl import *

class SortColumnCommand(Command):
    """
    Command to sort a basket by a specified column.
    
    Example:
        basket -> sort mcap desc
        $tech_stocks sort mcap desc
        
    The command expects:
    - A Basket as input (implicit or explicit)
    - Column name as first right token
    - Optional sort order ('asc'/'desc') as second right token
    """
    
    @property
    def input_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def output_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def description(self) -> str:
        return "Sort a basket by a specified column"
        
    @property
    def right_tokens(self) -> dict:
        return {
            "column": "The column to sort by",
            "order": "Sort order ('asc' or 'desc', default: 'asc')"
        }
        
    @property
    def examples(self) -> dict:
        return {
            "basket -> sort mcap desc": "Sort basket by market cap in descending order",
            "basket sort mcap desc": "Same as above, using explicit syntax",
            "$tech_stocks sort pe": "Sort tech stocks by P/E ratio in ascending order"
        }
        
    def validate_input(self, args: CommandArgs) -> None:
        """
        Validate command input and arguments.
        
        Args:
            args: The command arguments to validate
            
        Raises:
            TypeError: If input is not a Basket
            ValueError: If column is not specified or order is invalid
        """
        # First validate input type
        super().validate_input(args)
        
        # Validate right tokens
        if not args.right_operands:
            raise ValueError("Column must be specified for sorting")
            
        if len(args.right_operands) > 1:
            order_token = args.right_operands[1]
            if not order_token.is_literal:
                raise ValueError("Sort order must be a literal value")
            order = order_token.as_literal()
            if not isinstance(order, str) or order not in ("asc", "desc"):
                raise ValueError("Order must be 'asc' or 'desc'")
        
    def execute(self, args: CommandArgs) -> Output:
        """
        Sort the input basket by the specified column.
        
        Args:
            args: The command arguments containing:
                - implicit_input or left_input: The basket to sort
                - right_tokens: [column, [order]]
            
        Returns:
            The sorted basket
            
        Raises:
            TypeError: If input is not a Basket
            ValueError: If column is not specified or order is invalid
        """
        self.validate_input(args)
        basket = args.effective_input
        
        # Get column name
        column_token = args.right_operands[0]
        if not column_token.is_literal:
            raise ValueError("Column name must be a literal value")
        column = column_token.as_literal()
        
        # Get sort order
        order = "asc"
        if len(args.right_operands) > 1:
            order_token = args.right_operands[1]
            order = order_token.as_literal()
        
        # Sort the basket
        reverse = order == "desc"
        sorted_symbols = sorted(
            basket.symbols,
            key=lambda s: getattr(s, column, 0) or 0,  # Handle None values
            reverse=reverse
        )
        
        # Create new basket with sorted symbols
        result = Basket(sorted_symbols)
        
        # Copy columns from input basket
        for name, values in basket.columns.items():
            result.add_column(name, values)
            
        return Output(result)