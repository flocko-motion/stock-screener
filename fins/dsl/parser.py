"""
Parser for FINS (Financial Insights Script)
"""

import os
from lark import Lark
from typing import List, Dict, Any, Union, Optional

from .ast_transformer import AstTransformer
from .command_functions import (
    sort_basket, filter_basket, union_baskets, difference_baskets, 
    intersection_baskets, spread_symbol, create_basket, get_variable,
    add_column, get_info, lock_variable, unlock_variable, define_function
)

# Load the grammar from external file "parser.lark"
grammar_file = os.path.join(os.path.dirname(__file__), "parser.lark")
with open(grammar_file, "r") as f:
    grammar = f.read()

# Initialize the parser using Earley
parser = Lark(grammar, parser='earley')

class FinsParser:
    """
    FINS Parser class that provides a high-level interface for parsing FINS commands.
    This class encapsulates the parsing logic and provides methods for executing commands.
    """

    def __init__(self):
        """Initialize the FINS parser."""
        self.variables = {}  # Store variables (baskets)
        self.functions = {}  # Store functions
        self.locked_variables = set()  # Track locked variables
        
        # Command handlers dictionary for dispatch
        self.command_handlers = {
            "basket": self._handle_basket,
            "variable": self._handle_variable,
            "function_definition": self._handle_function_definition,
        }
        
        # Action handlers dictionary for command actions
        self.action_handlers = {
            "sort": sort_basket,
            "filter": filter_basket,
            "union": union_baskets,
            "difference": difference_baskets,
            "intersection": intersection_baskets,
            "spread": spread_symbol,
            "add_column": add_column,
            "info": get_info,
            "lock": self._handle_lock,
            "unlock": self._handle_unlock,
        }

    def parse(self, command_str):
        """
        Parse a FINS command string and execute it.
        
        Args:
            command_str: The FINS command string to parse
            
        Returns:
            The result of executing the command
        """
        try:
            # Parse the command string
            tree = parser.parse(command_str)
            
            # Transform the parse tree to an AST
            ast = AstTransformer().transform(tree)
            
            # Execute the command
            if ast["type"] == "command_chain":
                return self._execute_command_chain(ast)
            else:
                return self._execute_command(ast)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _handle_basket(self, command):
        """
        Handle basket creation commands.
        
        Args:
            command: The basket command to handle
            
        Returns:
            The created basket
        """
        symbols = command.get("symbols", [])
        return create_basket(symbols)
    
    def _handle_variable(self, command):
        """Handle variable commands."""
        name = command.get("name")
        action = command.get("action")
        
        # If no action is specified, assume we're retrieving the variable
        if not action:
            if name in self.variables:
                return self.variables[name]
            return get_variable(name)
        
        if action == "get":
            if name in self.variables:
                return self.variables[name]
            return get_variable(name)
        elif action == "lock":
            return lock_variable(name)
        elif action == "unlock":
            return unlock_variable(name)
        
        return f"Unknown variable action: {action}"
    
    def _handle_function_definition(self, command):
        """Handle function definition commands."""
        name = command.get("name")
        function_command = command.get("command")
        return define_function(name, function_command)
    
    def _handle_lock(self, current_basket, **kwargs):
        """Handle lock action"""
        var_name = kwargs.get("variable")
        self.locked_variables.add(var_name)
        return lock_variable(var_name)
    
    def _handle_unlock(self, current_basket, **kwargs):
        """Handle unlock action"""
        var_name = kwargs.get("variable")
        if var_name in self.locked_variables:
            self.locked_variables.remove(var_name)
        return unlock_variable(var_name)
            
    def _execute_command(self, command):
        """Execute a command and return the result."""
        command_type = command.get("type")
        action = command.get("action")
        
        # Handle command by type
        if command_type in self.command_handlers:
            return self.command_handlers[command_type](command)
        
        # Handle action commands
        if action in self.action_handlers:
            basket = command.get("basket")
            # Extract all other arguments from the command
            kwargs = {k: v for k, v in command.items() if k not in ["type", "action", "basket"]}
            return self.action_handlers[action](basket, **kwargs)
        
        # Handle unknown commands
        return f"Unknown command: {command}"

    def _execute_command_chain(self, command_chain, initial_basket=None):
        """
        Execute a chain of commands.
        
        Args:
            command_chain: The command chain to execute
            initial_basket: The initial basket (if any)
            
        Returns:
            The result of executing the command chain
        """
        current_basket = initial_basket
        result = None
        commands = command_chain["commands"]
        
        for i, command in enumerate(commands):
            result = self._execute_command(command)
            current_basket = result
            
            # If the last command in the chain is a variable assignment, store the result
            if i == len(commands) - 1 and command["type"] == "variable":
                var_name = command["name"]
                if var_name not in self.locked_variables:
                    self.variables[var_name] = result
        
        return result

if __name__ == "__main__":
    # Test with a simple command chain
    command_str = "AAPL MSFT -> + GOOGL -> sort mcap desc"
    try:
        parser_instance = FinsParser()
        result = parser_instance.parse(command_str)
        print("Parsed and executed command chain:")
        print(result)
    except Exception as e:
        print("Error parsing command:", e)
