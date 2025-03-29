from lark import Tree, Token

from fins.entities import Basket, BasketItem
from fins.dsl import *

@Command.register("sequence")
class SequenceCommand(Command):
    """Handles sequences of operands and operators."""
    
    @property
    def description(self) -> str:
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
        result_basket = args.previous_output.data if args.previous_output and args.previous_output.output_type == "basket" else Basket([])

        for i in range(len(sequence)):
            tree: Tree = sequence[i]
            if not isinstance(tree, Tree):
                raise SyntaxError(f"Unexpected node {tree}")
            elif tree.data == "symbol":
                result_basket.add_item(BasketItem(tree.children[0].value, 1.0))
                continue
            elif tree.data == "operand":
                if len(tree.children) != 2:
                    raise SyntaxError(f"Unexpected operand node {tree}")
                weight = self._parse_weight(tree.children[0].value)
                ticker = tree.children[1].children[0].value
                result_basket.add_item(BasketItem(ticker, weight))
                continue
            raise SyntaxError(f"Unexpected node {tree}")

        return Output(result_basket, previous=args.previous_output)

    @staticmethod
    def _parse_weight(value):
        if value.endswith("x"):
            return float(value.rstrip("x"))
        return float(value)
