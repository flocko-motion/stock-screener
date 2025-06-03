from types import NoneType

from lark import Tree, Token

from dsl.command import CommandArg
from fins.entities import Basket, BasketItem
from fins.dsl import *

@Command.register("sequence")
class SequenceCommand(Command):
    """Handles sequences of operands and operators."""
    
    @classmethod
    def category(cls) -> str | None:
        return "syntax"
        
    @classmethod
    def description(cls) -> str:
        return "Processes a sequence of operands and operators to create or modify baskets"

    @classmethod
    def named_args(cls) -> list[CommandArg]:
        return []

    @classmethod
    def input_type(cls) -> type:
        return NoneType

    @classmethod
    def output_type(cls) -> type:
        return NoneType
    
    def execute(self, args: CommandArgs) -> Output:
        """Execute the sequence command."""
        sequence = args.tree.children
        result_basket: Basket = args.previous_output.data if args.previous_output.is_type(Basket) else Basket([])
        operator: str | None  = None

        for i in range(len(sequence)):
            node: Tree | Token = sequence[i]
            if isinstance(node, Token):
                if operator is not None:
                    raise SyntaxError(f"Unexpected token {node}")
                operator = str(node.value)
                continue

            elif isinstance(node, Tree):
                res = self.execute_tree(CommandArgs(node, args.storage))
                if not res.assert_type(Basket):
                    raise SyntaxError(f"Expected a basket, got {res}")
                if operator is None:
                    operator = "+" # default operator
                result_basket = result_basket.operation(res.data, operator)
                operator = None
            else:
                raise SyntaxError(f"Unexpected node {node}")


        if operator is not None:
            raise SyntaxError("Unexpected end of sequence")

        return Output(result_basket, previous=args.previous_output)


