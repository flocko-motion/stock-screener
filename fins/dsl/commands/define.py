"""
Define function command for FINS.

This command defines a custom function.
"""

from typing import Type, Dict, Optional
from ...storage.entity import Entity
from ...entities.basket import Basket
from ...entities.symbol import Symbol
from .command import Command, CommandArgs

class DefineFunctionCommand(Command):
    """
    Command to define a custom function.
    
    Example:
        define tech_filter = $tech_stocks -> filter pe < 20
        
    The command expects:
    - No input (can be None)
    - Function name as first right token
    - Function command as second right token
    """
    
    @property
    def input_type(self) -> Optional[Type[Entity]]:
        return None  # This command doesn't require input
        
    @property
    def output_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def description(self) -> str:
        return "Define a custom function"
        
    @property
    def right_tokens(self) -> Dict[str, str]:
        return {
            "name": "The function name",
            "command": "The function command"
        }
        
    @property
    def examples(self) -> Dict[str, str]:
        return {
            "define tech_filter = $tech_stocks -> filter pe < 20": "Define a function to filter tech stocks by P/E ratio",
            "define top_5 = sort mcap desc -> limit 5": "Define a function to get the top 5 stocks by market cap"
        }
        
    def validate_input(self, args: CommandArgs) -> None:
        """
        Validate command input and arguments.
        
        Args:
            args: The command arguments to validate
            
        Raises:
            ValueError: If function name or command is not specified
        """
        # This command doesn't require input, so we don't call super().validate_input()
        
        # Validate right tokens
        if len(args.right_tokens) < 3:  # name, =, command
            raise ValueError("Define function command requires a name and command")
            
        # Validate equals sign
        equals_token = args.right_tokens[1]
        if not equals_token.is_literal or equals_token.as_literal() != "=":
            raise ValueError("Define function command requires an equals sign between name and command")
        
    def execute(self, args: CommandArgs) -> Entity:
        """
        Define a custom function.
        
        Args:
            args: The command arguments containing:
                - right_tokens: [name, =, command]
            
        Returns:
            A dummy basket
            
        Raises:
            ValueError: If function name or command is not specified
        """
        self.validate_input(args)
        
        # Get function name
        name_token = args.right_tokens[0]
        if not name_token.is_literal:
            raise ValueError("Function name must be a literal value")
        name = name_token.as_literal()
        
        # Get function command (everything after the equals sign)
        command_tokens = args.right_tokens[2:]
        command = " ".join(str(token.as_literal()) if token.is_literal else token.get_reference_name() 
                          for token in command_tokens)
        
        # In a real implementation, this would store the function
        # For now, just return a dummy basket
        return Basket([Symbol(f"function_{name}")]) 