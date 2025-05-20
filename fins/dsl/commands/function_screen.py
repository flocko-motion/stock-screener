from typing import Any, Dict

from lark import Tree, Token

from data_sources.fmp import screen
from fins.entities import Basket, BasketItem
from fins.dsl import *

@Command.register("function_screen")
class FunctionScreen(Command):

	@classmethod
	def category(cls) -> str | None:
		return "search"

	@classmethod
	def description(cls) -> str:
		return "Search symbols using filters"

	@property
	def input_type(self) -> str:
		return "none"  # Requires a basket from the pipeline

	@property
	def output_type(self) -> str:
		return "basket"

	def execute(self, args: CommandArgs) -> Output:
		filters: Dict[str, Any] = {"limit":100}
		if args.tree is not None:
			for arg in args.tree.children:
				if isinstance(arg, Tree):
					arg_name = str(arg.children[0])
					if isinstance(arg.children[1], Tree):
						if str(arg.children[1].data) != "value":
							raise SyntaxError("expected 'value'")
						arg_value = str(arg.children[1].children[0])
						filters[arg_name] = arg_value
				else:
					raise SyntaxError("failed parsing arguments")
		symbols = screen(**filters)
		return Output(Basket([BasketItem(symbol) for symbol in symbols]))

	def parse_arg(self, arg: Tree):
		return arg

