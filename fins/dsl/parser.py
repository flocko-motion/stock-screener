"""
Parser for FINS (Financial Insights Script)
"""

import os
from lark import Lark

from ..storage import Storage
from fins.entities import Basket, BasketItem
from .ast_transformer import AstTransformer
from .output import Output
from ..entities import Token
from .commands.command import Command, CommandArgs
from .commands.sort import SortColumnCommand
from .commands.filter import FilterCommand
from .commands.union import UnionCommand
from .commands.subtraction import SubtractionCommand
from .commands.intersection import IntersectionCommand
from .commands.spread import SpreadCommand
from .commands.create import CreateBasketCommand
from .commands.variable import VariableCommand
from .commands.column import AddColumnCommand
from .commands.info import InfoCommand
from .commands.define import DefineFunctionCommand

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

    def __init__(self, storage: Storage):
        # the storage instance persists variables and functions across command chains
        self.storage = storage

        # Command handlers dictionary for dispatch
        self.command_handlers = {
            "basket": self._handle_basket,
            "variable": self._handle_variable,
            "function_definition": self._handle_function_definition,
        }
        
        # Command instances for executing commands
        self.commands = {
            "sort": SortColumnCommand(),
            "filter": FilterCommand(),
            "union": UnionCommand(),
            "difference": SubtractionCommand(),
            "intersection": IntersectionCommand(),
            "spread": SpreadCommand(),
            "create": CreateBasketCommand(),
            "variable": VariableCommand(),
            "column": AddColumnCommand(),
            "info": InfoCommand(),
            "define": DefineFunctionCommand(),
        }

    def parse(self, command_str):
        """
        Parse a FINS command string and execute it.
        
        Args:
            command_str: The FINS command string to parse
            
        Returns:
            Output: The result of executing the command wrapped in an Output instance
        """
        try:
            # Parse the command string
            tree = parser.parse(command_str)
            
            # Transform the parse tree to an AST
            ast = AstTransformer().transform(tree)
            
            # Execute the command
            if ast["type"] == "command_chain":
                result = self._execute_command_chain(ast)
            else:
                result = self._execute_command(ast)
                
            # If result is already an Output instance, return it
            if isinstance(result, Output):
                return result
                
            # Otherwise wrap it in an Output instance
            return Output(result)
            
        except Exception as e:
            return Output(e, output_type="error")
    
    def _handle_basket(self, command):
        """
        Handle a basket command.
        
        Args:
            command: The basket command to handle
            
        Returns:
            Output: The result of executing the basket command
        """

        # Get list of symbol names as stated in the command
        tickers = command.get("symbols", [])
        
        # Convert symbol names to Token objects (Token is the most generic type of entity - it's basically an unparsed value)
        right_operands = []
        for ticker in tickers:
            if isinstance(ticker, dict) and ticker.get("type") == "symbol":
                right_operands.append(BasketItem(ticker.get("ticker"), 1))
            else:
                raise ValueError(f"Unknown token type {ticker.get('type')}")

        # Create command args
        args = CommandArgs(
            left_operands=[],
            right_operands=right_operands,  # right_input is already a list of Symbol objects which satisfies Sequence[Entity]
        )
        
        # Execute the command
        return self.commands["create"].execute_with_output(args)
        


    def _handle_variable(self, command):
        """
        Handle a variable command.
        
        Args:
            command: The variable command to handle
            
        Returns:
            Output: The result of executing the variable command
        """
        name = command.get("name")
        basket = command.get("basket")

        if basket is None:
            value = self.storage.get(name)
            if value is None:
                raise RuntimeError(f"no variable '{name}'")
            return Output(value)

        self.storage.set(name, basket)

        return Output(basket)


    def _handle_function_definition(self, command):
        """
        Handle a function definition command.
        
        Args:
            command: The function definition command to handle
            
        Returns:
            Output: The result of executing the function definition command
        """
        name = command.get("name")
        function_command = command.get("command")
        
        # Convert function name and command to tokens
        name_token = Token(name, is_reference=False)
        equals_token = Token("=", is_reference=False)
        command_token = Token(function_command, is_reference=False)
        
        # Create command args
        args = CommandArgs(
            implicit_input=None,
            left_input=None,
            right_tokens=[name_token, equals_token, command_token]
        )
        
        # Execute the command
        result = self.commands["define"].execute_with_output(args)
        
        # Store the function
        self.functions[name] = function_command
        
        return result
    
    def _handle_lock(self, basket, **kwargs):
        """
        Handle a lock command.
        
        Args:
            basket: The basket to lock
            **kwargs: Additional arguments
                - variable: The variable to lock
                
        Returns:
            Output: The result of executing the lock command
        """
        var_name = kwargs.get("variable")
        self.locked_variables.add(var_name)
        
        # Convert variable name to token
        var_token = Token(var_name, is_reference=True)
        action_token = Token("lock", is_reference=False)
        
        # Create command args
        args = CommandArgs(
            implicit_input=None,
            left_input=None,
            right_tokens=[action_token, var_token]
        )
        
        # Execute the command
        result = self.commands["variable"].execute_with_output(args)
        
        return result
    
    def _handle_unlock(self, basket, **kwargs):
        """
        Handle an unlock command.
        
        Args:
            basket: The basket to unlock
            **kwargs: Additional arguments
                - variable: The variable to unlock
                
        Returns:
            Output: The result of executing the unlock command
        """
        var_name = kwargs.get("variable")
        if var_name in self.locked_variables:
            self.locked_variables.remove(var_name)
            
        # Convert variable name to token
        var_token = Token(var_name, is_reference=True)
        action_token = Token("unlock", is_reference=False)
        
        # Create command args
        args = CommandArgs(
            implicit_input=None,
            left_input=None,
            right_tokens=[action_token, var_token]
        )
        
        # Execute the command
        result = self.commands["variable"].execute_with_output(args)
        
        return result
            
    def _execute_command(self, command):
        """Execute a command and return the result wrapped in an Output instance."""
        try:
            command_type = command.get("type")
            action = command.get("action")
            
            # Handle command by type
            if command_type in self.command_handlers:
                return self.command_handlers[command_type](command)
            
            # Handle action commands
            if action in self.commands:
                basket = command.get("basket")
                # Extract all other arguments from the command
                kwargs = {k: v for k, v in command.items() if k not in ["type", "action", "basket"]}
                
                # Convert arguments to tokens
                right_operands = []
                for key, value in kwargs.items():
                    if value.get("type") == "symbol":
                        right_operands.append(BasketItem(value.get("ticker")))
                    elif value.get("type") == "basket":
                        items = [BasketItem(s["ticker"]) for s in value.get("symbols", [])]
                        right_operands.append(Basket(items))
                    else:
                        raise ValueError("Unknown toke type {}".format(value.get("type")))
                
                # Create command args
                args = CommandArgs(
                    left_operands=[basket, ] if basket else [],
                    right_operands=right_operands,
                )
                
                # Execute the command
                return self.commands[action].execute_with_output(args)

            # Handle unknown commands
            return Output(f"Unknown command: {command}", output_type="error")
        except Exception as e:
            return Output(str(e), output_type="error")

    def _execute_command_chain(self, command_chain, initial_basket=None):
        """
        Execute a chain of commands.
        
        Args:
            command_chain: The command chain to execute
            initial_basket: The initial basket (if any)
            
        Returns:
            Output: The result of executing the command chain
        """
        current_basket = initial_basket
        result = None
        commands = command_chain["commands"]
        
        try:
            # Create an initial Output object to collect logs
            chain_output = Output(None, "none")
            chain_output.add_log("Starting command chain execution")
            
            for i, command in enumerate(commands):
                # Update the basket in the command
                if i > 0 and current_basket is not None:
                    command["basket"] = current_basket
                
                # Execute the command
                result = self._execute_command(command)
                
                # Merge logs from this command's output
                if isinstance(result, Output):
                    chain_output.merge_logs(result)
                    current_basket = result.data
                else:
                    current_basket = result
                    chain_output.add_log("Command returned non-Output result")

            # Set the final data and metadata in our chain output
            if isinstance(result, Output):
                chain_output.data = result.data
                chain_output.output_type = result.output_type
                chain_output.metadata = result.metadata
            else:
                chain_output.data = result
            
            return chain_output
            
        except Exception as e:
            return Output(str(e), output_type="error")

    def set_storage(self, storage: Storage):
        self.storage = storage


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
