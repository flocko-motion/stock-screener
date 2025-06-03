from types import NoneType

from lark import Tree

from dsl.command import CommandArg
from entities import Basket
from fins.dsl import *

@Command.register("function_asc")
class FunctionSortAscending(Command):
	""" Sort ascending
	"""

	@classmethod
	def category(cls) -> str | None:
		return "basket.sort"

	@classmethod
	def description(cls) -> str:
		return "Sort ascending"

	@classmethod
	def named_args(cls) -> list[CommandArg]:
		return []

	@classmethod
	def input_type(cls) -> type:
		return Basket

	@classmethod
	def output_type(cls) -> type:
		return Basket

	def execute(self, args: CommandArgs) -> Output:
		sort_cols = []
		for arg in args.tree.children[0].children:
			if not isinstance(arg, Tree):
				raise SyntaxError(f"Argument {arg} is not a Tree")
			sort_cols.append((str(arg.children[0]), 1))
		basket = args.previous_output.data
		basket_sorted = basket.sort(sort_cols)
		return Output(basket_sorted)

	def parse_arg(self, arg: Tree):
		return arg

