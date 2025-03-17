"""
Add column command for FINS.

This command adds a column to a basket.
"""

from typing import Type, Dict
from ...entities.entity import Entity
from ...entities.basket import Basket
from .command import Command, CommandArgs

class AddColumnCommand(Command):
    """
    Command to add a column to a basket.
    
    Example:
        basket -> pe
        $tech_stocks mcap
        
    The command expects:
    - A Basket as input (implicit or explicit)
    - Column type as first right token
    - Optional column name as second right token
    """
    
    @property
    def input_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def output_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def description(self) -> str:
        return "Add a column to a basket"
        
    @property
    def right_tokens(self) -> Dict[str, str]:
        return {
            "column_type": "The type of column to add",
            "column_name": "Optional name for the column (defaults to column_type)"
        }
        
    @property
    def examples(self) -> Dict[str, str]:
        return {
            "basket -> pe": "Add a P/E ratio column to the basket",
            "$tech_stocks mcap": "Add a market cap column to the tech stocks basket",
            "AAPL MSFT -> eps growth_5y": "Add an EPS growth column named 'growth_5y'"
        }
        
    def validate_input(self, args: CommandArgs) -> None:
        """
        Validate command input and arguments.
        
        Args:
            args: The command arguments to validate
            
        Raises:
            TypeError: If input is not a Basket
            ValueError: If column type is not specified
        """
        # First validate input type
        super().validate_input(args)
        
        # Validate right tokens
        if not args.right_tokens:
            raise ValueError("Add column command requires a column type")
        
    def execute(self, args: CommandArgs) -> Entity:
        """
        Add a column to the input basket.
        
        Args:
            args: The command arguments containing:
                - implicit_input or left_input: The basket to add the column to
                - right_tokens: [column_type, [column_name]]
            
        Returns:
            The basket with the added column
            
        Raises:
            TypeError: If input is not a Basket
            ValueError: If column type is not specified
        """
        self.validate_input(args)
        basket = args.effective_input
        
        # Get column type
        column_type_token = args.right_tokens[0]
        if not column_type_token.is_literal:
            raise ValueError("Column type must be a literal value")
        column_type = column_type_token.as_literal()
        
        # Get column name (defaults to column type)
        column_name = column_type
        if len(args.right_tokens) > 1:
            column_name_token = args.right_tokens[1]
            if not column_name_token.is_literal:
                raise ValueError("Column name must be a literal value")
            column_name = column_name_token.as_literal()
        
        # In a real implementation, this would calculate values
        # For now, just add a dummy column
        values = {symbol: 1.0 for symbol in basket.symbols}
        basket.add_column(column_name, values)
            
        return basket 