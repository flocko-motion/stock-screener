"""
Column commands for adding data columns to baskets.
"""

from typing import Type
from fins.entities import Basket, Column, Entity
from .command import Command, CommandArgs
from ..output import Output


class ColumnCommand(Command):
    """Base command for all column functions."""
    
    def __init__(self, column_class: Type[Column]):
        """Initialize with column class."""
        super().__init__()
        self.column_class = column_class
        
    @property
    def input_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def output_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def description(self) -> str:
        """Get the column's description."""
        return str(self.column_class())
        
    def execute(self, args: CommandArgs) -> Output:
        """Execute by creating and adding column."""
        self.validate_input(args)
        basket = args.effective_input
        
        # Create column instance
        column = self.column_class()
        basket.add_column(column)
        
        return Output(basket) 