from types import NoneType

from lark import Tree, Token

from dsl.command import CommandArg
from entities import Entity
from fins.entities import Basket, BasketItem
from fins.dsl import *

@Command.register("variable")
class VariableCommand(Command):
    """Handles variables"""
    
    @classmethod
    def category(cls) -> str | None:
        return "syntax"
        
    @classmethod
    def description(cls) -> str:
        return "Processes a variable"
        
    @classmethod
    def named_args(cls) -> list[CommandArg]:
        return []

    @classmethod
    def input_type(cls) -> type:
        return NoneType

    @classmethod
    def output_type(cls) -> type:
        return Entity
    
    def execute(self, args: CommandArgs) -> Output:
        if len(args.tree.children) != 1:
            raise RuntimeError("Invalid variable structure")
        node: Token = args.tree.children[0]
        if not isinstance(node, Token):
            raise RuntimeError("Invalid variable structure")
        # the whole tree is a single variable name => store the previous output in the variable (if it exists) and return var value
        variable_name = str(node.value)

        # store the previous output in the variable (if it exists)
        if (args.previous_output is not None) and (not args.previous_output.is_void()) and args.previous_output.assert_type(Basket):
            args.storage.set(variable_name, args.previous_output.data)

        val = args.storage.get(variable_name)
        return Output(val)
