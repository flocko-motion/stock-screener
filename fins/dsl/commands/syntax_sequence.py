from lark import Tree, Token

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
        
    @property
    def input_type(self) -> str:
        return "none"  # Can start fresh or use injected basket
        
    @property
    def output_type(self) -> str:
        return "basket"
    
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


