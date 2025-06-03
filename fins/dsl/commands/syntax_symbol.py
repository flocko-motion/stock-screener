from lark import Tree, Token
from typing import Optional

from dsl.command import CommandArg
from fins.entities import Basket, BasketItem
from fins.dsl import *

@Command.register("symbol")
class SymbolCommand(Command):
    """Handles a single symbol"""
    
    @classmethod
    def category(cls) -> str | None:
        return "syntax"
        
    @classmethod
    def description(cls) -> str:
        return "Processes a single symbol"

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
        """Execute the symbol command."""
        sequence = args.tree.children
        previous_basket: Basket = args.get_previous_output()
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
