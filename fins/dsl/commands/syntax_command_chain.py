from lark import Tree
from ..output import Output
from .command import Command, CommandArgs

@Command.register("command_chain")
class CommandChainCommand(Command):
    """Handles chains of commands connected by pipeline operators."""
    
    @property
    def description(self) -> str:
        return "Executes a chain of commands connected by pipeline operators (->)"
        
    @property
    def input_type(self) -> str:
        return "none"  # Can start fresh or use injected input
        
    @property
    def output_type(self) -> str:
        return "basket"  # The final output will be a basket
    
    def execute(self, args: CommandArgs) -> Output:
        """Execute the command chain."""
        chain_tree = args.tree
        return self.execute_chain(chain_tree, args.previous_output)