"""
Filter command for FINS.

This command filters a basket of symbols based on a specified condition.
"""

from typing import Type, Dict
from ...entities.entity import Entity
from ...entities.basket import Basket
from .command import Command, CommandArgs

class FilterCommand(Command):
    """
    Command to filter a basket by a specified condition.
    
    Example:
        basket -> filter pe < 20
        $tech_stocks filter mcap > 1000B
        
    The command expects:
    - A Basket as input (implicit or explicit)
    - Attribute name as first right token
    - Operator as second right token
    - Value as third right token
    """
    
    @property
    def input_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def output_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def description(self) -> str:
        return "Filter a basket by a specified condition"
        
    @property
    def right_tokens(self) -> Dict[str, str]:
        return {
            "attribute": "The attribute to filter by",
            "operator": "The comparison operator (>, <, =, >=, <=, !=)",
            "value": "The value to compare against"
        }
        
    @property
    def examples(self) -> Dict[str, str]:
        return {
            "basket -> filter pe < 20": "Filter basket to include only stocks with P/E ratio less than 20",
            "basket filter mcap > 1000B": "Filter basket to include only stocks with market cap greater than 1000B",
            "$tech_stocks filter sector = Technology": "Filter tech stocks to include only those in the Technology sector"
        }
        
    def validate_input(self, args: CommandArgs) -> None:
        """
        Validate command input and arguments.
        
        Args:
            args: The command arguments to validate
            
        Raises:
            TypeError: If input is not a Basket
            ValueError: If attribute, operator, or value is not specified or invalid
        """
        # First validate input type
        super().validate_input(args)
        
        # Validate right tokens
        if len(args.right_tokens) < 3:
            raise ValueError("Filter command requires attribute, operator, and value")
            
        # Validate operator
        operator_token = args.right_tokens[1]
        if not operator_token.is_literal:
            raise ValueError("Operator must be a literal value")
        operator = operator_token.as_literal()
        if not isinstance(operator, str) or operator not in (">", "<", "=", ">=", "<=", "!="):
            raise ValueError("Operator must be one of: >, <, =, >=, <=, !=")
        
    def execute(self, args: CommandArgs) -> Entity:
        """
        Filter the input basket by the specified condition.
        
        Args:
            args: The command arguments containing:
                - implicit_input or left_input: The basket to filter
                - right_tokens: [attribute, operator, value]
            
        Returns:
            The filtered basket
            
        Raises:
            TypeError: If input is not a Basket
            ValueError: If attribute, operator, or value is not specified or invalid
        """
        self.validate_input(args)
        basket = args.effective_input
        
        # Get attribute name
        attribute_token = args.right_tokens[0]
        if not attribute_token.is_literal:
            raise ValueError("Attribute name must be a literal value")
        attribute = attribute_token.as_literal()
        
        # Get operator
        operator_token = args.right_tokens[1]
        operator = operator_token.as_literal()
        
        # Get value
        value_token = args.right_tokens[2]
        value = value_token.as_literal() if value_token.is_literal else value_token.get_reference_name()
        
        # Define comparison functions
        ops = {
            ">": lambda x, y: x > y,
            "<": lambda x, y: x < y,
            "=": lambda x, y: x == y,
            ">=": lambda x, y: x >= y,
            "<=": lambda x, y: x <= y,
            "!=": lambda x, y: x != y
        }
        
        # Filter symbols that match the comparison
        filtered_symbols = []
        for symbol in basket.symbols:
            if attribute in basket.columns:
                attr_value = basket.columns[attribute].get(symbol)
            else:
                attr_value = getattr(symbol, attribute, None)
                
            if attr_value is not None and ops[operator](attr_value, value):
                filtered_symbols.append(symbol)
        
        # Create new filtered basket
        result = Basket(filtered_symbols)
        
        # Copy columns
        for name, values in basket.columns.items():
            result.add_column(name, {
                symbol: values[symbol]
                for symbol in filtered_symbols
                if symbol in values
            })
            
        return result 