"""
Variable command for FINS.

This command handles variable operations (get, lock, unlock).
"""

from typing import Type, Dict, Optional
from ...storage.entity import Entity
from ...entities.basket import Basket
from ...entities.symbol import Symbol
from .command import Command, CommandArgs

class VariableCommand(Command):
    """
    Command to handle variable operations (get, lock, unlock).
    
    Example:
        $tech_stocks
        lock $tech_stocks
        unlock $tech_stocks
        
    The command expects:
    - No input (can be None)
    - Variable name as right token
    - Optional action (lock, unlock) as prefix
    """
    
    @property
    def input_type(self) -> Optional[Type[Entity]]:
        return None  # This command doesn't require input
        
    @property
    def output_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def description(self) -> str:
        return "Handle variable operations (get, lock, unlock)"
        
    @property
    def right_tokens(self) -> Dict[str, str]:
        return {
            "variable": "The variable name",
            "action": "The action to perform (get, lock, unlock)"
        }
        
    @property
    def examples(self) -> Dict[str, str]:
        return {
            "$tech_stocks": "Get the value of the tech_stocks variable",
            "lock $tech_stocks": "Lock the tech_stocks variable to prevent modification",
            "unlock $tech_stocks": "Unlock the tech_stocks variable to allow modification"
        }
        
    def validate_input(self, args: CommandArgs) -> None:
        """
        Validate command input and arguments.
        
        Args:
            args: The command arguments to validate
            
        Raises:
            ValueError: If variable name is not specified
        """
        # This command doesn't require input, so we don't call super().validate_input()
        
        # Validate right tokens
        if not args.right_tokens:
            raise ValueError("Variable command requires a variable name")
        
    def execute(self, args: CommandArgs) -> Entity:
        """
        Handle variable operations (get, lock, unlock).
        
        Args:
            args: The command arguments containing:
                - right_tokens: [action, variable] or [variable]
            
        Returns:
            The variable value or a dummy basket
            
        Raises:
            ValueError: If variable name is not specified
        """
        self.validate_input(args)
        
        # Get action and variable name
        action = "get"  # Default action
        variable_name = None
        
        if len(args.right_tokens) == 1:
            # Just the variable name
            token = args.right_tokens[0]
            if token.is_literal:
                variable_name = token.as_literal()
            else:
                variable_name = token.get_reference_name()
        else:
            # Action and variable name
            action_token = args.right_tokens[0]
            variable_token = args.right_tokens[1]
            
            if action_token.is_literal:
                action = action_token.as_literal()
            
            if variable_token.is_literal:
                variable_name = variable_token.as_literal()
            else:
                variable_name = variable_token.get_reference_name()
        
        # Handle the action
        if action == "get":
            # In a real implementation, this would fetch from storage
            # For now, just return a basket with the variable name
            return Basket([Symbol(variable_name)])
        elif action == "lock":
            # In a real implementation, this would lock the variable
            # For now, just return a dummy basket
            return Basket([Symbol(f"locked_{variable_name}")])
        elif action == "unlock":
            # In a real implementation, this would unlock the variable
            # For now, just return a dummy basket
            return Basket([Symbol(f"unlocked_{variable_name}")])
        else:
            raise ValueError(f"Unknown variable action: {action}") 