from types import NoneType
from typing import Any, Dict

from lark import Tree, Token

from data_sources.fmp import screen
from dsl.command import CommandArg
from fins.entities import Basket, BasketItem
from fins.dsl import *

@Command.register("screen")
class FunctionScreen(Command):

	@classmethod
	def category(cls) -> str | None:
		return "search"

	@classmethod
	def description(cls) -> str:
		return "Search symbols using filters"

	@classmethod
	def named_args(cls) -> list[CommandArg] | None:
		return [
			CommandArg(name="mcap_min", description="Market Cap Min", optional=True),
			CommandArg(name="mcap_max", description="Market Cap Max", optional=True),
			CommandArg(name="type", description="Asset Type {stocks|etf|crypto}", optional=True),
			CommandArg(name="sector", description="Sector Name", optional=True),
			CommandArg(name="industry", description="Industry Name", optional=True),
			CommandArg(name="country", description="Country Code", optional=True),
			CommandArg(name="exchange", description="Exchange Name", optional=True),
			CommandArg(name="limit", description="Max results", optional=True, default="100"),
		]


	@classmethod
	def input_type(cls) -> type:
		return NoneType

	@classmethod
	def output_type(cls) -> type:
		return Basket

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
		return Output(Basket.from_symbols(symbols))

	def parse_arg(self, arg: Tree):
		return arg

