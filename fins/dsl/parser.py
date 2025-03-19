"""
Parser for FINS (Financial Insights Script)
"""

import os
import traceback
from lark import Lark, Tree

from ..storage import Storage
from fins.entities import Basket
from .output import Output
from .commands.command import Command, CommandArgs

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

    def parse(self, flow: str) -> Output:
        """Parse and execute a FINS command or command chain."""
        try:
            tree: Tree = parser.parse(flow)
            executor = Command.get_command(tree.data)
            return executor.execute(CommandArgs(tree=tree, previous_output=None))
        except Exception as e:
            traceback.print_exc()
            return Output(str(e), output_type="error")



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
