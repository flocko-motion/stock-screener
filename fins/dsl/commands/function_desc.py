from lark import Tree

from fins.dsl import *

@Command.register("function_desc")
class FunctionSortDescending(Command):

	@property
	def description(self) -> str:
		return "Sort descending"

	@property
	def input_type(self) -> str:
		return "none"  # Requires a basket from the pipeline

	@property
	def output_type(self) -> str:
		return "basket"

	def execute(self, args: CommandArgs) -> Output:
		if not args.previous_output.is_type("basket"):
			raise SyntaxError("Expected a basket")
		sort_cols = []
		for arg in args.tree.children[0].children:
			if not isinstance(arg, Tree):
				raise SyntaxError(f"Argument {arg} is not a Tree")
			sort_cols.append((str(arg.children[0]), -1))
		basket = args.previous_output.data
		basket_sorted = basket.sort(sort_cols)
		return Output(basket_sorted)

	def parse_arg(self, arg: Tree):
		return arg

