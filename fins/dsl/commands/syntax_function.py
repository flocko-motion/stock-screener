from types import NoneType

from lark import Tree, Token
from typing import Optional

from dsl.command import CommandArg
from fins.entities import Basket
from fins.dsl import *

@Command.register("function_call")
class FunctionCallCommand(Command):
    """ Executes a function call.
    """
    
    @classmethod
    def category(cls) -> str | None:
        return "syntax"
        
    @classmethod
    def description(cls) -> str:
        return "Call a function with arguments"

    @classmethod
    def examples(cls) -> str | None:
        return None

    @classmethod
    def named_args(cls) -> list[CommandArg]:
        return []

    @classmethod
    def input_type(cls) -> type:
        return Optional[Basket]
        
    @classmethod
    def output_type(cls) -> type:
        return Basket
    
    def execute(self, args: CommandArgs) -> Output:
        f_name = f"{args.tree.children[0]}"
        f_args: Tree | None = args.tree.children[1] if len(args.tree.children) > 1 else None
        if not f_args is None and not isinstance(f_args, Tree):
            raise TypeError("failed to parse arguments of function call")

        cmd_handler = Command.get_command(f_name)
        cmd_args = CommandArgs(cmd=cmd_handler, tree=f_args, previous_output=args.previous_output, storage=args.storage)
        cmd_handler.validate_input(cmd_args)
        res = cmd_handler.execute(cmd_args)
        cmd_handler.validate_output(res)
        return res

