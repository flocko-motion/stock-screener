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
        previous_basket: Basket = args.previous_output.data if args.previous_output and args.previous_output.output_type == "basket" else None
        result_basket = Basket([])
        operator: str | None  = None

        for i in range(len(sequence)):
            node: Tree | Token = sequence[i]
            if isinstance(node, Token):
                if operator is not None:
                    # multiple chained operations -> let's commit the current one
                    previous_basket = previous_basket.operation(result_basket, operator)
                operator = str(node.value)
                continue

            if not isinstance(node, Tree):
                raise SyntaxError(f"Unexpected node {node}")
            tree = node
            if tree.data == "symbol":
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

        if previous_basket is None:
            # left input -> basket creation
            if operator is None:
                return Output(result_basket, previous=args.previous_output)
            # operating on empty input -> error
            raise SyntaxError(f"Unexpected operator {operator}")

        if operator is None:
            # no operator -> undefined operation with previous basket
            raise SyntaxError("No operator specified")

        result_basket = previous_basket.operation(result_basket, operator)
        return Output(result_basket, previous=args.previous_output)

    @staticmethod
    def _parse_weight(value):
        if value.endswith("x"):
            return float(value.rstrip("x"))
        return float(value)
