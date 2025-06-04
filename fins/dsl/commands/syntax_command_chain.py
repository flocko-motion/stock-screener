from typing import Optional

from lark import Tree

from dsl.command import CommandArg
from fins.dsl import *

@Command.register("command_chain")
class CommandChainCommand(Command):
    """Handles chains of commands connected by pipeline operators."""
    
    @classmethod
    def category(cls) -> str | None:
        return "syntax"
        
    @classmethod
    def description(cls) -> str:
        return "Executes a chain of commands connected by pipeline operators (->)"

    @classmethod
    def examples(cls) -> str | None:
        return None

    @classmethod
    def named_args(cls) -> list[CommandArg]:
        return []

    @classmethod
    def input_type(cls) -> type:
        return Optional[object]

    @classmethod
    def output_type(cls) -> type:
        return Optional[object]

    def execute(self, args: CommandArgs) -> Output:
        chain_output = args.previous_output

        for tree in args.tree.children:
            if not isinstance(tree, Tree):
                raise RuntimeError("Invalid command chain structure")
            chain_output = Command.execute_tree(CommandArgs(tree=tree, previous_output=chain_output, storage=args.storage))

        return chain_output