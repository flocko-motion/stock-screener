from lark import Tree

from fins.dsl import *

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
        chain_output = args.previous_output

        for tree in args.tree.children:
            if not isinstance(tree, Tree):
                raise RuntimeError("Invalid command chain structure")
            chain_output = Command.execute_tree(CommandArgs(tree=tree, previous_output=chain_output, storage=args.storage))

        return chain_output