"""
Info command for FINS.

This command retrieves information about a basket.
"""

from typing import Type, Dict
from ...storage.entity import Entity
from ...entities.basket import Basket
from .command import Command, CommandArgs

class InfoCommand(Command):
    """
    Command to retrieve information about a basket.
    
    Example:
        basket -> info
        $tech_stocks info
        
    The command expects:
    - A Basket as input (implicit or explicit)
    - No additional arguments
    """
    
    @property
    def input_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def output_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def description(self) -> str:
        return "Retrieve information about a basket"
        
    @property
    def examples(self) -> Dict[str, str]:
        return {
            "basket -> info": "Get information about the basket",
            "$tech_stocks info": "Get information about the tech stocks basket"
        }
        
    def validate_input(self, args: CommandArgs) -> None:
        """
        Validate command input and arguments.
        
        Args:
            args: The command arguments to validate
            
        Raises:
            TypeError: If input is not a Basket
        """
        # First validate input type
        super().validate_input(args)
        
    def execute(self, args: CommandArgs) -> Entity:
        """
        Retrieve information about the input basket.
        
        Args:
            args: The command arguments containing:
                - implicit_input or left_input: The basket to get information about
            
        Returns:
            The input basket (unchanged)
            
        Raises:
            TypeError: If input is not a Basket
        """
        self.validate_input(args)
        basket = args.effective_input
        
        # In a real implementation, this would return actual info
        # For now, just return the basket unchanged
        return basket 