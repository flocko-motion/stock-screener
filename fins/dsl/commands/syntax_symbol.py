from lark import Tree, Token

from fins.entities import Basket, BasketItem
from fins.dsl import *

@Command.register("symbol")
class SymbolCommand(Command):
    """Handles a single symbol"""
    
    @property
    def description(self) -> str:
        return "Processes a single symbol"
        
    @property
    def input_type(self) -> str:
        return "none"  # Can start fresh or use injected basket
        
    @property
    def output_type(self) -> str:
        return "basket"
    
    def execute(self, args: CommandArgs) -> Output:
        """Execute the symbol command."""
        sequence = args.tree.children
        previous_basket: Basket = args.previous_output.data if args.previous_output and args.previous_output.output_type == "basket" else None
        if previous_basket is not None:
            raise SyntaxError("Symbol command can only be used at the beginning of a command chain")

        token: Token = sequence[0]
        if not isinstance(token, Token):
            raise SyntaxError(f"Unexpected node {token}")
        ticker = token.value
        result_basket = Basket([BasketItem(ticker, 1.0)])

        return Output(result_basket, previous=args.previous_output)

    @staticmethod
    def _parse_weight(value):
        if value.endswith("x"):
            return float(value.rstrip("x"))
        return float(value)
