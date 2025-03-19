"""
Parser for FINS (Financial Insights Script)
"""

import os
from lark import Lark, Tree

from ..storage import Storage
from fins.entities import Basket
from .output import Output
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
from .commands.expression import ExpressionCommand
from .commands.operation import OperationCommand
from .commands.sequence import SequenceCommand
from .commands.basket import BasketCommand
from .commands.function_definition import FunctionDefinitionCommand

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

        # Command handlers for all command types
        self.commands = {
            # Basic operations
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
            
            # Grammar-based commands
            "basket": BasketCommand(),
            "function_definition": FunctionDefinitionCommand(),
            "expression": ExpressionCommand(),
            "operation_command": OperationCommand(),
            "sequence": SequenceCommand(),
        }

    def parse(self, flow: str) -> Output:
        """Parse and execute a FINS command or command chain."""
        try:
            tree: Tree = parser.parse(flow)
            
            if tree.data == "command_chain":
                return self._execute_command_chain(tree)
            else:
                return self._execute_command(tree)
        except Exception as e:
            return Output(str(e), output_type="error")
            
    def _execute_command(self, command):
        """Execute a command and return the result wrapped in an Output instance."""
        try:
            command_type = command.data
            if command_type in self.commands:
                handler = self.commands[command_type]
                result = handler.execute(CommandArgs(command_tree=command))
                return Output(result) if result is not None else Output(None, "none")
            
            return Output(f"Unknown command type: {command_type}", output_type="error")
        except Exception as e:
            return Output(str(e), output_type="error")

    def _execute_command_chain(self, command_chain, initial_basket: Basket | None =None) -> Output:
        """Execute a chain of commands, passing results between them."""
        chain_output = Output(initial_basket, "none")
        chain_output.add_log("Starting command chain execution")

        for command in command_chain.children:
            if not isinstance(command, Tree):
                raise SyntaxError(f"Commands must have children of type Tree")

            if chain_output.data is not None and type(chain_output.data) == Basket:
                command.children = [Tree("basket", chain_output.data.items)] + list(command.children)

            step_output = self._execute_command(command)
            if not isinstance(step_output, Output):
                raise RuntimeError(f"Command step returned {type(step_output)}, expected Output")

            chain_output.merge_logs(step_output)
            chain_output.data = step_output.data
            chain_output.output_type = step_output.output_type
            chain_output.metadata = step_output.metadata

        return chain_output



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
