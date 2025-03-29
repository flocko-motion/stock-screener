"""
Parser for FINS (Financial Insights Script)
"""

import os
import traceback
from typing import Type, Dict
from lark import Lark, Tree

from ..storage import Storage
from fins.entities import Basket, Column, Entity
from .output import Output
from .commands.command import Command, CommandArgs
from .commands.column import ColumnCommand
from .commands.operator_union import UnionCommand
from .commands.operator_difference import DifferenceCommand
from .commands.operator_intersection import IntersectionCommand

# Import commands to trigger registration
from . import commands

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
        """Initialize the parser with storage for commands."""
        Command.initialize_all(storage)
        self._register_column_commands()
        self._register_operator_commands()
        
    def _register_column_commands(self):
        """Register all column classes as commands."""
        for col_class in Column.list():
            name = str(col_class())  # Get default name from instance
            Command.register_command(name, ColumnCommand)  # Register the class, not an instance
            
    def _register_operator_commands(self):
        """Register operator commands."""
        Command.register_command("+", UnionCommand)  # Register the class, not an instance
        Command.register_command("-", DifferenceCommand)
        Command.register_command("&", IntersectionCommand)

    def parse(self, flow: str) -> Output:
        """Parse and execute a FINS command or command chain."""
        try:
            tree: Tree = parser.parse(flow)
            executor = Command.get_command(tree.data)
            return executor.execute(CommandArgs(tree=tree, previous_output=Output(None)))
        except Exception as e:
            traceback.print_exc()
            return Output(str(e))


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
