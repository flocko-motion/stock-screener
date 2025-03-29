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

        i = 0
        while i < len(sequence):
            tree: Tree = sequence[i]
            if not isinstance(tree, Tree):
                raise SyntaxError(f"Unexpected node {tree}")
            if tree.data == "operand_group":
                result_basket = self._process_operand_group(tree, result_basket)
                i += 1
                continue
            elif tree.data == "symbol":
                result_basket.add_item(BasketItem(tree.children[0].value, 1.0))
                i += 1
                continue
            raise SyntaxError(f"Unexpected node {tree}")

        return Output(result_basket, previous=args.previous_output)
    #
    # def _find_existing_basket(self, sequence: list[Tree]) -> Basket | None:
    #     """Find any existing basket from the pipeline."""
    #     for node in sequence:
    #         if isinstance(node, Tree) and node.data == "basket":
    #             return self._process_basket_node(node)
    #     return None
    #
    # def _process_basket_node(self, basket_node) -> Basket:
    #     """Process a basket node into a Basket object."""
    #     items = []
    #     for child in basket_node.children:
    #         if isinstance(child, Tree):
    #             if child.data == "symbol":
    #                 # Get the STOCK_SYMBOL token value
    #                 symbol_token = child.children[0]
    #                 if isinstance(symbol_token, Token):
    #                     items.append(BasketItem(symbol_token.value, 1.0))
    #                 elif isinstance(symbol_token, str):
    #                     items.append(BasketItem(symbol_token, 1.0))
    #                 elif isinstance(symbol_token, Tree):
    #                     symbol_value = symbol_token.children[0]
    #                     if isinstance(symbol_value, Token):
    #                         items.append(BasketItem(symbol_value.value, 1.0))
    #                     else:
    #                         items.append(BasketItem(str(symbol_value), 1.0))
    #             elif child.data == "operand":
    #                 weight = 1.0
    #                 symbol = None
    #
    #                 for operand_child in child.children:
    #                     if isinstance(operand_child, Tree):
    #                         if operand_child.data == "weight":
    #                             weight = float(operand_child.children[0].value.rstrip('x'))
    #                         elif operand_child.data == "symbol":
    #                             symbol_token = operand_child.children[0]
    #                             if isinstance(symbol_token, Token):
    #                                 symbol = symbol_token.value
    #                             elif isinstance(symbol_token, str):
    #                                 symbol = symbol_token
    #                             elif isinstance(symbol_token, Tree):
    #                                 symbol_value = symbol_token.children[0]
    #                                 if isinstance(symbol_value, Token):
    #                                     symbol = symbol_value.value
    #                                 else:
    #                                     symbol = str(symbol_value)
    #
    #                 if symbol:
    #                     items.append(BasketItem(symbol, weight))
    #     return Basket(items)

    def _process_operand_group(self, node: Tree, result_basket: Basket) -> Basket:
        """Process an operand group node."""
        operand_output = self._execute_subcommand("operand_group", node)
        if result_basket is None:
            return operand_output.data
        return result_basket.union(operand_output.data)
    #
    # def _process_operator(self, operator: str, next_node: Tree, result_basket: Basket) -> Basket:
    #     """Process an operator and its following operand group."""
    #     if not next_node or next_node.data != "operand_group" or result_basket is None:
    #         return result_basket
    #
    #     operand_output = self._execute_subcommand("operand_group", next_node)
    #
    #     operations = {
    #         "-": lambda x, y: x.subtract(y),
    #         "&": lambda x, y: x.intersection(y),
    #         "+": lambda x, y: x.union(y)
    #     }
    #
    #     operation = operations.get(operator)
    #     if operation:
    #         return operation(result_basket, operand_output.data)
    #     return result_basket