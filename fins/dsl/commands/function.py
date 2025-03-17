"""
Base class for commands that add columns and optionally filter.

This module provides a unified approach to commands that:
1. Apply a calculation to a basket to create a new column
2. Optionally filter the basket based on a comparison
"""

from typing import Type, Optional, Any, Callable
from ...entities.entity import Entity
from ...entities.basket import Basket
from .command import Command, CommandArgs
from ..token import Token

class ColumnCommand(Command):
    """
    Base class for commands that apply calculations to a basket.
    
    These commands can:
    1. Add a new column to the basket (like analysis columns)
    2. Optionally filter based on a comparison (like filters)
    
    Example:
        basket -> pe  # Just adds PE column
        basket -> pe > 10  # Adds PE column and filters
        $tech_stocks pe < $max_pe  # Explicit syntax
    """
    
    @property
    def input_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def output_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def column_name(self) -> str:
        """The name of the column this command adds."""
        # Remove 'ColumnCommand' suffix for the column name
        class_name = self.__class__.__name__
        if class_name.endswith("ColumnCommand"):
            return class_name[:-13].lower()  # 13 is the length of "ColumnCommand"
        return class_name.lower()
        
    @property
    def description(self) -> str:
        """Description should explain what the command calculates."""
        pass
        
    @property
    def right_tokens(self) -> dict:
        return {
            "comparison": "Optional comparison operator (>, <, =)",
            "value": "Optional value to compare against"
        }
        
    def calculate(self, symbol: Entity) -> Any:
        """
        Calculate the value for a single symbol.
        
        Args:
            symbol: The symbol to calculate for
            
        Returns:
            The calculated value
        """
        raise NotImplementedError
        
    def validate_input(self, args: CommandArgs) -> None:
        """
        Validate command input and arguments.
        
        Args:
            args: The command arguments to validate
            
        Raises:
            TypeError: If input is not a Basket
            ValueError: If comparison operator or value is invalid
        """
        super().validate_input(args)
        
        # If we have tokens, validate comparison
        if args.right_tokens:
            if len(args.right_tokens) != 2:
                raise ValueError("Must provide both comparison operator and value")
                
            op_token = args.right_tokens[0]
            if not op_token.is_literal:
                raise ValueError("Comparison operator must be a literal")
            op = op_token.as_literal()
            if op not in (">", "<", "=", ">=", "<="):
                raise ValueError(f"Invalid comparison operator: {op}")
                
    def compare(self, value: Any, op: str, target: Any) -> bool:
        """
        Compare a value against a target using the given operator.
        
        Args:
            value: The value to compare
            op: The comparison operator (>, <, =, >=, <=)
            target: The target value
            
        Returns:
            True if comparison succeeds, False otherwise
        """
        if value is None:
            return False
            
        ops = {
            ">": lambda x, y: x > y,
            "<": lambda x, y: x < y,
            "=": lambda x, y: x == y,
            ">=": lambda x, y: x >= y,
            "<=": lambda x, y: x <= y
        }
        return ops[op](value, target)
        
    def execute(self, args: CommandArgs) -> Entity:
        """
        Execute the column command.
        
        Args:
            args: The command arguments
            
        Returns:
            The basket with new column added and optionally filtered
            
        Raises:
            TypeError: If input is not a Basket
            ValueError: If comparison operator or value is invalid
        """
        self.validate_input(args)
        basket = args.effective_input
        
        # Calculate values for all symbols
        values = {
            symbol: self.calculate(symbol)
            for symbol in basket.symbols
        }
        
        # Add the column
        basket.add_column(self.column_name, values)
        
        # If we have comparison tokens, filter the basket
        if args.right_tokens:
            op = args.right_tokens[0].as_literal()
            target = args.right_tokens[1].as_literal()
            
            # Filter symbols that match the comparison
            filtered_symbols = [
                symbol for symbol in basket.symbols
                if self.compare(values[symbol], op, target)
            ]
            
            # Create new filtered basket
            result = Basket(filtered_symbols)
            
            # Copy all columns
            for name, col_values in basket.columns.items():
                result.add_column(name, {
                    symbol: col_values[symbol]
                    for symbol in filtered_symbols
                })
                
            return result
            
        return basket 